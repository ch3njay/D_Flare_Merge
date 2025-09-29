"""Shared notification data structures for D-FLARE UI modules."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional, Tuple

# 共用的嚴重度標籤定義，供通知模組與介面顯示使用。
SEVERITY_LABELS = {
    1: "危險",
    2: "高",
    3: "中",
    4: "低",
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
            lines.append("🤖 AI 建議：")
            lines.append(self.suggestion.strip())

        return "\n".join(lines).strip()


__all__ = ["NotificationMessage", "SEVERITY_LABELS"]
