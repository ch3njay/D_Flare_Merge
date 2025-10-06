"""Cisco ETL Pipeline 統籌模組。"""
from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Dict, Tuple

import pandas as pd

from .etl_pipeline import feature_engineering, log_cleaning, log_mapping
from .etl_pipeline.utils import get_next_batch_id


@dataclass(slots=True)
class EtlOutputs:
    """封裝 ETL 步驟的所有輸出路徑與統計資訊。"""

    batch_id: int
    processed_count: int
    step1_csv: str
    step2_csv: str
    unique_json: str


def run_etl_pipeline(
    raw_log_path: str,
    output_dir: str,
    show_progress: bool = True,
) -> EtlOutputs:
    """執行兩階段 ETL 並回傳輸出資訊。"""
    os.makedirs(output_dir, exist_ok=True)

    unique_json = os.path.join(output_dir, "log_unique_values.json")
    step1_out = os.path.join(output_dir, "processed_logs.csv")
    step2_out = os.path.join(output_dir, "preprocessed_data.csv")
    all_results_path = os.path.join(output_dir, "all_results.csv")
    batch_id = get_next_batch_id(all_results_path)

    processed_count, _ = log_cleaning.step1_process_logs(
        raw_log_path=raw_log_path,
        step1_out_path=step1_out,
        unique_out_json=unique_json,
        batch_id=batch_id,
        show_progress=show_progress,
    )
    log_mapping.step2_preprocess_data(
        step1_out_path=step1_out,
        step2_out_path=step2_out,
        unique_json=unique_json,
        show_progress=show_progress,
    )
    return EtlOutputs(
        batch_id=batch_id,
        processed_count=processed_count,
        step1_csv=step1_out,
        step2_csv=step2_out,
        unique_json=unique_json,
    )


def run_models(
    etl_outputs: EtlOutputs,
    binary_model_path: str,
    multiclass_model_path: str,
    output_dir: str,
    bin_feat_cols: list[str] | None = None,
    multi_feat_cols: list[str] | None = None,
) -> Tuple[Dict[str, object], pd.DataFrame]:
    """套用二元與多元模型並整理輸出資訊。"""
    os.makedirs(output_dir, exist_ok=True)
    binary_csv = os.path.join(output_dir, "binary_result.csv")
    binary_pie = os.path.join(output_dir, "binary_pie.png")
    binary_bar = os.path.join(output_dir, "binary_bar.png")
    multi_csv = os.path.join(output_dir, "multiclass_result.csv")
    multi_pie = os.path.join(output_dir, "multiclass_pie.png")
    multi_bar = os.path.join(output_dir, "multiclass_bar.png")

    import traceback
    try:
        binary_result, df_binary = feature_engineering.dflare_binary_predict(
            input_csv=etl_outputs.step2_csv,
            binary_model_path=binary_model_path,
            output_csv=binary_csv,
            output_pie=binary_pie,
            output_bar=binary_bar,
            feat_cols=bin_feat_cols,
        )
        attack_df = df_binary[df_binary["is_attack"] == 1].copy()
        if attack_df.empty:
            return (
                {
                    "batch_id": etl_outputs.batch_id,
                    "binary": binary_result,
                    "multiclass": None,
                    "binary_output_csv": binary_csv,
                    "binary_output_pie": binary_pie,
                    "binary_output_bar": binary_bar,
                    "multiclass_output_csv": None,
                    "multiclass_output_pie": None,
                    "multiclass_output_bar": None,
                    "debug": "No attack samples found. df_binary shape: {} columns: {}".format(df_binary.shape, list(df_binary.columns)),
                },
                df_binary,
            )
        multi_result = feature_engineering.dflare_multiclass_predict(
            df_attack=attack_df,
            multiclass_model_path=multiclass_model_path,
            output_csv=multi_csv,
            output_pie=multi_pie,
            output_bar=multi_bar,
            feat_cols=multi_feat_cols,
        )
        return (
            {
                "batch_id": etl_outputs.batch_id,
                "binary": binary_result,
                "multiclass": multi_result,
                "binary_output_csv": binary_csv,
                "binary_output_pie": binary_pie,
                "binary_output_bar": binary_bar,
                "multiclass_output_csv": multi_csv,
                "multiclass_output_pie": multi_pie,
                "multiclass_output_bar": multi_bar,
                "debug": "Success. df_binary shape: {} columns: {} attack_df shape: {}".format(df_binary.shape, list(df_binary.columns), attack_df.shape),
            },
            df_binary,
        )
    except Exception as exc:
        tb = traceback.format_exc()
        return (
            {
                "batch_id": getattr(etl_outputs, 'batch_id', None),
                "binary": None,
                "multiclass": None,
                "binary_output_csv": binary_csv,
                "binary_output_pie": binary_pie,
                "binary_output_bar": binary_bar,
                "multiclass_output_csv": multi_csv,
                "multiclass_output_pie": multi_pie,
                "multiclass_output_bar": multi_bar,
                "debug": f"Exception: {exc}\nTraceback:\n{tb}",
            },
            None,
        )
