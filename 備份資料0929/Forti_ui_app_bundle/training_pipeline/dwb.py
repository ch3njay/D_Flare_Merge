# dwb.py
import numpy as np
from sklearn.base import BaseEstimator, ClassifierMixin, clone
from sklearn.model_selection import StratifiedKFold

def class_weights(y, beta=0.5, eps=1e-6):
    y = np.asarray(y)
    classes, counts = np.unique(y, return_counts=True)
    N, K = len(y), len(classes)
    return {int(c): (N / (K * (n + eps))) ** beta for c, n in zip(classes, counts)}

def true_class_proba(y_true, proba):
    y_true = np.asarray(y_true)
    proba = np.asarray(proba)
    if proba.ndim == 1:  # binary score
        return (y_true==1)*proba + (y_true==0)*(1-proba)
    return proba[np.arange(len(y_true)), y_true.astype(int)]

def build_weights(y, pt, cw, rarity=None, cost=None, disagree=None,
                  gamma=1.5, delta=0.5, alpha=0.5, wmin=0.2, wmax=5.0, normalize=True):
    # 難例
    dw = np.power(1.0 - pt, gamma)
    # 罕見度/漂移
    if rarity is None:
        rw = np.ones_like(dw)
    else:
        med = np.median(rarity[rarity>0]) if (rarity is not None and np.any(rarity>0)) else 1.0
        rw = np.power(med / (rarity + 1e-6), delta)
    # 成本
    mw = np.ones_like(dw) if cost is None else np.array([cost[int(c)] for c in y], float)
    # 分歧度
    uw = 1.0 + (alpha * (disagree if disagree is not None else 0.0))
    base = np.array([cw[int(c)] for c in y], float)
    w = base * dw * rw * mw * uw
    if normalize:
        w = w / (w.mean() if w.mean() > 0 else 1.0)
    return np.clip(w, wmin, wmax)

class DWBWrapper(BaseEstimator, ClassifierMixin):
    """通用包裝器：先用類別權重做 OOF 得到 pt，再以 DWB 權重全量重訓"""
    def __init__(self, base_estimator, k=5, beta=0.5, gamma=1.5, delta=0.5, alpha=0.5,
                 wmin=0.2, wmax=5.0, random_state=42):
        self.base_estimator = base_estimator
        self.k = k; self.beta=beta; self.gamma=gamma
        self.delta=delta; self.alpha=alpha; self.wmin=wmin; self.wmax=wmax
        self.random_state=random_state

    def fit(self, X, y, rarity=None, cost=None, disagree=None):
        X = np.asarray(X); y = np.asarray(y)
        cw = class_weights(y, beta=self.beta)
        # 1) OOF 取得 pt
        skf = StratifiedKFold(n_splits=self.k, shuffle=True, random_state=self.random_state)
        proba_oof = np.zeros((len(y), len(np.unique(y))))
        for tr, va in skf.split(X, y):
            est = clone(self.base_estimator)
            sw = np.array([cw[int(c)] for c in y[tr]], float)
            est.fit(X[tr], y[tr], sample_weight=sw)
            p = est.predict_proba(X[va]) if hasattr(est, "predict_proba") else np.full((len(va), len(np.unique(y))), 1/len(np.unique(y)))
            proba_oof[va] = p[:, :proba_oof.shape[1]] if p.shape[1]>=proba_oof.shape[1] else np.pad(p, ((0,0),(0,proba_oof.shape[1]-p.shape[1])))

        pt = true_class_proba(y, proba_oof)
        # 2) 建 w 後全量重訓
        w = build_weights(y, pt, cw, rarity=rarity, cost=cost, disagree=disagree,
                          gamma=self.gamma, delta=self.delta, alpha=self.alpha,
                          wmin=self.wmin, wmax=self.wmax, normalize=True)
        self.est_ = clone(self.base_estimator)
        self.est_.fit(X, y, sample_weight=w)
        return self

    def predict(self, X): return self.est_.predict(X)
    def predict_proba(self, X):
        return self.est_.predict_proba(X) if hasattr(self.est_, "predict_proba") else None
