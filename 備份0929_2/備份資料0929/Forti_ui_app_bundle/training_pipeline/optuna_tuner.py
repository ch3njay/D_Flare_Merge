# training_pipeline/optuna_tuner.py
from __future__ import annotations
import argparse
import json
import os
from typing import Dict, Any

import numpy as np
import optuna
import pandas as pd
from sklearn.metrics import roc_auc_score, f1_score
from sklearn.model_selection import StratifiedKFold

from xgboost import XGBClassifier

try:  # optional GPU acceleration
    import cupy as cp

    if getattr(cp, "__name__", "") != "cupy":  # fallback stubs
        cp = None  # type: ignore[assignment]
except Exception:  # pragma: no cover - cupy is optional
    cp = None  # type: ignore[assignment]


from .feature_policy import FeaturePolicy

# -------------------------
# 讀取資料（你可改為實際的 data_loader）
# -------------------------
def load_dataset(csv_path: str) -> pd.DataFrame:
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"找不到資料檔：{csv_path}")
    df = pd.read_csv(csv_path)
    return df

# -------------------------
# 目標函式：與正式訓練共用 FeaturePolicy
# -------------------------
def build_objective(
    df: pd.DataFrame,
    policy: FeaturePolicy,
    n_splits: int = 3,
    use_gpu: bool = True,
    metric: str = "roc_auc",   # "roc_auc" | "f1"
) -> optuna.trial.Trial:
    skf = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=42)

    # 先在「整體」上凍結欄位集，確保每折一致
    _X_all, _y_all = policy.transform_Xy(df)
    # 若設定了 freeze_feature_list_path，這裡會寫出 features.json
    if policy.freeze_feature_list_path:
        # 再 align 一次（雖然 _X_all 本身就是來源）
        _ = policy.align_like(_X_all)

    def objective(trial: optuna.trial.Trial) -> float:
        # ---- 取超參數 ----
        params = dict(
            n_estimators=trial.suggest_int("n_estimators", 200, 1200, step=100),
            max_depth=trial.suggest_int("max_depth", 3, 10),
            learning_rate=trial.suggest_float("learning_rate", 1e-3, 3e-1, log=True),
            subsample=trial.suggest_float("subsample", 0.6, 1.0),
            colsample_bytree=trial.suggest_float("colsample_bytree", 0.5, 1.0),
            reg_alpha=trial.suggest_float("reg_alpha", 0.0, 5.0),
            reg_lambda=trial.suggest_float("reg_lambda", 0.0, 10.0),
            min_child_weight=trial.suggest_float("min_child_weight", 1e-3, 10.0, log=True),
        )

        # XGB 版本相容：device / tree_method
        gpu_enabled = use_gpu and cp is not None
        if gpu_enabled:
            params.update({"tree_method": "gpu_hist", "device": "cuda"})
        else:
            params.update({"tree_method": "hist"})

        # 任務型態
        if policy.task_type == "binary":
            params.update({
                "objective": "binary:logistic",
                "eval_metric": "auc",
            })
        else:
            n_class = int(pd.Series(_y_all).nunique())
            params.update({
                "objective": "multi:softprob",
                "num_class": n_class,
                "eval_metric": "mlogloss",  # AUC 由外部 sklearn 計算
            })

        # ---- 交叉驗證 ----
        scores = []
        for tr_idx, va_idx in skf.split(_X_all, _y_all):
            df_tr = df.iloc[tr_idx].reset_index(drop=True)
            df_va = df.iloc[va_idx].reset_index(drop=True)

            X_tr, y_tr = policy.transform_Xy(df_tr)
            X_va, y_va = policy.transform_Xy(df_va)

            # 若有凍結欄位集 → 對齊
            X_tr = policy.align_like(X_tr)
            X_va = policy.align_like(X_va)

            if gpu_enabled:
                X_tr_arr = cp.asarray(X_tr.values)
                y_tr_arr = cp.asarray(y_tr)
                X_va_arr = cp.asarray(X_va.values)
                y_va_arr = cp.asarray(y_va)
            else:
                X_tr_arr = X_tr.values
                y_tr_arr = y_tr
                X_va_arr = X_va.values
                y_va_arr = y_va

            clf = XGBClassifier(**params, random_state=42)
            clf.fit(
                X_tr_arr,
                y_tr_arr,
                eval_set=[(X_va_arr, y_va_arr)],
                verbose=False,
            )

            # ---- 評分 ----
            if policy.task_type == "binary":
                pred = clf.predict_proba(X_va_arr)[:, 1]
                if gpu_enabled:
                    pred = cp.asnumpy(pred)
                    y_va_eval = cp.asnumpy(y_va_arr)
                else:
                    y_va_eval = y_va_arr
                if metric == "roc_auc":
                    sc = roc_auc_score(y_va_eval, pred)
                elif metric == "f1":
                    sc = f1_score(y_va_eval, (pred >= 0.5).astype(int))
                else:
                    raise ValueError(f"未知 metric: {metric}")
            else:
                pred = clf.predict_proba(X_va_arr)
                if gpu_enabled:
                    pred = cp.asnumpy(pred)
                    y_va_eval = cp.asnumpy(y_va_arr)
                else:
                    y_va_eval = y_va_arr
                if metric == "roc_auc":
                    sc = roc_auc_score(y_va_eval, pred, multi_class="ovr")
                elif metric == "f1":
                    sc = f1_score(y_va_eval, pred.argmax(axis=1), average="macro")
                else:
                    raise ValueError(f"未知 metric: {metric}")

            scores.append(sc)

        return float(np.mean(scores))

    return objective

