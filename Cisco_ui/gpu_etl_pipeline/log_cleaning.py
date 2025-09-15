"""GPU 版 Log 清洗預留模組。"""
from __future__ import annotations

from ..etl_pipeline import log_cleaning


def step1_process_logs(*args, **kwargs):
    """目前回退至 CPU 實作，保留介面一致。"""
    return log_cleaning.step1_process_logs(*args, **kwargs)
