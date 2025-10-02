"""Cisco Pipeline 執行流程模組。"""
from __future__ import annotations

import os
from typing import Dict

from ..etl_pipeliner import EtlOutputs, run_etl_pipeline, run_models
from .config import PipelineConfig


def _append_all_results(etl_outputs: EtlOutputs, df_binary, output_dir: str) -> str:
    """將本批結果追加到 all_results.csv。"""
    all_results_path = os.path.join(output_dir, "all_results.csv")
    write_header = not os.path.exists(all_results_path)
    dataframe = df_binary.copy()
    dataframe["batch_id"] = etl_outputs.batch_id
    with open(all_results_path, "a", newline="", encoding="utf-8") as handle:
        dataframe.to_csv(handle, header=write_header, index=False)
    return all_results_path


def execute_pipeline(config: PipelineConfig) -> Dict[str, object]:
    """依據設定執行完整的 Cisco Pipeline。"""
    etl_outputs = run_etl_pipeline(
        raw_log_path=config.raw_log_path,
        output_dir=config.output_dir,
        show_progress=config.show_progress,
    )
    result_dict, df_binary = run_models(
        etl_outputs=etl_outputs,
        binary_model_path=config.binary_model_path,
        multiclass_model_path=config.multiclass_model_path,
        output_dir=config.output_dir,
        bin_feat_cols=config.bin_feat_cols,
        multi_feat_cols=config.multi_feat_cols,
    )
    all_results = _append_all_results(etl_outputs, df_binary, config.output_dir)
    result_dict["all_results_csv"] = all_results
    return result_dict
