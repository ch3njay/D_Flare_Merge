# training_pipeline/evaluator.py
from __future__ import annotations

from typing import Any, Dict, Optional
import numpy as np
import warnings

from sklearn.metrics import (
    accuracy_score,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
    classification_report,
    confusion_matrix,
)
try:
    from sklearn.exceptions import UndefinedMetricWarning
except Exception:
    UndefinedMetricWarning = Warning  # 兼容舊版

class Evaluator:
    """
    保留原輸出風格：
    ✅ 測試集準確率：
    📈 OVR-AUC：
    📋 分類報告：
    📝 混淆矩陣：
    新增：統一 zero_division=0 並靜音 UndefinedMetricWarning（例如少數類別完全無預測時）
    """

    def __init__(self, task: str = "binary") -> None:
        self.task = task

    def evaluate(self, model: Any, X, y_true, name: Optional[str] = None) -> Dict[str, Any]:
        if name:
            print(f"\n==================== [ {name} 評估結果 ] ====================")

        X_eval = X.to_numpy() if hasattr(X, "to_numpy") else np.asarray(X)
        y_true_np = y_true.to_numpy().reshape(-1) if hasattr(y_true, "to_numpy") else np.asarray(y_true).reshape(-1)

        # 預測
        y_pred = model.predict(X_eval)

        # ====== 分類報告與基本指標（靜音 UndefinedMetricWarning） ======
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", category=UndefinedMetricWarning)
            acc = accuracy_score(y_true_np, y_pred)
            if self.task == "binary":
                f1 = f1_score(y_true_np, y_pred, average="binary", zero_division=0)
                prec = precision_score(y_true_np, y_pred, average="binary", zero_division=0)
                rec = recall_score(y_true_np, y_pred, average="binary", zero_division=0)
                report = classification_report(y_true_np, y_pred, digits=4, zero_division=0)
            else:
                f1 = f1_score(y_true_np, y_pred, average="macro", zero_division=0)
                prec = precision_score(y_true_np, y_pred, average="macro", zero_division=0)
                rec = recall_score(y_true_np, y_pred, average="macro", zero_division=0)
                report = classification_report(y_true_np, y_pred, digits=4, zero_division=0)

        # ====== AUC（binary / multiclass OVR） ======
        auc = np.nan
        try:
            if hasattr(model, "predict_proba"):
                proba = model.predict_proba(X_eval)
                if self.task == "binary":
                    # 取正類索引為 1；若 classes_ 不含 1，用最後一類
                    pos_idx = 1
                    if hasattr(model, "classes_"):
                        cls = list(model.classes_)
                        pos_idx = cls.index(1) if 1 in cls else (len(cls) - 1)
                    auc = roc_auc_score(y_true_np, proba[:, pos_idx])
                else:
                    auc = roc_auc_score(y_true_np, proba, multi_class="ovr")
        except Exception:
            pass  # 保留 auc=nan

        # ====== 輸出 ======
        print(f"✅ 測試集準確率： {acc:.6f}")
        if self.task == "binary":
            print(f"📈 AUC： {auc if np.isnan(auc) else f'{auc:.6f}'}")
        else:
            print(f"📈 OVR-AUC： {auc if np.isnan(auc) else f'{auc:.6f}'}")
        print("📋 分類報告：")
        print(report)

        cm = confusion_matrix(y_true_np, y_pred)
        print("📝 混淆矩陣：")
        print(cm)

        # 額外：列出每一類被預測的數量（幫助觀察「完全沒預測到某類」的狀況）
        try:
            unique, counts = np.unique(y_pred, return_counts=True)
            dist = dict(zip(unique.tolist(), counts.tolist()))
            print(f"📦 預測類別分佈：{dist}")
        except Exception:
            pass

        return {
            "acc": acc,
            "auc": auc,
            "f1": f1,
            "precision": prec,
            "recall": rec,
            "report": report,
            "confusion_matrix": cm,
        }
