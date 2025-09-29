# training_pipeline/model_optimizer.py
import optuna
import numpy as np
from sklearn.model_selection import cross_val_score

class ModelOptimizer:
    def __init__(self, model_class, param_space, n_trials=30, scoring="roc_auc", random_state=42):
        self.model_class = model_class
        self.param_space = param_space
        self.n_trials = n_trials
        self.scoring = scoring
        self.random_state = random_state
        self.best_params = None

    def _objective(self, trial, X, y):
        params = {key: fn(trial) for key, fn in self.param_space.items()}
        try:
            model = self.model_class(**params, random_state=self.random_state)
        except TypeError:
            model = self.model_class(**params)
        scoring = self.scoring
        if scoring == "roc_auc" and len(np.unique(y)) > 2:
            scoring = "roc_auc_ovr"
        score = cross_val_score(model, X, y, cv=3, scoring=scoring, error_score=np.nan).mean()
        return score

    def optimize(self, X, y):
        study = optuna.create_study(direction="maximize")
        study.optimize(lambda trial: self._objective(trial, X, y), n_trials=self.n_trials)
        self.best_params = study.best_params
        print(f"✅ 最佳參數：{self.best_params}")
        return self.best_params