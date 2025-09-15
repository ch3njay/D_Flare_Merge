# training_pipeline/feature_policy.py
from __future__ import annotations
import json, os
from typing import Iterable, Optional, Tuple, List, Dict
import numpy as np
import pandas as pd


class FeaturePolicy:
    """
    統一訓練/搜尋的特徵過濾規則：
    - 僅保留數值/布林欄位 (numeric_only=True)
    - 排除 drop_cols 與疑似洩漏欄位（名稱包含 leak_like 片段）
    - 去除常數特徵
    - 缺失填補
    - 支援凍結欄位集（features.json），確保 Optuna 與正式訓練一致
    - 新增：transform_Xy_with_report()，回傳欄位過濾報告
    """
    def __init__(
        self,
        target_col: str,
        task_type: str = "binary",
        numeric_only: bool = True,
        drop_cols: Optional[Iterable[str]] = None,
        feature_whitelist: Optional[Iterable[str]] = None,
        leak_like: Optional[Iterable[str]] = None,
        cast_float32: bool = True,
        fillna_value: float = 0.0,
        freeze_feature_list_path: Optional[str] = None,
    ):
        self.target_col = target_col
        self.task_type = task_type
        self.numeric_only = bool(numeric_only)
        self.drop_cols = set(drop_cols or [])
        self.feature_whitelist = set(feature_whitelist) if feature_whitelist else None
        self.leak_like = [str(x).lower() for x in (leak_like or [])]
        self.cast_float32 = bool(cast_float32)
        self.fillna_value = fillna_value
        self.freeze_feature_list_path = freeze_feature_list_path

    # --- utils ---
    def _filter_cols(self, df: pd.DataFrame) -> List[str]:
        cols = [c for c in df.columns if c != self.target_col and c not in self.drop_cols]
        if self.leak_like:
            lks = self.leak_like
            cols = [c for c in cols if not any(lk in c.lower() for lk in lks)]
        if self.feature_whitelist:
            cols = [c for c in cols if c in self.feature_whitelist]
        return cols

    def _to_numeric_bool(self, X: pd.DataFrame) -> pd.DataFrame:
        if not self.numeric_only:
            return X
        Xn = X.select_dtypes(include=["number", "bool"]).copy()
        for c in Xn.columns:
            if Xn[c].dtype == bool:
                Xn[c] = Xn[c].astype(np.int8)
        if self.cast_float32:
            for c in Xn.columns:
                if np.issubdtype(Xn[c].dtype, np.floating):
                    Xn[c] = Xn[c].astype(np.float32)
        return Xn

    # --- public ---
    def transform_Xy(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.Series]:
        X, y, _ = self.transform_Xy_with_report(df)
        return X, y

    def transform_Xy_with_report(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.Series, Dict]:
        report: Dict[str, List[str] | int] = {}
        target_col = self.target_col

        init_cols = list(df.columns)
        report["initial_cols"] = init_cols
        report["initial_count"] = len(init_cols)

        # 1) 基於名稱的過濾（drop_cols / leak_like / whitelist）
        cols = self._filter_cols(df)
        X = df[cols].copy()
        y = df[target_col].copy() if target_col in df.columns else pd.Series([], dtype=np.int64)

        dropped_by_name = sorted(list(set(init_cols) - set([*X.columns, target_col])))
        report["after_name_filter"] = list(X.columns)
        report["dropped_by_name_filter"] = dropped_by_name

        # 2) 僅保留 numeric/bool
        X2 = self._to_numeric_bool(X)
        dropped_by_type = sorted(list(set(X.columns) - set(X2.columns)))
        report["after_type_filter"] = list(X2.columns)
        report["dropped_by_type"] = dropped_by_type

        # 3) 去常數欄
        nunique = X2.nunique(dropna=False)
        const_cols = nunique[nunique <= 1].index.tolist()
        X3 = X2.drop(columns=const_cols, errors="ignore")
        report["dropped_constant"] = const_cols

        # 4) 缺失補值
        X3 = X3.fillna(self.fillna_value)

        report["final_cols"] = list(X3.columns)
        report["final_count"] = int(X3.shape[1])

        return X3, y, report

    def align_like(self, X: pd.DataFrame) -> pd.DataFrame:
        path = self.freeze_feature_list_path
        if not path:
            return X

        if not os.path.exists(path):
            os.makedirs(os.path.dirname(path), exist_ok=True) if os.path.dirname(path) else None
            with open(path, "w", encoding="utf-8") as f:
                json.dump(list(X.columns), f, ensure_ascii=False, indent=2)
            return X

        with open(path, "r", encoding="utf-8") as f:
            cols = json.load(f)
        X_aligned = X.reindex(columns=cols, fill_value=0)
        return X_aligned
