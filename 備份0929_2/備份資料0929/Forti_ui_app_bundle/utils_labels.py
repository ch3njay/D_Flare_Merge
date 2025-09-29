import json
import os
import numpy as np
import pandas as pd

CRLEVEL_MAP = {
    "unknown": 0,
    "low": 1,
    "medium": 2,
    "high": 3,
    "critical": 4,
}
INV_CRLEVEL_MAP = {v: k for k, v in CRLEVEL_MAP.items()}

def encode_crlevel_series(y: pd.Series) -> pd.Series:
    """將字串 crlevel 統一映射為 0..4，回傳 int32 Series。"""
    if y.dtype == object:
        y2 = y.str.lower().map(CRLEVEL_MAP)
        if y2.isna().any():
            bad = sorted(y[y2.isna()].unique().tolist())
            raise ValueError(f"[crlevel 編碼] 出現未知標籤：{bad}")
        return y2.astype("int32")
    return y.astype("int32")

def save_label_mapping(out_dir: str):
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, "label_mapping.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump({"crlevel_map": CRLEVEL_MAP}, f, ensure_ascii=False, indent=2)
    return path
