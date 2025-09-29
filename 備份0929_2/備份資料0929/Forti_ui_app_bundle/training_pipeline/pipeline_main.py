# training_pipeline/pipeline_main.py
from __future__ import annotations

import os
import json
import time
from typing import Any, Dict, Tuple, List
import numpy as np
from sklearn.model_selection import train_test_split

try:
    from utils_labels import encode_crlevel_series, save_label_mapping
except ModuleNotFoundError as exc:  # pragma: no cover - package-relative fallback
    if exc.name != "utils_labels":
        raise
    if not __package__:
        raise
    from ..utils_labels import encode_crlevel_series, save_label_mapping

# === 你專案內的模組 ===
try:
    from training_pipeline.data_loader import DataLoader              # load_data(), prepare_xy_with_report()
    from training_pipeline.model_builder import ModelBuilder          # build_models(X, y, task=...)
    from training_pipeline.trainer import Trainer                     # train(models, X, y) -> dict
    from training_pipeline.evaluator import Evaluator                 # evaluate(...)
except ModuleNotFoundError as exc:  # pragma: no cover - package-relative fallback
    if exc.name != "training_pipeline":
        raise
    if not __package__:
        raise
    from .data_loader import DataLoader
    from .model_builder import ModelBuilder
    from .trainer import Trainer
    from .evaluator import Evaluator

# config：載入預設組態
try:
    from training_pipeline.config import CONFIG_BINARY, CONFIG_MULTICLASS
except ModuleNotFoundError as exc:  # pragma: no cover - package-relative fallback
    if exc.name != "training_pipeline":
        raise
    if not __package__:
        raise
    try:
        from .config import CONFIG_BINARY, CONFIG_MULTICLASS
    except Exception:
        CONFIG_BINARY, CONFIG_MULTICLASS = {}, {}
except Exception:
    CONFIG_BINARY, CONFIG_MULTICLASS = {}, {}

# Ensemble：優先使用 ComboOptimizer；若不可用則回退 DMW
_USE_COMBO = True
try:
    from training_pipeline.combo_optimizer import ComboOptimizer
except ModuleNotFoundError as exc:  # pragma: no cover - package-relative fallback
    if exc.name != "training_pipeline":
        raise
    if not __package__:
        raise
    try:
        from .combo_optimizer import ComboOptimizer
    except Exception:
        _USE_COMBO = False
except Exception:
    _USE_COMBO = False


def _load_dmw_class():
    """Import ``DynamicSoftVoter`` with a relative fallback."""

    try:
        from training_pipeline.dmw import DynamicSoftVoter
    except ModuleNotFoundError as exc:  # pragma: no cover - package-relative fallback
        if exc.name != "training_pipeline":
            raise
        if not __package__:
            raise
        from .dmw import DynamicSoftVoter
    return DynamicSoftVoter


def _merge_dict(base: Dict[str, Any], override: Dict[str, Any] | None) -> Dict[str, Any]:
    """Deep-merge default config with user override.

    Using ``dict()`` on ``base`` only creates a shallow copy which means nested
    dictionaries (e.g. ``ENSEMBLE_SETTINGS``) would be shared between different
    pipeline instances. Any in-place modification done by the UI could then leak
    back and mutate the module level defaults, causing subsequent runs to pick
    up stale values like ``SEARCH='voting_subsets'`` even when the user did not
    request it.  A deep copy keeps each run isolated.
    """

    from copy import deepcopy

    out = deepcopy(base or {})
    if override:
        out.update(override)
    return out


