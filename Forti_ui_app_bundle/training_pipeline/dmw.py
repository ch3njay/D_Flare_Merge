# training_pipeline/dmw.py
from __future__ import annotations
from typing import Dict, List, Tuple, Optional
import numpy as np
from sklearn.ensemble import VotingClassifier
from sklearn.model_selection import StratifiedKFold
from sklearn.metrics import roc_auc_score, recall_score, confusion_matrix
from sklearn.base import clone

def _sigmoid(x: np.ndarray) -> np.ndarray:
    return 1.0 / (1.0 + np.exp(-x))

def _ensure_proba(est, X) -> np.ndarray:
    """
    統一保證輸出 shape=(n_samples, n_classes) 的機率：
    1) 有 predict_proba -> 直接使用（處理 binary 單欄情況）
    2) 有 decision_function -> 對二分類做 sigmoid，對多類做 softmax
    3) 否則用 predict one-hot 當作機率退化替代
    """
    # 1) predict_proba（最佳）
    if hasattr(est, "predict_proba"):
        proba = est.predict_proba(X)
        if proba.ndim == 1:                       # 二分類某些模型會回傳 (n_samples,)
            proba = np.vstack([1.0 - proba, proba]).T
        return proba

    # 2) decision_function -> 轉成機率
    if hasattr(est, "decision_function"):
        df = np.asarray(est.decision_function(X))
        if df.ndim == 1:                          # binary
            p1 = 1.0 / (1.0 + np.exp(-df))
            return np.vstack([1.0 - p1, p1]).T
        # multi-class: softmax
        m = df.max(axis=1, keepdims=True)
        ex = np.exp(df - m)
        return ex / ex.sum(axis=1, keepdims=True)

    # 3) fallback: one-hot on predict
    pred = est.predict(X)
    classes = np.unique(pred)
    proba = np.zeros((len(pred), len(classes)))
    for i, c in enumerate(classes):
        proba[pred == c, i] = 1.0
    return proba


def _per_class_auc(y_true: np.ndarray, proba: np.ndarray, labels: np.ndarray) -> np.ndarray:
    K = len(labels)
    scores = np.zeros(K, dtype=float)
    for idx, c in enumerate(labels):
        y_bin = (y_true == c).astype(int)
        try:
            scores[idx] = roc_auc_score(y_bin, proba[:, idx])
        except Exception:
            scores[idx] = 0.5
    return scores

def _per_class_recall(y_true: np.ndarray, y_pred: np.ndarray, labels: np.ndarray) -> np.ndarray:
    try:
        cm = confusion_matrix(y_true, y_pred, labels=labels)
        denom = cm.sum(axis=1)
        with np.errstate(divide="ignore", invalid="ignore"):
            rec = np.where(denom > 0, np.diag(cm) / denom, 0.0)
        return rec
    except Exception:
        return np.array([recall_score(y_true == c, y_pred == c, zero_division=0) for c in labels])

def _normalize_weights(w: np.ndarray) -> np.ndarray:
    s = w.sum()
    return (w / s) if s > 0 else np.ones_like(w) / len(w)

def init_soft_weights(
    per_class_scores: Dict[str, np.ndarray],
    class_importance: Optional[np.ndarray] = None
) -> tuple[list[str], np.ndarray]:
    names = sorted(per_class_scores.keys())
    K = len(next(iter(per_class_scores.values())))
    lam = class_importance if class_importance is not None else np.ones(K)
    raw = np.array([(per_class_scores[n] * lam).sum() for n in names], dtype=float)
    raw = np.maximum(raw, 1e-8)
    w = _normalize_weights(raw)
    return names, w

def exp_grad_update(w: np.ndarray, grad: np.ndarray, eta: float = 0.2) -> np.ndarray:
    w_new = w * np.exp(eta * grad)
    return _normalize_weights(w_new)

def _set_params_if_supported(est, **kwargs):
    try:
        est.set_params(**kwargs)
    except Exception:
        pass
    return est

# -----------------------------
# 遞迴：OOF 階段用的 clone（保留結構）
# -----------------------------
def _clone_for_oof(est):
    e = clone(est)
    cls = e.__class__.__name__.lower()

    if "stackingclassifier" in cls:
        new_estimators = []
        for name, sub in e.estimators:
            new_estimators.append((name, _clone_for_oof(sub)))
        e.estimators = new_estimators
        if getattr(e, "final_estimator", None) is not None:
            e.final_estimator = _clone_for_oof(e.final_estimator)
        e = _set_params_if_supported(e, n_jobs=1)
    return e

# -----------------------------
# 遞迴：最終 fit 前的「硬化」處理（僅調整堆疊結構）
# -----------------------------
def _finalize_estimators_for_fit(estimators: List[Tuple[str, object]]) -> List[Tuple[str, object]]:
    new_items: List[Tuple[str, object]] = []
    for name, est in estimators:
        new_items.append((name, _finalize_single_estimator(est)))
    return new_items

def _finalize_single_estimator(est):
    cls = est.__class__.__name__.lower()

    # Stacking：遞迴處理所有子模型 + final_estimator
    if "stackingclassifier" in cls:
        # 1) base estimators
        new_estimators = []
        for nm, sub in est.estimators:
            new_estimators.append((nm, _finalize_single_estimator(sub)))
        est.estimators = new_estimators
        # 2) final estimator
        if getattr(est, "final_estimator", None) is not None:
            est.final_estimator = _finalize_single_estimator(est.final_estimator)
        # 3) 降低併行以穩定
        est = _set_params_if_supported(est, n_jobs=1)
    return est

