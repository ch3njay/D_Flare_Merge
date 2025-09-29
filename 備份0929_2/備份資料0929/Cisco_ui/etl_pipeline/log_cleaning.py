"""Cisco ASA Log 清洗流程。"""
from __future__ import annotations

import csv
import json
from typing import Dict, Iterable, Tuple

from tqdm import tqdm

from .utils import STANDARD_COLUMNS, detect_encoding, iter_unique_columns


def step1_process_logs(
    raw_log_path: str,
    step1_out_path: str,
    unique_out_json: str,
    batch_id: int,
    show_progress: bool = True,
) -> Tuple[int, Dict[str, Iterable[str]]]:
    """執行原始 log 的清洗與唯一值統計。"""
    encoding = detect_encoding(raw_log_path)
    total_lines = max(sum(1 for _ in open(raw_log_path, encoding=encoding)) - 1, 0)

    unique_vals = iter_unique_columns(STANDARD_COLUMNS)
    processed_count = 0

    with open(raw_log_path, "r", encoding=encoding, errors="replace") as source, open(
        step1_out_path, "w", newline="", encoding="utf-8"
    ) as target:
        reader = csv.DictReader(source)
        writer = csv.DictWriter(target, fieldnames=STANDARD_COLUMNS)
        writer.writeheader()
        progress = tqdm(reader, total=total_lines, desc="清洗進度", disable=not show_progress)
        for row in progress:
            record = {column: row.get(column, "") for column in STANDARD_COLUMNS}
            record["batch_id"] = batch_id
            record["raw_log"] = json.dumps(row, ensure_ascii=False)
            for column in STANDARD_COLUMNS:
                if column not in record:
                    record[column] = "unknown"
                unique_vals[column].add(record[column])
            writer.writerow(record)
            processed_count += 1

    unique_json = {key: sorted(values) for key, values in unique_vals.items()}
    with open(unique_out_json, "w", encoding="utf-8") as handle:
        json.dump(unique_json, handle, ensure_ascii=False, indent=4)
    return processed_count, unique_json
