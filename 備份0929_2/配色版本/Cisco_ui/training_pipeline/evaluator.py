"""Cisco Pipeline 結果評估工具。"""
from __future__ import annotations

from typing import Dict

import pandas as pd


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
