"""GPU 版欄位映射預留模組。"""
from __future__ import annotations

from ..etl_pipeline import log_mapping


def step2_preprocess_data(*args, **kwargs):
    """目前回退至 CPU 實作，保留介面一致。"""
    return log_mapping.step2_preprocess_data(*args, **kwargs)
