from __future__ import annotations

"""Optuna-based ensemble optimizer supporting free and fixed subset search modes."""

from dataclasses import dataclass
import json
import os
import itertools
from typing import Dict, List, Optional, Sequence

import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, clone
from sklearn.model_selection import StratifiedKFold
from sklearn.metrics import roc_auc_score

import optuna


# ---------------------------------------------------------------------------
# Utility functions
# ---------------------------------------------------------------------------

def auc(task: str, y_true, proba: np.ndarray) -> float:
    """Compute AUC for binary or multiclass tasks."""
    if proba.ndim == 1:
        proba = proba.reshape(-1, 1)
    if task == "binary":
        pos_idx = 1 if proba.shape[1] > 1 else 0
        return float(roc_auc_score(y_true, proba[:, pos_idx]))
    return float(roc_auc_score(y_true, proba, multi_class="ovr"))


def _normalize(weights: Sequence[float]) -> np.ndarray:
    w = np.array(weights, dtype=float)
    if not np.all(np.isfinite(w)) or w.sum() <= 0:
        w = np.ones(len(w), dtype=float)
    w /= w.sum()
    return w



def _ensure_numpy_xy(X, Y):
    X_np = X.to_numpy() if isinstance(X, (pd.DataFrame, pd.Series)) else np.asarray(X)
    y_np = Y.to_numpy().reshape(-1) if isinstance(Y, (pd.Series, pd.DataFrame)) else np.asarray(Y).reshape(-1)
    return X_np, y_np

# ---------------------------------------------------------------------------
# Core scorer
# ---------------------------------------------------------------------------

def score_combo(
    task: str,
    estimators: Dict[str, BaseEstimator],
    names: Sequence[str],
    weights: Sequence[float],
    X,
    y,
    n_splits: int,
    seed: int,
    trial: Optional[optuna.trial.Trial] = None,
    X_valid=None,
    y_valid=None,
) -> float:
    """Evaluate a weighted combination using CV and optional hold-out validation."""
    X_np, y_np = _ensure_numpy_xy(X, y)
    Xv_np = yv_np = None
    if X_valid is not None and y_valid is not None:
        Xv_np, yv_np = _ensure_numpy_xy(X_valid, y_valid)
    cv = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=seed)
    fold_scores: List[float] = []
    for fold, (tr_idx, va_idx) in enumerate(cv.split(X_np, y_np)):
        preds = []
        for name in names:
            est = clone(estimators[name])
            if hasattr(est, "get_params") and "random_state" in est.get_params():
                est.set_params(random_state=seed + fold)
            est.fit(X_np[tr_idx], y_np[tr_idx])
            preds.append(est.predict_proba(X_np[va_idx]))
        proba = np.average(preds, axis=0, weights=weights)
        fold_score = auc(task, y_np[va_idx], proba)
        fold_scores.append(fold_score)
        if trial is not None:
            trial.report(fold_score, fold)
            if trial.should_prune():
                raise optuna.TrialPruned()
    cv_score = float(np.mean(fold_scores))

    if Xv_np is not None and yv_np is not None:
        preds_v = []
        for name in names:
            est = clone(estimators[name])
            if hasattr(est, "get_params") and "random_state" in est.get_params():
                est.set_params(random_state=seed)
            est.fit(X_np, y_np)
            preds_v.append(est.predict_proba(Xv_np))
        proba_v = np.average(preds_v, axis=0, weights=weights)
        valid_score = auc(task, yv_np, proba_v)
        return 0.3 * cv_score + 0.7 * valid_score
    return cv_score


# ---------------------------------------------------------------------------
# OptunaEnsembler
# ---------------------------------------------------------------------------