# -------------------------
# CLI
# -------------------------
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", required=True, help="訓練資料 CSV 路徑（包含 target 欄位）")
    ap.add_argument("--target", required=True, help="目標欄位，例如 is_attack / crlevel")
    ap.add_argument("--task_type", default="binary", choices=["binary", "multiclass"])
    ap.add_argument("--drop_cols", default="", help="以逗號分隔的欄位名（會被強制剔除）")
    ap.add_argument("--whitelist", default="", help="以逗號分隔的欄位名（只允許這些特徵；留空為不限）")
    ap.add_argument("--features_json", default="", help="features.json 路徑；提供則凍結欄位順序")
    ap.add_argument("--splits", type=int, default=3, help="StratifiedKFold 次數")
    ap.add_argument("--metric", default="roc_auc", choices=["roc_auc", "f1"])
    ap.add_argument("--use_gpu", type=int, default=1, help="1=使用 GPU（若可用）")
    ap.add_argument("--trials", type=int, default=30, help="Optuna 試驗次數")
    ap.add_argument("--study_name", default="xgb_tuning", help="Optuna Study 名稱")
    args = ap.parse_args()

    df = load_dataset(args.csv)

    drop_cols = [c.strip() for c in args.drop_cols.split(",") if c.strip()]
    whitelist = [c.strip() for c in args.whitelist.split(",") if c.strip()]
    features_json = args.features_json.strip() or None

    policy = FeaturePolicy(
        target_col=args.target,
        task_type=args.task_type,
        numeric_only=True,                # <<== 與正式訓練一致：只用數值/布林
        drop_cols=drop_cols,
        feature_whitelist=whitelist or None,
        leak_like=["level"],              # <<== 預設排除可疑洩漏欄位
        cast_float32=True,
        fillna_value=0.0,
        freeze_feature_list_path=features_json,
    )

    objective = build_objective(
        df=df,
        policy=policy,
        n_splits=args.splits,
        use_gpu=bool(args.use_gpu),
        metric=args.metric,
    )

    study = optuna.create_study(direction="maximize", study_name=args.study_name)
    study.optimize(objective, n_trials=args.trials)

    print("\n===== Optuna 最佳結果 =====")
    print("Best Value:", study.best_value)
    print("Best Params:")
    for k, v in study.best_trial.params.items():
        print(f"  - {k}: {v}")

    # 若有凍結欄位，保存一份結果摘要
    if features_json:
        out = {
            "best_value": study.best_value,
            "best_params": study.best_trial.params,
            "features_json": features_json,
        }
        with open(os.path.splitext(features_json)[0] + "_optuna_best.json", "w", encoding="utf-8") as f:
            json.dump(out, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    main()
