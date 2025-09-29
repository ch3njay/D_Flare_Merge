# training_pipeline/data_loader.py
import numpy as np
import pandas as pd
from typing import Dict, Tuple


class DataLoader:
    def __init__(self, config: dict):
        self.config = config

    def load_data(self, file_path: str) -> pd.DataFrame:
        df = pd.read_csv(file_path)
        # 第一次訊息：原始載入
        print(f"✅ 原始資料載入完成：{df.shape[0]} 筆，欄位 {df.shape[1]}")
        return df

    # === 新增：帶報告版本（不破壞舊介面） ===
    @staticmethod
    def prepare_xy_with_report(df: pd.DataFrame, config: dict, task: str) -> Tuple[pd.DataFrame, pd.Series, Dict]:
        """
        與舊版一致的邏輯，但額外回傳 report：
        - dropped_by_dropcols
        - dropped_by_type
        - dropped_constant
        - initial_count, final_count, final_cols
        """
        target_col = config["TARGET_COLUMN"]
        drop_cols = set(config.get("DROP_COLUMNS", []))
        if target_col not in df.columns:
            raise KeyError(f"找不到目標欄位 {target_col}")

        report: Dict = {}
        init_cols = list(df.columns)
        report["initial_count"] = len(init_cols)
        report["initial_cols"] = init_cols

        y = df[target_col]
        # 1) 丟掉 DROP_COLUMNS
        X1 = df.drop(columns=list(drop_cols & set(df.columns)), errors="ignore")
        report["dropped_by_dropcols"] = sorted(list(set(init_cols) - set(X1.columns) - {target_col}))
        report["after_drop_cols"] = list(X1.columns)

        # 2) 僅保留 numeric/bool
        keep_cols = []
        for c in X1.columns:
            if c == target_col:
                continue
            dt = X1[c].dtype
            if pd.api.types.is_bool_dtype(dt) or pd.api.types.is_numeric_dtype(dt):
                keep_cols.append(c)
        X2 = X1[keep_cols].copy()
        report["dropped_by_type"] = sorted(list(set(X1.columns) - set(X2.columns)))
        report["after_type_filter"] = list(X2.columns)

        # 3) 補值 + 型別統一
        for c in X2.columns:
            if pd.api.types.is_bool_dtype(X2[c].dtype):
                X2[c] = X2[c].fillna(False).astype(np.int8, copy=False)
            else:
                X2[c] = X2[c].fillna(0).astype(np.float32, copy=False)

        # 4) 去常數欄（含全 NaN/單一值）
        nunique = X2.nunique(dropna=False)
        const_cols = nunique[nunique <= 1].index.tolist()
        X3 = X2.drop(columns=const_cols, errors="ignore")
        report["dropped_constant"] = const_cols

        report["final_cols"] = list(X3.columns)
        report["final_count"] = int(X3.shape[1])

        # 第二次訊息：特徵篩選摘要
        print(f"✅ 特徵篩選完成：由 {report['initial_count']} → {report['final_count']} 欄")
        print(f"• 由 DROP_COLUMNS 移除：{report['dropped_by_dropcols'] or '無'}")
        print(f"• 非數值/布林被過濾：{report['dropped_by_type'] or '無'}")
        print(f"• 常數/全空欄移除：{report['dropped_constant'] or '無'}")

        return X3, y, report

    # === 舊介面（維持不破壞） ===
    @staticmethod
    def prepare_xy(df: pd.DataFrame, config: dict, task: str):
        X, y, _ = DataLoader.prepare_xy_with_report(df, config, task)
        return X, y