class TrainingPipeline:
    def __init__(self,
                 task_type: str = "binary",
                 optuna_enabled: bool = False,
                 optimize_base: bool = False,
                 optimize_ensemble: bool = False,
                 use_tuned_for_training: bool = True,   # ★ 新增：是否套用 Optuna 結果至後續訓練/集成
                 config: Any = None,
                 logger: Any = None) -> None:
        self.task_type = task_type
        self.optuna_enabled = bool(optuna_enabled)
        self.optimize_base = bool(optimize_base)
        self.optimize_ensemble = bool(optimize_ensemble)
        self.use_tuned_for_training = bool(use_tuned_for_training)
        self.logger = logger

        default_cfg = CONFIG_BINARY if task_type == "binary" else CONFIG_MULTICLASS
        user_cfg = config if isinstance(config, dict) else {}
        self.config: Dict[str, Any] = _merge_dict(default_cfg, user_cfg)

        if "TARGET_COLUMN" not in self.config:
            self.config["TARGET_COLUMN"] = "is_attack" if task_type == "binary" else "crlevel"
        self.config.setdefault("VALID_SIZE", 0.2)
        self.config.setdefault("RANDOM_STATE", 42)
        self.config.setdefault("ENSEMBLE_SETTINGS", {
            "STACK_CV": 5, "VOTING": "soft", "THRESHOLD": 0.5,
            "SEARCH": "none", "SEARCH_MAX_SUBSET": 4, "SEARCH_TOPK": 3, "MIN_MODELS": 2
        })
        self.config.setdefault("OUTPUT_DIR", "./artifacts")
        self.config.setdefault("SAVE_BASE_MODELS", False)

        self.evaluator = Evaluator(task=("binary" if task_type == "binary" else "multiclass"))
        self.out_dir: str | None = None

    # ---------- helpers ----------
    def _say(self, msg: str) -> None:
        print(msg)

    def _prepare_artifacts_dir(self) -> str:
        root = self.config.get("OUTPUT_DIR", "./artifacts")
        ts = time.strftime("%Y%m%d_%H%M%S")
        out_dir = os.path.join(root, ts)
        os.makedirs(os.path.join(out_dir, "models"), exist_ok=True)
        os.makedirs(os.path.join(out_dir, "reports"), exist_ok=True)
        os.makedirs(os.path.join(out_dir, "optuna"), exist_ok=True)
        print(f"📁 輸出目錄：{out_dir}")
        return out_dir

    def _dump_json(self, path: str, obj: Any) -> None:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(obj, f, ensure_ascii=False, indent=2)

    def _np_to_py(self, obj: Any) -> Any:
        """Recursively convert NumPy objects to pure Python types."""
        if isinstance(obj, dict):
            return {k: self._np_to_py(v) for k, v in obj.items()}
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        if isinstance(obj, (np.floating, np.integer)):
            return obj.item()
        return obj

    # ===== 匯出「可直接覆蓋 config.py」的 MODEL_PARAMS 片段 =====
    def _export_config_overwrite_snippet(self, trained: Dict[str, Any]) -> None:
        model_keys_whitelist: Dict[str, List[str]] = {}
        base_mp: Dict[str, Dict[str, Any]] = self.config.get("MODEL_PARAMS", {}) or {}
        for m in ["XGB", "LGB", "CAT", "RF", "ET"]:
            if m in base_mp and isinstance(base_mp[m], dict) and len(base_mp[m]) > 0:
                model_keys_whitelist[m] = list(base_mp[m].keys())

        defaults = {
            "XGB": ["n_estimators", "max_depth", "learning_rate", "subsample", "colsample_bytree",
                    "tree_method", "device", "eval_metric"],
            "LGB": ["n_estimators", "max_depth", "learning_rate", "num_leaves", "device_type"],
            "CAT": ["iterations", "depth", "learning_rate", "task_type", "devices"],
            "RF":  ["n_estimators", "max_depth"],
            "ET":  ["n_estimators", "max_depth"],
        }

        compact: Dict[str, Dict[str, Any]] = {}
        for name, est in trained.items():
            gp = getattr(est, "get_params", None)
            if not callable(gp):
                continue
            params = gp()
            keys = model_keys_whitelist.get(name, defaults.get(name, []))
            kv = {}
            for k in keys:
                if k in params:
                    kv[k] = params[k]
            compact[name] = kv

        self._dump_json(os.path.join(self.out_dir, "optuna", "best_params_compact.json"), compact)
        cfg_var = "CONFIG_BINARY" if self.task_type == "binary" else "CONFIG_MULTICLASS"
        lines = []
        lines.append("# === 將下列片段貼回 config.py 覆蓋該任務的 MODEL_PARAMS ===")
        lines.append(f"{cfg_var}['MODEL_PARAMS'] = {{")
        for m in ["XGB", "LGB", "CAT", "RF", "ET"]:
            if m in compact:
                lines.append(f"    '{m}': {compact[m]},")
        lines.append("}\n")
        txt = "\n".join(lines)
        path_txt = os.path.join(self.out_dir, "optuna", "overwrite_config_MODEL_PARAMS.txt")
        os.makedirs(os.path.dirname(path_txt), exist_ok=True)
        with open(path_txt, "w", encoding="utf-8") as f:
            f.write(txt)
        print("📝 超參數覆寫片段已輸出：optuna/overwrite_config_MODEL_PARAMS.txt")

    # ---------- 資料處理 ----------
    def _load_and_split(self, file_path: str):
        dl = DataLoader(self.config)
        df = dl.load_data(file_path)  # ✅ 第一次訊息在 DataLoader 內印

        # 取得欄位差異報告並顯示（第二次訊息同時在 DataLoader 內印摘要）
        X, y, report = DataLoader.prepare_xy_with_report(df, self.config, self.task_type)
        if self.task_type == "multiclass":
            y = encode_crlevel_series(y)
            save_label_mapping(self.out_dir)
        else:
            y = y.astype("int32")

        test_size = float(self.config.get("VALID_SIZE", 0.2))
        random_state = int(self.config.get("RANDOM_STATE", 42))
        X_tr, X_va, y_tr, y_va = train_test_split(
            X, y, test_size=test_size, random_state=random_state, stratify=y
        )

        # 第三次訊息：分集完成
        print(f"✅ 分割完成：訓練 {len(X_tr)}、驗證 {len(X_va)}")

        X_tr = X_tr.reset_index(drop=True)
        X_va = X_va.reset_index(drop=True)
        y_tr = y_tr.reset_index(drop=True)
        y_va = y_va.reset_index(drop=True)

        return X_tr, X_va, y_tr, y_va

    def _build_models(self, X_train, y_train) -> Dict[str, Any]:
        mb = ModelBuilder(
            config=self.config,
            use_optuna=(self.optuna_enabled and self.optimize_base and self.use_tuned_for_training),
            max_trials_xgb=int(self.config.get("MAX_TRIALS_XGB", 15)),
            max_trials_others=int(self.config.get("MAX_TRIALS_OTHERS", 10)),
            enable_pruner=True,
        )

        # Case 1：使用 Optuna 結果建模（內部自動 run_optuna）
        task_name = "binary" if self.task_type == "binary" else "multiclass"

        if self.optuna_enabled and self.optimize_base and self.use_tuned_for_training:
            models = mb.build_models(X_train, y_train, task=task_name)
            return models

        # Case 2：執行 Optuna（僅記錄、不套用），再用 config 建模
        if self.optuna_enabled and self.optimize_base and (not self.use_tuned_for_training):
            try:
                _ = mb.run_optuna(X_train, y_train, self.task_type)  # 產出 best_params（僅紀錄）
                print("🧪 Optuna 已執行（僅記錄結果，不套用於後續訓練）。")
            except Exception as e:
                print(f"⚠️ Optuna 執行失敗（僅記錄階段），將跳過：{e}")
            models = mb.build_models(X_train, y_train, task=task_name)
            return models

        # Case 3：完全不啟用 Optuna

        if not self.optuna_enabled:
            print("🚫 Optuna 未啟用，使用 config 參數建模。")

        models = mb.build_models(X_train, y_train, task=task_name)
        return models

    # ---------- public ----------
    def run(self, file_path: str) -> Dict[str, Any]:
        self.out_dir = self._prepare_artifacts_dir()

        X_train, X_valid, y_train, y_valid = self._load_and_split(file_path)

        models = self._build_models(X_train, y_train)

        trainer = Trainer()
        trained = trainer.train(models, X_train, y_train)

        print("\n=== 單模型評估 ===\n")
        single_results = {}
        for name, model in trained.items():
            res = self.evaluator.evaluate(model, X_valid, y_valid, name=name)
            single_results[name] = res
        single_results_py = {n: self._np_to_py(r) for n, r in single_results.items()}
        self._dump_json(os.path.join(self.out_dir, "reports", "single_model_results.json"), single_results_py)

        # 保存基模型（依設定；預設不存）與最佳參數覆寫片段（若啟用基模型優化）
        if self.optuna_enabled and self.optimize_base:
            self._export_config_overwrite_snippet(trained)

        # === 集成（Ensemble） ===
        print("\n=== 集成（Ensemble）階段 ===")
        if _USE_COMBO:
            combo = ComboOptimizer(
                estimators=[(n, trained[n]) for n in trained.keys()],
                X_train=X_train, y_train=y_train,
                X_valid=X_valid, y_valid=y_valid,
                task_type=self.task_type,
                config=self.config,
                logger=self.logger,
                out_dir=self.out_dir,
                # ★ 傳遞旗標（目前 ComboOptimizer 未實作 Optuna 介面，照實提示）
                use_optuna=(self.optuna_enabled and self.optimize_ensemble and self.use_tuned_for_training),
            )
            if self.optuna_enabled and self.optimize_ensemble:
                if self.use_tuned_for_training:
                    print("🧪 集成優化：已啟用 Optuna 搜尋。")
                else:
                    print("🧪 集成優化：選擇不套用 Optuna 結果，改以固定子集搜尋邏輯。")

            ensemble_results = combo.optimize()
        else:
            DynamicSoftVoter = _load_dmw_class()
            dmw = DynamicSoftVoter(
                estimators=[(n, trained[n]) for n in trained.keys()],
                init_metric="auc" if self.task_type == "binary" else "recall",
                init_cv=int(self.config.get("STACK_CV", 5)),
                eta=0.2,
                verbose=False,
                n_jobs=None
            )
            dmw.fit(X_train, y_train)
            _ = self.evaluator.evaluate(dmw, X_valid, y_valid, name="DMW-Ensemble")
            ensemble_results = {"model": dmw, "settings": {"DMW": True}, "metrics": {}}
        ensemble_metrics_py = self._np_to_py(ensemble_results.get("metrics", {}))
        summary = {
            "task_type": self.task_type,
            "single_models": single_results_py,
            "ensemble": ensemble_metrics_py,
        }
        self._dump_json(os.path.join(self.out_dir, "reports", "evaluation_summary.json"), summary)

        print(f"📦 產出已保存於：{self.out_dir}")

        return {
            "single_models": trained,
            "single_results": single_results,
            "ensemble": ensemble_results,
            "artifacts_dir": self.out_dir,
        }
