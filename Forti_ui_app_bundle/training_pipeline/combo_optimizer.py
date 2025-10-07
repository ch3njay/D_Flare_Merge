# training_pipeline/combo_optimizer.py
from __future__ import annotations

import os
import json
import itertools
from typing import Any, Dict, List, Sequence, Tuple, Optional
import warnings
import numpy as np

from sklearn.ensemble import StackingClassifier, VotingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedKFold
from sklearn.metrics import (
    accuracy_score,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
    classification_report,
    confusion_matrix,
)
from sklearn.base import clone
from joblib import parallel_backend, dump

from .ensemble_optuna import OptunaEnsembler

try:
    from sklearn.exceptions import UndefinedMetricWarning
except Exception:
    UndefinedMetricWarning = Warning  # 兼容舊版


# ---------------- 工具：CPU 版（避免 Stacking/Voting 重新訓練 clone 時觸發單卡 GPU 衝突） ----------------
def _set_if_has(est, **pairs):
    """若 est 支援該參數，才設定；不丟例外。"""
    try:
        est.set_params(**{k: v for k, v in pairs.items() if k in est.get_params()})
    except Exception:
        pass
    return est

def _as_cpu_estimator(est):
    """
    將常見樹系模型的平行度與裝置收斂到 CPU + 單執行緒，避免單卡 GPU/多進程衝突。
    僅在參數存在時才設定，不改變未知參數。
    """
    e = clone(est)
    name = e.__class__.__name__.lower()

    # Sklearn 常見模型：若有 n_jobs → 設 1
    if hasattr(e, "get_params") and "n_jobs" in e.get_params():
        _set_if_has(e, n_jobs=1)

    # CatBoost
    if "catboost" in name:
        _set_if_has(e, task_type="CPU", devices="", verbose=False)

    # XGBoost sklearn API
    if "xgb" in name or "xgboost" in name:
        # 若你要 GPU 訓練，這裡可依需求調整。為了 ensemble 安全，仍以 CPU 推論/重訓。
        _set_if_has(e, tree_method="hist", n_jobs=1, verbosity=0)

    return e


# ---------------- 評分工具（靜音 UndefinedMetricWarning，zero_division=0） ----------------
def _compute_metrics(task: str, y_true, y_pred, proba: Optional[np.ndarray]) -> Dict[str, Any]:
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=UndefinedMetricWarning)
        acc = accuracy_score(y_true, y_pred)

        if task == "binary":
            f1 = f1_score(y_true, y_pred, average="binary", zero_division=0)
            prec = precision_score(y_true, y_pred, average="binary", zero_division=0)
            rec = recall_score(y_true, y_pred, average="binary", zero_division=0)
            report = classification_report(y_true, y_pred, digits=4, zero_division=0)
        else:
            f1 = f1_score(y_true, y_pred, average="macro", zero_division=0)
            prec = precision_score(y_true, y_pred, average="macro", zero_division=0)
            rec = recall_score(y_true, y_pred, average="macro", zero_division=0)
            report = classification_report(y_true, y_pred, digits=4, zero_division=0)

    auc = np.nan
    try:
        if proba is not None:
            if task == "binary":
                pos_idx = 1 if proba.shape[1] > 1 else 0
                auc = roc_auc_score(y_true, proba[:, pos_idx])
            else:
                auc = roc_auc_score(y_true, proba, multi_class="ovr")  # 多類別採 OVR-AUC
    except Exception:
        pass

    cm = confusion_matrix(y_true, y_pred)

    # 額外：預測類別分佈
    try:
        uniq, cnts = np.unique(y_pred, return_counts=True)
        pred_dist = dict(zip(uniq.tolist(), cnts.tolist()))
    except Exception:
        pred_dist = {}

    return {
        "acc": acc,
        "auc": auc,
        "f1": f1,
        "precision": prec,
        "recall": rec,
        "report": report,
        "confusion_matrix": cm,
        "pred_dist": pred_dist,
    }


