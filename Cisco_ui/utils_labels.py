"""Cisco UI 共用工具與標籤設定模組。

此模組集中管理所有 Streamlit 介面與 Pipeline 所需的共用輔助函式，
包含 JSON 設定讀寫、日誌緩衝處理與嚴重度標籤對應表。為了符合
獨立運行的需求，所有功能都以絕對匯入提供給其他子模組使用。
"""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

# 添加 ui_shared 模組路徑
_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT / "ui_shared") not in sys.path:
    sys.path.insert(0, str(_ROOT / "ui_shared"))

from notification_models import NotificationMessage, SEVERITY_LABELS

# ---- 常數定義 ----
LOG_BUFFER_LIMIT = 500

# ============================================================================
# Cisco ASA Severity 顏色配置
# ============================================================================
# 注意：Cisco ASA 的 Severity 與 Forti 相反！
# Cisco: 數字越小越嚴重（0=最嚴重紅色, 7=最不嚴重灰色）
# Forti: 數字越大越嚴重（4=最嚴重, 1=最不嚴重）
# ============================================================================
SEVERITY_COLORS = {
    0: "#8B0000",   # 深紅色 - Emergencies（緊急，系統不可用）
    1: "#DC143C",   # 猩紅色 - Alert（警報，需立即處理）
    2: "#FF4500",   # 橙紅色 - Critical（嚴重）
    3: "#FF8C00",   # 深橙色 - Error（錯誤）
    4: "#FFD700",   # 金色 - Warning（警告）
    5: "#90EE90",   # 淺綠色 - Notification（通知）
    6: "#87CEEB",   # 天藍色 - Informational（資訊）
    7: "#D3D3D3",   # 淺灰色 - Debugging（除錯）
}

# 舊的 Forti 配置（保留供參考）
# SEVERITY_COLORS_FORTI = {
#     1: "#7bd684",  # 綠色 - 低風險
#     2: "#29b6f6",  # 藍色 - 中風險
#     3: "#ffb300",  # 橙色 - 高風險
#     4: "#ea3b3b",  # 紅色 - 危險
# }


# ---- Severity 相關輔助函式 ----
def get_severity_color(severity: int, default: str = "#808080") -> str:
    """取得 Severity 對應的顏色
    
    Args:
        severity: Severity 等級（0-7）
        default: 若找不到對應顏色時的預設值
        
    Returns:
        十六進位顏色代碼
    """
    return SEVERITY_COLORS.get(severity, default)


def get_severity_label(severity: int, default: str = "未知") -> str:
    """取得 Severity 對應的中文標籤
    
    Args:
        severity: Severity 等級（0-7）
        default: 若找不到對應標籤時的預設值
        
    Returns:
        中文標籤字串
    """
    return SEVERITY_LABELS.get(severity, default)


def format_severity_display(severity: int) -> str:
    """格式化 Severity 顯示（包含等級和標籤）
    
    Args:
        severity: Severity 等級（0-7）
        
    Returns:
        格式化字串，例如 "Level 1 (警報)"
    """
    label = get_severity_label(severity)
    return f"Level {severity} ({label})"


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
