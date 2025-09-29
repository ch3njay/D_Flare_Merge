"""Cisco Pipeline 特徵欄位建構工具。"""
from __future__ import annotations

import json
from typing import List

import pandas as pd


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
    dataframe = pd.read_csv(sample_csv, nrows=1)
    return [column for column in dataframe.columns if column not in {"is_attack", "Severity"}]