class ComboOptimizer:
    """
    集成組合器（流程）：
    1) 讀取 ENSEMBLE_SETTINGS，決定 Voting/Stacking 與 CV。
    2) 將基模型 clone 成「CPU＋單執行緒版」以避免單卡 GPU 衝突。
    3) 建立集成器：
       - VotingClassifier(voting='soft' 或 'hard')
       - 或 StackingClassifier(cv=K, final_est=LogisticRegression)
    4) 可選：Voting 子集排列組合搜尋，列出 Top-K 並保存最佳（Optuna 或固定枚舉）。
    5) 驗證：輸出 ACC/AUC/F1、分類報告、混淆矩陣與預測分佈。
    6) 額外回傳/印出「🧩 Ensemble 組成」：Voting 權重或 Stacking 係數。
    7) 保存產物：
       - models/ensemble_best.joblib
       - reports/ensemble_search_report.json（若啟用子集搜尋）
       - reports/ensemble_topk.txt（Top-K 可讀版）
       - reports/ensemble_final.txt（最終組合＋成績）
    """

    def __init__(
        self,
        estimators: Sequence[Tuple[str, Any]],
        X_train,
        y_train,
        X_valid,
        y_valid,
        task_type: str = "binary",
        config: Optional[Dict[str, Any]] = None,
        logger: Any = None,
        out_dir: Optional[str] = None,
        use_optuna: bool = False,   # ★ 與 pipeline 串接
    ) -> None:
        self.base_estimators = list(estimators)
        self.X_train = X_train
        self.y_train = y_train
        self.X_valid = X_valid
        self.y_valid = y_valid
        self.task_type = task_type
        self.config = config or {}
        self.logger = logger
        self.out_dir = out_dir or "./artifacts"
        self.use_optuna = bool(use_optuna)

        ens = (self.config.get("ENSEMBLE_SETTINGS") or {}).copy()
        ens.setdefault("STACK_CV", 5)
        ens.setdefault("VOTING", "soft")
        ens.setdefault("THRESHOLD", 0.5)
        # Voting 搜尋參數
        ens.setdefault("SEARCH", "none")   # "none" / "voting_subsets"
        ens.setdefault("SEARCH_MAX_SUBSET", 4)       # 子集最大模型數
        ens.setdefault("SEARCH_TOPK", 3)             # 取 Top-K
        # Optuna 搜尋回合（僅用於 ensemble）
        ens.setdefault("OPTUNA_TRIALS", 30)
        ens.setdefault("WEIGHT_MODE", "dirichlet")
        ens.setdefault("MODE", "free")
        ens.setdefault("MIN_MODELS", 2)
        ens.setdefault("MAX_MODELS", None)
        ens.setdefault("PRUNING", True)
        ens.setdefault("DIRECTION", "maximize")
        ens.setdefault("SEED", 42)
        if not self.use_optuna:
            ens.pop("OPTUNA_TRIALS", None)
        self.ens = ens

        # 供 Stacking 組成解讀用的類別列表（保持決定式）
        self.classes_ = np.unique(self.y_train)

    def optimize(self) -> Dict[str, Any]:
        print(f"⚙️  Ensemble 設定載入完成：{self.ens}")
        if not self.use_optuna:
            print("🚫 Optuna 未啟用，使用既定集成策略。")

        voting_mode = str(self.ens.get("VOTING", "soft")).lower()
        stack_cv = int(self.ens.get("STACK_CV", 5))

        # 建立 CPU 版的基模型清單（避免 clone 時再開 GPU）
        cpu_estimators = [(name, _as_cpu_estimator(est)) for name, est in self.base_estimators]

        # ============ 分支一：Voting + Optuna ============ 
        if self.use_optuna and voting_mode in ("soft", "hard"):
            try:
                final_model, metrics, composition = self._optuna_voting_search(cpu_estimators, voting_mode)
                self._save_ensemble(final_model)
                self._write_final_txt(kind="voting", metrics=metrics, composition=composition)
                kind_desc = f"OptunaEnsembler（mode='{self.ens.get('MODE', 'free')}'）"
                return self._finalize(kind_desc, final_model, metrics, composition)
            except Exception as e:
                print(f"⚠️ 集成 Optuna 搜尋失敗，改用固定子集搜尋：{e}")

        # ============ 分支二：固定子集枚舉 ============ 
        if voting_mode in ("soft", "hard"):
            if self.ens.get("SEARCH", "none") == "voting_subsets":
                print("🔍 集成搜尋：使用固定子集枚舉搜尋（Top-K）。")
                results = self._search_voting_subsets(cpu_estimators, voting_mode)
                # 以最佳名稱組合重訓並保存（避免把 estimator 物件寫入 JSON）
                best_names = results["best_names"]
                pool = {n: e for n, e in cpu_estimators}
                best_ests = [(n, clone(pool[n])) for n in best_names]

                final_model = self._fit_voting(best_ests, voting_mode)
                self._save_ensemble(final_model)

                # 保存報告（json 全可序列化 + txt）
                self._dump_json(
                    os.path.join(self.out_dir, "reports", "ensemble_search_report.json"),
                    self._np_to_py({
                        "mode": results["mode"],
                        "topk": results["topk"],
                        "all_evaluated": results["all_evaluated"]
                    })
                )
                self._write_topk_txt(results["topk"])

                metrics, composition = self._eval_and_compose(final_model, kind="voting", estimators=best_ests)
                self._write_final_txt(kind="voting", metrics=metrics, composition=composition)
                kind_desc = f"VotingClassifier（voting='{voting_mode}'）"
                return self._finalize(kind_desc, final_model, metrics, composition)
            else:
                final_model = self._fit_voting(cpu_estimators, voting_mode)
                self._save_ensemble(final_model)
                metrics, composition = self._eval_and_compose(final_model, kind="voting", estimators=cpu_estimators)
                self._write_final_txt(kind="voting", metrics=metrics, composition=composition)
                kind_desc = f"VotingClassifier（voting='{voting_mode}'）"
                return self._finalize(kind_desc, final_model, metrics, composition)
        else:
            # Stacking
            final_model = self._fit_stacking(cpu_estimators, cv=stack_cv)
            self._save_ensemble(final_model)
            metrics, composition = self._eval_and_compose(final_model, kind="stacking", estimators=cpu_estimators)
            self._write_final_txt(kind="stacking", metrics=metrics, composition=composition)
            kind_desc = f"StackingClassifier（cv={stack_cv}）"
            return self._finalize(kind_desc, final_model, metrics, composition)

    # ============ Optuna 搜尋（Voting 子集＋權重） ============
    def _optuna_voting_search(self, estimators: List[Tuple[str, Any]], voting_mode: str):
        """使用 OptunaEnsembler 搜尋最佳權重與子集。"""
        est_dict = {n: e for n, e in estimators}
        ens = OptunaEnsembler(
            task_type=self.task_type,
            n_splits=int(self.ens.get("STACK_CV", 5)),
            n_trials=int(self.ens.get("OPTUNA_TRIALS", 30)),
            weight_mode=self.ens.get("WEIGHT_MODE", "dirichlet"),
            mode=self.ens.get("MODE", "free"),
            min_models=int(self.ens.get("MIN_MODELS", 2)),
            max_models=self.ens.get("MAX_MODELS"),
            pruning=bool(self.ens.get("PRUNING", True)),
            direction=self.ens.get("DIRECTION", "maximize"),
            seed=int(self.ens.get("SEED", 42)),
            report_dir=os.path.join(self.out_dir, "reports"),
        )
        info = ens.fit(est_dict, self.X_train, self.y_train, self.X_valid, self.y_valid)
        proba = ens.predict_proba(self.X_valid)
        y_pred = np.argmax(proba, axis=1)
        metrics = _compute_metrics(self.task_type, self.y_valid, y_pred, proba)
        composition = {
            "type": "voting",
            "voting": "soft",
            "estimators": info["selected"],
            "weights": info["weights"],
        }
        self._dump_json(
            os.path.join(self.out_dir, "reports", "ensemble_optuna_best.json"),
            {
                "selected": info["selected"],
                "weights": info["weights"],
                "best_score": info["best_score"],
                "strategy": info["strategy"],
                "metrics": self._np_to_py(metrics),
            },
        )
        return ens, metrics, composition

    # ---------------- Voting 子集枚舉（固定搜尋） ----------------
    def _search_voting_subsets(self, estimators: List[Tuple[str, Any]], mode: str) -> Dict[str, Any]:
        names = [n for n, _ in estimators]
        pool = {n: e for n, e in estimators}
        max_subset = int(self.ens.get("SEARCH_MAX_SUBSET", 4))
        topk_n = int(self.ens.get("SEARCH_TOPK", 3))

        cand_sets: List[List[str]] = []
        for r in range(2, min(max_subset, len(names)) + 1):
            for combo in itertools.combinations(names, r):
                cand_sets.append(list(combo))

        results_serializable = []
        best_tuple = None  # (metrics_key, names)
        for comb in cand_sets:
            ests = [(n, clone(pool[n])) for n in comb]
            model = self._fit_voting(ests, mode)
            metrics, _ = self._eval_and_compose(model, kind="voting", estimators=ests)

            # 可序列化：只存 names/metrics
            results_serializable.append({
                "names": list(comb),
                "metrics": self._np_to_py(metrics),
            })

            # 排序鍵（macro-F1，其次 ACC、AUC）
            auc_val = metrics.get("auc", np.nan)
            key = (metrics["f1"], metrics["acc"], -np.nan_to_num(auc_val, nan=-1.0))
            if (best_tuple is None) or (key > best_tuple[0]):
                best_tuple = (key, list(comb))

        # 依目標排序，取 Top-K（已是可序列化結構）
        def _key(r):
            m = r["metrics"]
            return (m["f1"], m["acc"], -np.nan_to_num(m.get("auc", np.nan), nan=-1.0))
        results_serializable.sort(key=_key, reverse=True)
        topk = results_serializable[:topk_n]

        return {
            "mode": mode,
            "topk": topk,                         # 可序列化
            "best_names": best_tuple[1],          # 提供最佳名稱清單以利重訓
            "all_evaluated": len(results_serializable)
        }

    # ---------------- 建模與評估 ----------------
    def _fit_voting(self, estimators: List[Tuple[str, Any]], mode: str):
        model = VotingClassifier(estimators=estimators, voting=mode, n_jobs=None)
        with parallel_backend("threading", n_jobs=1):
            model.fit(self.X_train, self.y_train)
        return model

    def _fit_stacking(self, estimators: List[Tuple[str, Any]], cv: int = 5):
        skf = StratifiedKFold(n_splits=cv, shuffle=True, random_state=42)
        final_est = LogisticRegression(max_iter=1000, n_jobs=1, multi_class="auto")
        model = StackingClassifier(estimators=estimators, final_estimator=final_est, cv=skf, n_jobs=None, passthrough=False)
        with parallel_backend("threading", n_jobs=1):
            model.fit(self.X_train, self.y_train)
        return model

    def _eval_and_compose(self, model, kind: str, estimators: List[Tuple[str, Any]]):
        y_pred = model.predict(self.X_valid)
        proba = None
        if hasattr(model, "predict_proba"):
            try:
                proba = model.predict_proba(self.X_valid)
            except Exception:
                proba = None
        metrics = _compute_metrics(self.task_type, self.y_valid, y_pred, proba)
        composition = self._extract_composition(model, kind, estimators)
        return metrics, composition

    def _extract_composition(self, model, kind: str, estimators: List[Tuple[str, Any]]) -> Dict[str, Any]:
        if kind == "voting" or isinstance(model, VotingClassifier):
            names = [n for n, _ in estimators]
            return {
                "type": "voting",
                "estimators": names,                          # 名稱清單（可序列化）
                "voting": getattr(model, "voting", "soft"),
                "weights": getattr(model, "weights", None),   # 可能為 None → 平均
            }
        # stacking：列出 meta LR 係數 top-k
        names = [n for n, _ in estimators]
        n_classes = len(self.classes_)
        feat_names = []
        for n in names:
            for k in range(n_classes):
                feat_names.append(f"{n}::class_{k}")
        clf = model.final_estimator_
        coef = getattr(clf, "coef_", None)
        topk_map = {}
        if coef is not None:
            K = min(5, len(feat_names))
            for c_idx in range(coef.shape[0]):
                coefs = coef[c_idx, :]
                order = np.argsort(-np.abs(coefs))[:K]
                tops = [(feat_names[j], float(coefs[j])) for j in order]
                cls_label = self.classes_[c_idx] if c_idx < len(self.classes_) else f"idx_{c_idx}"
                topk_map[cls_label] = tops
        return {
            "type": "stacking",
            "feature_names": feat_names,
            "coef": coef if coef is None else coef.tolist(),
            "classes": self.classes_.tolist(),
            "topk_per_class": topk_map
        }

    # ---------------- 保存 ----------------
    def _save_ensemble(self, model):
        try:
            os.makedirs(os.path.join(self.out_dir, "models"), exist_ok=True)
            path = os.path.join(self.out_dir, "models", "ensemble_best.joblib")
            dump(model, path)
            print(f"💾 已保存最佳 Ensemble：{path}")
        except Exception as e:
            print(f"⚠️ 保存 Ensemble 失敗：{e}")

    def _write_topk_txt(self, topk: List[Dict[str, Any]]) -> None:
        """將 Voting 子集搜尋的前 K 名輸出為純文字摘要。"""
        lines = []
        lines.append("🏆 Ensemble Voting 組合 Top-K：")
        for i, r in enumerate(topk, 1):
            m = r["metrics"]
            auc_val = m.get("auc", np.nan)
            auc_str = "nan" if np.isnan(auc_val) else f"{auc_val:.6f}"
            lines.append(f"[{i}] {list(r['names'])} | ACC={m['acc']:.6f} | macro-F1={m['f1']:.6f} | AUC={auc_str}")
        p = os.path.join(self.out_dir, "reports", "ensemble_topk.txt")
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

    def _write_final_txt(self, kind: str, metrics: Dict[str, Any], composition: Dict[str, Any]) -> None:
        """輸出最終選用的 Ensemble 組成與成績（純文字）。"""
        auc_val = metrics.get("auc", np.nan)
        auc_str = "nan" if np.isnan(auc_val) else f"{auc_val:.6f}"
        lines = []
        lines.append("🧩 Ensemble 最終選用：")
        if kind == "voting" or composition.get("type") == "voting":
            lines.append(f"  類型：Voting（voting='{composition.get('voting', 'soft')}'）")
            lines.append(f"  基模型：{composition.get('estimators')}")
            lines.append(f"  權重：{composition.get('weights') if composition.get('weights') is not None else '平均（None）'}")
        else:
            lines.append("  類型：Stacking（meta-learner = LogisticRegression）")
        lines.append(f"  成績：ACC={metrics['acc']:.6f} | F1={metrics['f1']:.6f} | AUC={auc_str}")
        p = os.path.join(self.out_dir, "reports", "ensemble_final.txt")
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

    # ---------------- 工具 ----------------
    def _dump_json(self, path: str, obj: Any):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(obj, f, ensure_ascii=False, indent=2)

    def _np_to_py(self, d: Dict[str, Any]) -> Dict[str, Any]:
        def _conv(v):
            import numpy as np
            if isinstance(v, (np.floating, np.integer)): return v.item()
            if isinstance(v, np.ndarray): return v.tolist()
            return v
        return {k: _conv(v) for k, v in d.items()}

    def _finalize(self, kind_desc: str, final_model, metrics: Dict[str, Any], composition: Dict[str, Any]) -> Dict[str, Any]:
        print(f"🧱 使用 {kind_desc}")
        print("🧪 驗證 Ensemble 中 ...")
        auc_val = metrics.get("auc", np.nan)
        auc_str = "nan" if np.isnan(auc_val) else f"{auc_val:.6f}"
        if self.task_type == "binary":
            print(f"📈 AUC={auc_str} | ACC={metrics['acc']:.6f} | F1={metrics['f1']:.6f}")
            print(f"✅ Ensemble 完成｜AUC={auc_str} | ACC={metrics['acc']:.6f} | F1={metrics['f1']:.6f}")
            print("ℹ️  二元分類可用 threshold（預設 THRESHOLD）；詳細報表見下方。")
        else:
            print(f"📈 OVR-AUC={auc_str} | ACC={metrics['acc']:.6f} | macro-F1={metrics['f1']:.6f}")
            print(f"✅ Ensemble 完成｜AUC={auc_str} | ACC={metrics['acc']:.6f} | F1={metrics['f1']:.6f}")
            print("ℹ️  多類別不套用 threshold；詳細報表見下方。")
        print("📋 分類報告：")
        print(metrics["report"])
        print("📝 混淆矩陣：")
        print(metrics["confusion_matrix"])
        if metrics.get("pred_dist"):
            print(f"📦 預測類別分佈：{metrics['pred_dist']}")
        print("🧩 Ensemble 組成：")
        if composition["type"] == "voting":
            print(f"  類型：Voting（voting='{composition['voting']}'）")
            print(f"  基模型：{composition['estimators']}")
            print(f"  權重：{composition['weights'] if composition['weights'] is not None else '平均（None）'}")
        else:
            print("  類型：Stacking（meta-learner = LogisticRegression）")
            topk = composition.get("topk_per_class", {})
            for cls_label, tops in topk.items():
                print(f"    - 類別 {cls_label}：")
                for feat, coef in tops:
                    print(f"        {feat:>24s} 係數={coef:+.4f}")
        return {
            "model": final_model,
            "metrics": metrics,
            "settings": self.ens,
            "composition": composition,
        }

    def _print_topk(self, topk: List[Dict[str, Any]]):
        print("\n🏆 Ensemble Voting 組合 Top-3：")
        for i, r in enumerate(topk, 1):
            m = r["metrics"]
            auc_val = m.get("auc", np.nan)
            auc_str = "nan" if np.isnan(auc_val) else f"{auc_val:.6f}"
            print(f"[{i}] {list(r['names'])} | ACC={m['acc']:.6f} | macro-F1={m['f1']:.6f} | AUC={auc_str}")


