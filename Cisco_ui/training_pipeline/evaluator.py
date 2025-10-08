"""Cisco Pipeline 結果評估工具。"""
from __future__ import annotations

from typing import Dict, Any
import pandas as pd
import numpy as np
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    classification_report,
    confusion_matrix
)


# 工具函式（保留原有功能）
def summarize_binary_results(result_csv: str) -> Dict[str, int]:
    """統計二元結果中的攻擊與正常數量。"""
    dataframe = pd.read_csv(result_csv)
    distribution = dataframe["is_attack"].value_counts().to_dict()
    return {
        "攻擊流量": int(distribution.get(1, 0)),
        "正常流量": int(distribution.get(0, 0)),
    }


def summarize_multiclass_results(result_csv: str) -> Dict[str, int]:
    """統計多元結果的 Severity 分佈。"""
    dataframe = pd.read_csv(result_csv)
    distribution = dataframe["Severity"].value_counts().to_dict()
    return {str(level): int(count) for level, count in distribution.items()}


class Evaluator:
    """Cisco ASA 模型評估器"""
    
    def __init__(self):
        """初始化評估器"""
        pass
    
    def evaluate(
        self,
        y_true: np.ndarray,
        y_pred: np.ndarray,
        task_type: str = "binary"
    ) -> Dict[str, Any]:
        """
        評估模型效能
        
        Args:
            y_true: 真實標籤
            y_pred: 預測標籤
            task_type: 任務類型 ("binary" 或 "multiclass")
            
        Returns:
            評估指標字典
        """
        results = {}
        
        # 準確率
        results["accuracy"] = float(accuracy_score(y_true, y_pred))
        
        # 精確率、召回率、F1
        if task_type == "binary":
            results["precision"] = float(
                precision_score(y_true, y_pred, zero_division=0)
            )
            results["recall"] = float(
                recall_score(y_true, y_pred, zero_division=0)
            )
            results["f1"] = float(
                f1_score(y_true, y_pred, zero_division=0)
            )
        else:
            results["precision"] = float(
                precision_score(
                    y_true, y_pred, average="weighted", zero_division=0
                )
            )
            results["recall"] = float(
                recall_score(
                    y_true, y_pred, average="weighted", zero_division=0
                )
            )
            results["f1"] = float(
                f1_score(
                    y_true, y_pred, average="weighted", zero_division=0
                )
            )
        
        # 分類報告
        results["classification_report"] = classification_report(
            y_true, y_pred, output_dict=True, zero_division=0
        )
        
        # 混淆矩陣
        results["confusion_matrix"] = confusion_matrix(
            y_true, y_pred
        ).tolist()
        
        return results
