"""Cisco GPU ETL Pipeline 主控模組（暫以 CPU 流程代替）。"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Tuple

import pandas as pd

from .etl_pipeliner import EtlOutputs
from .gpu_etl_pipeline import feature_engineering as gpu_feature
from .gpu_etl_pipeline.utils import is_gpu_available


@dataclass(slots=True)
class GpuPipelineResult:
    """封裝 GPU Pipeline 的結果。"""

    available: bool
    detail: Dict[str, object]


def run_gpu_pipeline(
    etl_outputs: EtlOutputs, binary_model_path: str, multiclass_model_path: str
) -> Tuple[GpuPipelineResult, pd.DataFrame]:
    """若 GPU 可用則執行，否則回傳降級訊息。"""
    if not is_gpu_available():
        return GpuPipelineResult(available=False, detail={"message": "目前環境無 GPU，改用 CPU 流程"}), pd.DataFrame()

    binary_result, df_binary = gpu_feature.dflare_binary_predict(
        input_csv=etl_outputs.step2_csv,
        binary_model_path=binary_model_path,
        output_csv="gpu_binary.csv",
        output_pie="gpu_binary_pie.png",
        output_bar="gpu_binary_bar.png",
    )
    attack_df = df_binary[df_binary["is_attack"] == 1].copy()
    if attack_df.empty:
        return GpuPipelineResult(available=True, detail=binary_result), df_binary

    multi_result = gpu_feature.dflare_multiclass_predict(
        df_attack=attack_df,
        multiclass_model_path=multiclass_model_path,
        output_csv="gpu_multi.csv",
        output_pie="gpu_multi_pie.png",
        output_bar="gpu_multi_bar.png",
    )
    return GpuPipelineResult(
        available=True,
        detail={"binary": binary_result, "multiclass": multi_result},
    ), df_binary
