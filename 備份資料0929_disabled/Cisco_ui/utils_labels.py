"""Cisco UI 共用工具與標籤設定模組。

此模組集中管理所有 Streamlit 介面與 Pipeline 所需的共用輔助函式，
包含 JSON 設定讀寫、日誌緩衝處理與嚴重度標籤對應表。為了符合
獨立運行的需求，所有功能都以絕對匯入提供給其他子模組使用。
"""
from __future__ import annotations

import json
import os
from datetime import datetime
from typing import Any, Dict, List

from notification_models import NotificationMessage, SEVERITY_LABELS

# ---- 常數定義 ----
LOG_BUFFER_LIMIT = 500

SEVERITY_COLORS = {
    1: "#ea3b3b",
    2: "#ffb300",
    3: "#29b6f6",
    4: "#7bd684",
}


# ---- 共用工具函式 ----
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
