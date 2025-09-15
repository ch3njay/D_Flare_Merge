"""Cisco ASA Log 欄位映射與預處理。"""
from __future__ import annotations

import json
import os
from typing import Dict

import pandas as pd
from tqdm import tqdm

from .utils import STANDARD_COLUMNS

CATEGORICAL_MAPPINGS: Dict[str, Dict[str, int]] = {
    "Protocol": {
        "http": 1,
        "https": 2,
        "icmp": 3,
        "tcp": 4,
        "udp": 5,
        "scan": 6,
        "flood": 7,
        "other": 8,
        "unknown": 0,
        "nan": -1,
    },
    "Action": {
        "built": 1,
        "teardown": 2,
        "deny": 3,
        "drop": 4,
        "login": 5,
        "other": 6,
        "unknown": 0,
        "nan": -1,
    },
}

NUMERIC_COLUMNS = ["SourcePort", "DestinationPort", "Duration", "Bytes"]


def _is_attack_severity(value: object) -> int:
    """根據 Severity 欄位推論是否屬於攻擊流量。"""
    try:
        return 1 if int(str(value).strip()) <= 4 else 0
    except Exception:
        return 0


def step2_preprocess_data(
    step1_out_path: str,
    step2_out_path: str,
    unique_json: str,
    show_progress: bool = True,
) -> pd.DataFrame:
    """執行欄位映射、型態轉換與重複資料清理。"""
    if os.path.exists(unique_json):  # 讀入唯一值資訊，供日後擴充使用。
        with open(unique_json, "r", encoding="utf-8") as handle:
            json.load(handle)

    total_rows = sum(1 for _ in open(step1_out_path, encoding="utf-8"))
    chunks = []
    reader = pd.read_csv(step1_out_path, chunksize=50000)
    progress = tqdm(reader, total=max(total_rows // 50000, 1), desc="預處理進度", disable=not show_progress)
    for chunk in progress:
        for column, mapping in CATEGORICAL_MAPPINGS.items():
            if column in chunk.columns:
                chunk[column] = chunk[column].astype(str).str.lower().map(mapping).fillna(-1).astype(int)
        if "Severity" in chunk.columns:
            chunk["is_attack"] = chunk["Severity"].apply(_is_attack_severity)
        else:
            chunk["is_attack"] = 0
        for column in NUMERIC_COLUMNS:
            if column in chunk.columns:
                chunk[column] = pd.to_numeric(chunk[column], errors="coerce").fillna(0).astype(int)
        for column in STANDARD_COLUMNS:
            if column not in chunk.columns:
                chunk[column] = ""
        ordered = chunk[[col for col in STANDARD_COLUMNS if col != "raw_log"] + ["raw_log"]]
        ordered["batch_id"] = chunk.get("batch_id", 0)
        chunks.append(ordered)
    dataframe = pd.concat(chunks, ignore_index=True) if chunks else pd.DataFrame(columns=STANDARD_COLUMNS)
    dataframe.drop_duplicates(inplace=True)
    dataframe.to_csv(step2_out_path, index=False, encoding="utf-8")
    return dataframe
