"""Cisco notification page wrapper with sidebar triggers."""
from __future__ import annotations

import streamlit as st

from Cisco_ui.ui_pages import apply_dark_theme
from Cisco_ui.ui_pages import notifications as _notifications


def _consume_command() -> str | None:
    return st.session_state.pop("cisco_command_notifications", None)


def _dispatch(command: str | None) -> None:
    if not command:
        return
    settings = _notifications._load_settings()
    if command == "notifications:save":
        _notifications._save_settings(settings)
        st.session_state.setdefault("cisco_flash_messages", []).append("💾 已儲存通知設定。")
    elif command == "notifications:test_line":
        _notifications._send_line_test(settings)
        st.session_state.setdefault("cisco_flash_messages", []).append("🟩 已透過側邊欄觸發 LINE 測試通知。")
    elif command == "notifications:test_discord":
        _notifications._send_discord_test(settings)
        st.session_state.setdefault("cisco_flash_messages", []).append("💬 已透過側邊欄觸發 Discord 測試通知。")


def render() -> None:
    """Render Cisco notification page after consuming sidebar commands."""

    apply_dark_theme()
    _dispatch(_consume_command())
    _notifications.app()
