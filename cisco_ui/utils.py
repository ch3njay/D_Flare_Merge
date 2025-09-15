"""Cisco Streamlit UI 共用工具函式模組。

此模組集中管理設定檔讀寫、日誌紀錄等共用邏輯，
提供其他子模組呼叫以維持程式碼一致性。所有函式皆附上
中文註解，方便後續維護與擴充。
"""
from __future__ import annotations

import json
import os
from datetime import datetime
from typing import Any, Dict, List

LOG_BUFFER_LIMIT = 500


def load_json(path: str, default: Dict[str, Any] | None = None) -> Dict[str, Any]:
    """讀取 JSON 設定檔，若不存在則回傳預設值。"""
    if default is None:
        default = {}
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as handle:
                data = json.load(handle)
            if isinstance(data, dict):
                return data
        except Exception:
            # 若讀檔失敗則回傳預設值，避免整體流程中斷。
            pass
    return dict(default)


def save_json(path: str, data: Dict[str, Any]) -> None:
    """將資料以 JSON 格式寫入指定路徑。"""
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(data, handle, ensure_ascii=False, indent=2)


def append_log(buffer: List[str], message: str) -> None:
    """將訊息附上時間戳記後寫入日誌緩衝區。"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    buffer.append(f"[{timestamp}] {message}")
    if len(buffer) > LOG_BUFFER_LIMIT:
        del buffer[:-LOG_BUFFER_LIMIT]


def ensure_directory(path: str) -> None:
    """確認資料夾存在，不存在時自動建立。"""
    if path and not os.path.exists(path):
        os.makedirs(path, exist_ok=True)
