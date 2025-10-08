"""Cisco Pipeline 模型建構工具。"""
from __future__ import annotations

import json
from typing import List, Any
import warnings

import pandas as pd
import numpy as np
from xgboost import XGBClassifier
from lightgbm import LGBMClassifier
from catboost import CatBoostClassifier


# 工具函式（保留原有功能）
def load_feature_names(config_path: str) -> List[str]:
    """從 JSON 設定檔載入特徵欄位名稱。"""
    with open(config_path, "r", encoding="utf-8") as handle:
        data = json.load(handle)
    features = data.get("feature_names", [])
    if not isinstance(features, list):
        raise ValueError("feature_names 必須為列表格式")
    return [str(name) for name in features]


def infer_features_from_dataframe(sample_csv: str) -> List[str]:
    """根據示例 CSV 自動推斷可用特徵欄位。"""
    try:
        dataframe = pd.read_csv(sample_csv, nrows=1)
    except pd.errors.ParserError:
        # 如果有格式問題，使用容錯模式
        try:
            dataframe = pd.read_csv(
                sample_csv, 
                nrows=1,
                error_bad_lines=False,
                warn_bad_lines=False,
                on_bad_lines='skip'
            )
        except Exception:
            # 最後嘗試用 Python 引擎
            dataframe = pd.read_csv(
                sample_csv,
                nrows=1,
                sep=None,
                engine='python',
                quoting=3
            )
    
    return [
        column for column in dataframe.columns 
        if column not in {"is_attack", "Severity", "crlevel"}
    ]


class ModelBuilder:
    """Cisco ASA 模型建構器"""
    
    def __init__(self):
        """初始化模型建構器"""
        # 抑制警告訊息
        warnings.filterwarnings("ignore", category=UserWarning)
        warnings.filterwarnings("ignore", category=FutureWarning)
        
    def build_lightgbm(
        self, 
        X: pd.DataFrame, 
        y: pd.Series,
        task_type: str = "binary"
    ) -> Any:
        """
        建立 LightGBM 模型
        
        Args:
            X: 特徵資料
            y: 標籤資料
            task_type: 任務類型 ("binary" 或 "multiclass")
            
        Returns:
            訓練好的 LightGBM 模型
        """
        params = {
            "n_estimators": 100,
            "learning_rate": 0.1,
            "max_depth": 7,
            "num_leaves": 31,
            "random_state": 42,
            "verbose": -1
        }
        
        if task_type == "multiclass":
            num_classes = len(np.unique(y))
            params["objective"] = "multiclass"
            params["num_class"] = num_classes
        else:
            params["objective"] = "binary"
        
        model = LGBMClassifier(**params)
        model.fit(X, y)
        return model
    
    def build_xgboost(
        self,
        X: pd.DataFrame,
        y: pd.Series,
        task_type: str = "binary"
    ) -> Any:
        """
        建立 XGBoost 模型
        
        Args:
            X: 特徵資料
            y: 標籤資料
            task_type: 任務類型 ("binary" 或 "multiclass")
            
        Returns:
            訓練好的 XGBoost 模型
        """
        params = {
            "n_estimators": 100,
            "learning_rate": 0.1,
            "max_depth": 7,
            "random_state": 42,
            "verbosity": 0
        }
        
        if task_type == "multiclass":
            num_classes = len(np.unique(y))
            params["objective"] = "multi:softmax"
            params["num_class"] = num_classes
        else:
            params["objective"] = "binary:logistic"
        
        model = XGBClassifier(**params)
        model.fit(X, y)
        return model
    
    def build_catboost(
        self,
        X: pd.DataFrame,
        y: pd.Series,
        task_type: str = "binary"
    ) -> Any:
        """
        建立 CatBoost 模型
        
        Args:
            X: 特徵資料
            y: 標籤資料
            task_type: 任務類型 ("binary" 或 "multiclass")
            
        Returns:
            訓練好的 CatBoost 模型
        """
        params = {
            "iterations": 100,
            "learning_rate": 0.1,
            "depth": 7,
            "random_state": 42,
            "verbose": False,
            "allow_writing_files": False
        }
        
        if task_type == "multiclass":
            num_classes = len(np.unique(y))
            params["loss_function"] = "MultiClass"
            params["classes_count"] = num_classes
        else:
            params["loss_function"] = "Logloss"
        
        model = CatBoostClassifier(**params)
        model.fit(X, y, verbose=False)
        return model