# ---------------------------------------------------------------------------
# Lightweight wrapper for OptunaEnsembler
# ---------------------------------------------------------------------------


def run_ensemble(
    estimators: Dict[str, Any],
    X,
    y,
    X_valid=None,
    y_valid=None,
    cfg: Optional[Dict[str, Any]] = None,
):
    """Convenience wrapper around :class:`OptunaEnsembler`.

    Parameters
    ----------
    estimators: Dict[str, Any]
        Mapping from estimator name to unfitted estimator instances.
    X, y: array-like
        Training data and labels.
    X_valid, y_valid: array-like, optional
        Hold-out validation set. When provided, scores mix CV and validation
        results (0.3 * CV + 0.7 * Valid).
    cfg: Dict[str, Any], optional
        Configuration dictionary. Keys mirror ``OptunaEnsembler`` init
        arguments.
    """

    cfg = cfg or {}
    mode = cfg.get("MODE", "free")
    ens = OptunaEnsembler(
        task_type=cfg.get("TASK_TYPE", "binary"),
        n_splits=cfg.get("STACK_CV", 5),
        n_trials=cfg.get("OPTUNA_TRIALS", 50),
        weight_mode=cfg.get("WEIGHT_MODE", "dirichlet"),
        mode=mode,
        min_models=cfg.get("MIN_MODELS", 2),
        max_models=cfg.get("MAX_MODELS", None),
        pruning=cfg.get("PRUNING", True),
        direction=cfg.get("DIRECTION", "maximize"),
        seed=cfg.get("SEED", 42),
        report_dir=cfg.get("REPORT_DIR", "./reports"),
    )
    return ens.fit(estimators, X, y, X_valid, y_valid)