class DynamicSoftVoter(VotingClassifier):
    """
    - voting='soft'
    - fit() 前用 OOF 估 per-class 分數初始化各基模型的軟投票權重
    - 最終 fit 前遞迴「硬化」：處理巢狀結構並統一併行設定
    - 可在視窗資料上用指數權重更新 (Hedge) 做線上微調
    - 自動處理 DataFrame 欄位名：訓練若用 DataFrame，之後收到 ndarray 會自動補回欄位名
    """
    def __init__(
        self,
        estimators: List[Tuple[str, object]],
        class_importance: Optional[np.ndarray] = None,
        init_metric: str = "auc",   # "auc" 或 "recall"
        init_cv: int = 5,
        eta: float = 0.2,
        verbose: bool = False,
        n_jobs: Optional[int] = None
    ):
        super().__init__(estimators=estimators, voting="soft", weights=None, n_jobs=n_jobs, flatten_transform=False)
        self.class_importance = class_importance
        self.init_metric = init_metric
        self.init_cv = init_cv
        self.eta = eta
        self.verbose = verbose
        self.model_names_: List[str] = [n for n, _ in estimators]
        self.weights_: Optional[np.ndarray] = None
        self.labels_: Optional[np.ndarray] = None
        self.feature_columns_: Optional[List[str]] = None

    # --- DataFrame 欄位名輔助 ---
    def _maybe_to_df(self, X):
        if self.feature_columns_ is not None and not hasattr(X, "columns"):
            import pandas as pd
            return pd.DataFrame(X, columns=self.feature_columns_)
        return X

    # --- OOF 初始化（僅用 numpy，避免小切片不穩） ---
    def _init_weights_via_oof(self, X: np.ndarray, y: np.ndarray) -> np.ndarray:
        skf = StratifiedKFold(n_splits=self.init_cv, shuffle=True, random_state=42)
        labels = np.unique(y)
        self.labels_ = labels
        per_model_scores: Dict[str, np.ndarray] = {}

        for n, est in self.estimators:
            fold_scores = []
            for tr, va in skf.split(X, y):
                est_fold = _clone_for_oof(est)
                est_fold.fit(X[tr], y[tr])
                proba = _ensure_proba(est_fold, X[va])
                # 對齊類別欄寬
                if proba.shape[1] != len(labels):
                    if proba.shape[1] > len(labels):
                        proba = proba[:, :len(labels)]
                    else:
                        pad = np.zeros((proba.shape[0], len(labels) - proba.shape[1]))
                        proba = np.hstack([proba, pad])
                if self.init_metric == "auc":
                    s = _per_class_auc(y[va], proba, labels)
                else:
                    y_pred = labels[np.argmax(proba, axis=1)]
                    s = _per_class_recall(y[va], y_pred, labels)
                fold_scores.append(s)
            per_model_scores[n] = np.array(fold_scores).mean(axis=0)

        names, w = init_soft_weights(per_class_scores=per_model_scores, class_importance=self.class_importance)
        if self.verbose:
            print("[DMW] 初始 per-class 分數：")
            for n in names:
                print(f"  - {n}: {per_model_scores[n]}")
            print(f"[DMW] 初始權重 (sum=1): {w}")
        return w

    # --- sklearn 介面 ---
    def fit(self, X, y, sample_weight=None):
        # 1) 記錄訓練欄位名（若是 DataFrame）
        self.feature_columns_ = list(X.columns) if hasattr(X, "columns") else None
        # 2) OOF 初始化權重（使用 numpy）
        w0 = self._init_weights_via_oof(np.asarray(X), np.asarray(y))
        self.weights_ = w0
        self.weights = w0.tolist()
        # 3) 最終 fit 前，遞迴硬化所有 estimator（統一處理堆疊結構）
        self.estimators = _finalize_estimators_for_fit(self.estimators)
        # 4) 正式訓練（VotingClassifier 內會逐一 .fit）
        return super().fit(X, y, sample_weight=sample_weight)

    def predict(self, X):
        X = self._maybe_to_df(X)
        return super().predict(X)

    def predict_proba(self, X):
        X = self._maybe_to_df(X)
        return super().predict_proba(X)

    # 收集各基模型在新資料的機率（供線上更新）
    def probas_per_estimator(self, X) -> Dict[str, np.ndarray]:
        assert hasattr(self, "estimators_"), "請先 fit 再呼叫"
        X = self._maybe_to_df(X)
        out = {}
        items = list(self.named_estimators_.items()) if hasattr(self, "named_estimators_") else self.estimators_
        for name, est in items:
            out[name] = _ensure_proba(est, X)
        return out

    # 線上視窗更新（Hedge）
    def update_with_window(
        self,
        y_true: np.ndarray,
        probas_per_model: Dict[str, np.ndarray],
        metric: str = "recall"
    ) -> np.ndarray:
        assert self.weights_ is not None, "請先 fit 再更新權重"
        labels = self.labels_
        lam = self.class_importance if self.class_importance is not None else np.ones(len(labels))
        scores = []
        for n in self.model_names_:
            proba = probas_per_model[n]
            if metric == "auc":
                s = _per_class_auc(y_true, proba, labels)
            else:
                y_pred = labels[np.argmax(proba, axis=1)]
                s = _per_class_recall(y_true, y_pred, labels)
            scores.append((s * lam).sum())
        scores = np.array(scores, dtype=float)

        ensemble_score = float(np.dot(self.weights_, scores))
        grad = scores - ensemble_score
        self.weights_ = exp_grad_update(self.weights_, grad, eta=self.eta)
        self.weights = self.weights_.tolist()
        if self.verbose:
            print(f"[DMW] window score: {scores}, ensemble={ensemble_score:.4f}, new_w={self.weights_}")
        return self.weights_
