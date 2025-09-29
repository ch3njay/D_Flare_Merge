"""Cisco ETL Pipeline 共用工具模組。"""
from __future__ import annotations

import os
from typing import Dict, Iterable

import chardet
import pandas as pd


STANDARD_COLUMNS = [
    "batch_id",
    "Datetime",
    "SyslogID",
    "Severity",
    "SourceIP",
    "SourcePort",
    "DestinationIP",
    "DestinationPort",
    "Duration",
    "Bytes",
    "Protocol",
    "Action",
    "Description",
    "raw_log",
]


def detect_encoding(file_path: str) -> str:
    """偵測輸入檔案的編碼，確保後續能正確讀取。"""
    with open(file_path, "rb") as handle:
        guess = chardet.detect(handle.read(10000)).get("encoding", "utf-8")
    return guess or "utf-8"


def get_next_batch_id(all_results_path: str) -> int:
    """根據歷史輸出檔決定新的 batch_id。"""
    if not os.path.exists(all_results_path):
        return 1
    try:
        dataframe = pd.read_csv(all_results_path)
        if "batch_id" in dataframe.columns and not dataframe.empty:
            return int(dataframe["batch_id"].max()) + 1
    except Exception:
        # 讀檔失敗時回傳預設值，避免流程被中止。
        pass
    return 1


def iter_unique_columns(columns: Iterable[str]) -> Dict[str, set]:
    """建立用來收集唯一值的字典結構。"""
    return {column: set() for column in columns}
