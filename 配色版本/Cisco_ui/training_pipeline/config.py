"""Cisco Pipeline 設定資料類型。"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional


@dataclass(slots=True)
class PipelineConfig:
    """描述完整 Pipeline 所需的參數。"""

    raw_log_path: str
    binary_model_path: str
    multiclass_model_path: str
    output_dir: str
    bin_feat_cols: Optional[List[str]] = None
    multi_feat_cols: Optional[List[str]] = None
    show_progress: bool = True
