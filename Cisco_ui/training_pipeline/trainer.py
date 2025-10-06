"""Cisco Pipeline 執行流程模組。"""
from __future__ import annotations

import os
from typing import Dict

# Import with robust fallback mechanism
import sys
import os

# 確保正確的模組路徑
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)  # Cisco_ui 目錄
root_dir = os.path.dirname(parent_dir)     # 專案根目錄

# 添加必要的路徑到 sys.path
for path in [parent_dir, root_dir]:
    if path not in sys.path:
        sys.path.insert(0, path)

# 嘗試各種 import 方式
EtlOutputs = None
run_etl_pipeline = None
run_models = None

try:
    # 優先嘗試絕對路徑
    from Cisco_ui.etl_pipeliner import EtlOutputs, run_etl_pipeline, run_models
except ImportError:
    try:
        # 嘗試相對路徑
        from ..etl_pipeliner import EtlOutputs, run_etl_pipeline, run_models  # type: ignore[no-redef]
    except ImportError:
        try:
            # 嘗試直接 import（當前目錄已在 sys.path 中）
            from etl_pipeliner import EtlOutputs, run_etl_pipeline, run_models  # type: ignore[no-redef]
        except ImportError:
            # 最後備案：動態載入
            import importlib.util
            etl_pipeliner_path = os.path.join(parent_dir, 'etl_pipeliner.py')
            if os.path.exists(etl_pipeliner_path):
                spec = importlib.util.spec_from_file_location("etl_pipeliner", etl_pipeliner_path)
                etl_pipeliner = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(etl_pipeliner)
                EtlOutputs = etl_pipeliner.EtlOutputs
                run_etl_pipeline = etl_pipeliner.run_etl_pipeline
                run_models = etl_pipeliner.run_models
            else:
                raise RuntimeError(f"找不到 etl_pipeliner.py 檔案。預期路徑: {etl_pipeliner_path}")

from .config import PipelineConfig


def _append_all_results(etl_outputs: EtlOutputs, df_binary, output_dir: str) -> str:
    """將本批結果追加到 all_results.csv。"""
    if df_binary is None:
        raise ValueError("模型推論結果為 None，請檢查模型與輸入資料格式是否正確。")
    all_results_path = os.path.join(output_dir, "all_results.csv")
    write_header = not os.path.exists(all_results_path)
    dataframe = df_binary.copy()
    dataframe["batch_id"] = etl_outputs.batch_id
    with open(all_results_path, "a", newline="", encoding="utf-8") as handle:
        dataframe.to_csv(handle, header=write_header, index=False)
    return all_results_path


def execute_pipeline(config: PipelineConfig) -> Dict[str, object]:
    """依據設定執行完整的 Cisco Pipeline。"""
    print(f"DEBUG: run_etl_pipeline = {run_etl_pipeline}")
    print(f"DEBUG: run_models = {run_models}")
    print(f"DEBUG: config paths - log: {config.raw_log_path}, binary: {config.binary_model_path}, multi: {config.multiclass_model_path}")
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
    if df_binary is None:
        # 直接回傳 result_dict，讓 UI 能顯示 debug 訊息
        return result_dict
    all_results = _append_all_results(etl_outputs, df_binary, config.output_dir)
    result_dict["all_results_csv"] = all_results
    return result_dict