@dataclass
class OptunaEnsembler:
    """Optuna based model ensembling."""

    task_type: str = "binary"
    n_splits: int = 5
    n_trials: int = 50
    weight_mode: str = "dirichlet"
    mode: str = "free"  # "free" or "fixed"
    min_models: int = 2
    max_models: Optional[int] = None
    pruning: bool = True
    direction: str = "maximize"
    seed: int = 42
    report_dir: Optional[str] = None

    def fit(
        self,
        estimators: Dict[str, BaseEstimator],
        X,
        y,
        X_valid=None,
        y_valid=None,
    ) -> Dict[str, object]:
        self.estimators = estimators
        names = list(estimators.keys())

        # Validate predict_proba and class counts
        n_classes = None
        for name, est in estimators.items():
            if not hasattr(est, "predict_proba"):
                raise ValueError(f"Estimator '{name}' lacks predict_proba")
            tmp = clone(est)
            if hasattr(tmp, "get_params") and "random_state" in tmp.get_params():
                tmp.set_params(random_state=self.seed)
            tmp.fit(X, y)
            proba = tmp.predict_proba(X[:2])
            if n_classes is None:
                n_classes = proba.shape[1]
            elif proba.shape[1] != n_classes:
                raise ValueError("Inconsistent number of classes among estimators")
        self.n_classes_ = n_classes

        sampler = optuna.samplers.TPESampler(seed=self.seed)
        pruner = optuna.pruners.MedianPruner() if self.pruning else optuna.pruners.NopPruner()
        study = optuna.create_study(direction=self.direction, sampler=sampler, pruner=pruner)

        if self.mode == "free":
            def objective(trial: optuna.trial.Trial) -> float:
                mask = [trial.suggest_int(f"use_{n}", 0, 1) for n in names]
                chosen = [n for n, m in zip(names, mask) if m]
                if len(chosen) < self.min_models:
                    raise optuna.TrialPruned()
                if self.max_models is not None and len(chosen) > self.max_models:
                    raise optuna.TrialPruned()
                if self.weight_mode == "dirichlet":
                    raw = [trial.suggest_float(f"w_{i}", 1e-3, 1.0, log=True) for i in range(len(chosen))]
                    weights = _normalize(raw)
                else:
                    raw = [trial.suggest_float(f"w_{i}", -5, 5) for i in range(len(chosen))]
                    weights = _normalize(np.exp(raw))
                return score_combo(
                    self.task_type,
                    estimators,
                    chosen,
                    weights,
                    X,
                    y,
                    self.n_splits,
                    self.seed,
                    trial if self.pruning else None,
                    X_valid,
                    y_valid,
                )

        else:  # fixed
            all_combos: List[Sequence[str]] = []
            max_m = self.max_models or len(names)
            for r in range(max(self.min_models, 1), min(max_m, len(names)) + 1):
                for comb in itertools.combinations(names, r):
                    all_combos.append(comb)

            def objective(trial: optuna.trial.Trial) -> float:
                idx = trial.suggest_int("subset_idx", 0, len(all_combos) - 1)
                chosen = list(all_combos[idx])
                if self.weight_mode == "dirichlet":
                    raw = [trial.suggest_float(f"w_{i}", 1e-3, 1.0, log=True) for i in range(len(chosen))]
                    weights = _normalize(raw)
                else:
                    raw = [trial.suggest_float(f"w_{i}", -5, 5) for i in range(len(chosen))]
                    weights = _normalize(np.exp(raw))
                return score_combo(
                    self.task_type,
                    estimators,
                    chosen,
                    weights,
                    X,
                    y,
                    self.n_splits,
                    self.seed,
                    trial if self.pruning else None,
                    X_valid,
                    y_valid,
                )

        study.optimize(objective, n_trials=self.n_trials, show_progress_bar=False)
        best = study.best_trial

        if self.mode == "free":
            best_names = [n for n in names if best.params.get(f"use_{n}")]
        else:
            idx = int(best.params["subset_idx"])
            best_names = list(all_combos[idx])

        if self.weight_mode == "dirichlet":
            raw = [best.params.get(f"w_{i}") for i in range(len(best_names))]
            weights = _normalize(raw)
        else:
            raw = [best.params.get(f"w_{i}") for i in range(len(best_names))]
            weights = _normalize(np.exp(raw))

        # fit final models
        self.selected_ = best_names
        self.weights_ = weights.tolist()
        self.best_score_ = float(best.value)
        self.strategy_ = f"optuna-{self.mode}"
        self.fitted_: List[BaseEstimator] = []
        for i, name in enumerate(best_names):
            est = clone(estimators[name])
            if hasattr(est, "get_params") and "random_state" in est.get_params():
                est.set_params(random_state=self.seed)
            est.fit(X, y)
            self.fitted_.append(est)

        if self.report_dir:
            os.makedirs(self.report_dir, exist_ok=True)
            report_path = os.path.join(self.report_dir, "ensemble_optuna_best.json")
            with open(report_path, "w", encoding="utf-8") as f:
                json.dump(
                    {
                        "selected": self.selected_,
                        "weights": self.weights_,
                        "best_score": self.best_score_,
                        "task_type": self.task_type,
                        "n_splits": self.n_splits,
                        "n_trials": self.n_trials,
                        "mode": self.mode,
                        "weight_mode": self.weight_mode,
                        "min_models": self.min_models,
                        "max_models": self.max_models,
                        "seed": self.seed,
                    },
                    f,
                    indent=2,
                    ensure_ascii=False,
                )

        return {
            "selected": self.selected_,
            "weights": self.weights_,
            "best_score": self.best_score_,
            "strategy": self.strategy_,
        }

    # ------------------------------------------------------------------
    def predict_proba(self, X) -> np.ndarray:
        """Aggregate各子模型的機率預測並依權重加總。"""
        preds = [est.predict_proba(X) for est in self.fitted_]
        proba = np.average(preds, axis=0, weights=self.weights_)
        return proba


__all__ = ["OptunaEnsembler", "auc", "score_combo"]
