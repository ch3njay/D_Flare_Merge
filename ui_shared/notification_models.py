"""Shared notification data structures for D-FLARE UI modules."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional, Tuple

# ============================================================================
# Cisco ASA Severity 標籤定義
# ============================================================================
# 注意：Cisco ASA 的 Severity 與 Forti 相反
# Cisco: 數字越小越嚴重（0=最嚴重, 7=最不嚴重）
# Forti: 數字越大越嚴重（4=最嚴重, 1=最不嚴重）
# ============================================================================
SEVERITY_LABELS = {
    0: "緊急",      # Emergencies - 系統不可用（硬體損壞）
    1: "警報",      # Alert - 需要立即處理
    2: "嚴重",      # Critical - 嚴重狀況
    3: "錯誤",      # Error - 錯誤狀況
    4: "警告",      # Warning - 警告狀況
    5: "通知",      # Notification - 正常但重要
    6: "資訊",      # Informational - 資訊性訊息
    7: "除錯",      # Debugging - 除錯訊息
}


@dataclass(slots=True)
class NotificationMessage:
    """封裝跨品牌共用的通知訊息格式。"""

    severity: int
    source_ip: str
    description: str
    suggestion: str = ""
    aggregated_count: int = 1
    time_window: Optional[Tuple[str, str]] = None
    match_signature: str = ""
    aggregated_descriptions: List[str] = field(default_factory=list)

    def to_text(self) -> str:
        """將通知內容轉換為適合推播的文字格式。"""

        lines: List[str] = [
            "🚨 偵測到高風險事件",
            f"等級：{SEVERITY_LABELS.get(self.severity, str(self.severity))}",
        ]

        if self.aggregated_count > 1:
            lines.append(f"🔁 收斂通知：整合 {self.aggregated_count} 則相似告警")
            if self.time_window:
                start, end = self.time_window
                lines.append(f"⏱️ 時間範圍：{start} ～ {end}")
            if self.match_signature:
                lines.append(f"🎯 匹配條件：{self.match_signature}")

        if self.source_ip:
            lines.append(f"來源 IP：{self.source_ip}")

        if self.description:
            lines.append(f"描述：{self.description}")

        extra_descs = [
            desc
            for desc in self.aggregated_descriptions
            if desc and desc != self.description
        ]
        if extra_descs:
            lines.append("📚 其他相似事件摘要：")
            preview = extra_descs[:3]
            lines.extend(f"• {desc}" for desc in preview)
            remaining = len(extra_descs) - len(preview)
            if remaining > 0:
                lines.append(f"• 另有 {remaining} 筆相似描述")

        if self.suggestion:
            lines.append("⚙️ AI 建議：")
            lines.append(self.suggestion.strip())

        return "\n".join(lines).strip()


__all__ = ["NotificationMessage", "SEVERITY_LABELS"]
