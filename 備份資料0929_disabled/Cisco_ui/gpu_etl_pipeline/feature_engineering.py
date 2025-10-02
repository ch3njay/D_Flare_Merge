"""GPU 版模型推論預留模組。"""
from __future__ import annotations

from ..etl_pipeline import feature_engineering


def dflare_binary_predict(*args, **kwargs):
    """目前回退至 CPU 模型，保留函式接口。"""
    return feature_engineering.dflare_binary_predict(*args, **kwargs)


def dflare_multiclass_predict(*args, **kwargs):
    """目前回退至 CPU 模型，保留函式接口。"""
    return feature_engineering.dflare_multiclass_predict(*args, **kwargs)
