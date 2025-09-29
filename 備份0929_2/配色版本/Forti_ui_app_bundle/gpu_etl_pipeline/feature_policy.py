# training_pipeline/feature_policy.py
from __future__ import annotations
import json
import warnings
from dataclasses import dataclass, field
from typing import List, Optional, Tuple, Dict
import numpy as np
import pandas as pd

@dataclass
class FeaturePolicy:
    # ----- 必要設定 -----
    target_col: str                    # 例：'is_attack' 或 'crlevel'
    task_type: str = "binary"          # "binary" | "multiclass"
    # ----- 欄位策略 -----
    numeric_only: bool = True          # True => 只保留數值/布林欄位
    drop_cols: List[str] = field(default_factory=list)     # 強制剔除欄位
    feature_whitelist: Optional[List[str]] = None          # 只允許的欄位名清單（可為 None）
    leak_like: List[str] = field(default_factory=lambda: ["level"])  # 疑似洩漏欄位
    # ----- dtype 與 NaN 策略 -----
    cast_float32: bool = True
    fillna_value: float = 0.0
    # ----- 特徵對齊（可選）-----
    freeze_feature_list_path: Optional[str] = None  # "features.json" 用於持久化欄位集
    _frozen_features: Optional[List[str]] = None    # 內部：載入/記憶固定欄位順序

    def _infer_feature_names(self, df: pd.DataFrame) -> List[str]:
        """依設定取得候選特徵欄位"""
        cols = [c for c in df.columns if c != self.target_col and c not in self.drop_cols]
        # 移除疑似洩漏欄位
        cols = [c for c in cols if c not in self.leak_like]

        if self.feature_whitelist is not None:
            wl = set(self.feature_whitelist)
            cols = [c for c in cols if c in wl]

        if self.numeric_only:
            # 僅保留數值或布林欄位
            num_cols = df.select_dtypes(include=["number", "bool"]).columns.tolist()
            cols = [c for c in cols if c in num_cols]
        else:
            # 警告：若仍有 object 欄位，提醒使用者
            obj_cols = df.select_dtypes(include=["object"]).columns.tolist()
            bad = [c for c in cols if c in obj_cols]
            if bad:
                warnings.warn(
                    f"[FeaturePolicy] 偵測到 object 欄位：{bad}。"
                    f" 若使用 XGBoost 請改設 numeric_only=True 或先行編碼。",
                    UserWarning
                )
        return cols

    def _freeze_or_apply(self, cols: List[str]) -> List[str]:
        """如設定 features.json，則優先載入；否則以當前 cols 冷凍後存檔。"""
        if self.freeze_feature_list_path:
            if self._frozen_features is None:
                try:
                    with open(self.freeze_feature_list_path, "r", encoding="utf-8") as f:
                        self._frozen_features = json.load(f)
                except FileNotFoundError:
                    # 第一次建立
                    with open(self.freeze_feature_list_path, "w", encoding="utf-8") as f:
                        json.dump(cols, f, ensure_ascii=False, indent=2)
                    self._frozen_features = cols
            # 對齊既有的欄位順序（忽略新生或缺失）
            cols = [c for c in self._frozen_features if c in cols]
        return cols

    def transform_Xy(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, np.ndarray]:
        """將 df → (X, y)，套用同一份策略"""
        if self.target_col not in df.columns:
            raise ValueError(f"[FeaturePolicy] 找不到 target_col='{self.target_col}' 於 DataFrame.")

        y = df[self.target_col].copy()

        # 轉換 y dtype for sklearn/xgboost
        if self.task_type == "binary":
            # 保險起見：轉 int
            y = y.astype(int).to_numpy()
        else:
            # 多類：保留原 label，但 roc_auc 評分時會以 sklearn 處理
            y = y.to_numpy()

        cols = self._infer_feature_names(df)
        cols = self._freeze_or_apply(cols)

        X = df[cols].copy()

        # 填補 NaN
        if self.fillna_value is not None:
            X = X.fillna(self.fillna_value)

        # dtype 安全
        if self.cast_float32:
            for c in X.columns:
                if pd.api.types.is_bool_dtype(X[c]):
                    X[c] = X[c].astype(np.uint8)
                elif not pd.api.types.is_float_dtype(X[c]) and not pd.api.types.is_integer_dtype(X[c]):
                    # 若仍非數值，強制轉 float32（避免 XGB 當掉）
                    X[c] = pd.to_numeric(X[c], errors="coerce").fillna(self.fillna_value)
                X[c] = X[c].astype(np.float32)

        # 最終檢查：不得有 object
        bad_obj = X.select_dtypes(include=["object"]).columns.tolist()
        if bad_obj:
            raise TypeError(f"[FeaturePolicy] X 仍包含 object 欄位：{bad_obj}")

        return X, y

    def align_like(self, X: pd.DataFrame) -> pd.DataFrame:
        """依 frozen features.json 對齊欄位，補缺列為 0，保證推論/驗證一致。"""
        if not self.freeze_feature_list_path:
            return X
        if self._frozen_features is None:
            with open(self.freeze_feature_list_path, "r", encoding="utf-8") as f:
                self._frozen_features = json.load(f)
        # 只保留凍結欄位，缺少的補 0
        X = X.reindex(columns=self._frozen_features, fill_value=0.0)
        # dtype 保持 float32
        return X.astype(np.float32)
