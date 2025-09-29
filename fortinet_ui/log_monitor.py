"""Fortinet folder monitor wrapper for unified router usage."""
from __future__ import annotations

import os

import streamlit as st

from Forti_ui_app_bundle.ui_pages import apply_dark_theme
from Forti_ui_app_bundle.ui_pages import folder_monitor_ui as _folder_monitor


def _consume_command() -> str | None:
    return st.session_state.pop("fortinet_command_log_monitor", None)


def _flash(message: str) -> None:
    st.session_state.setdefault("fortinet_flash_messages", []).append(message)


def _dispatch(command: str | None) -> None:
    if not command:
        return
    if command == "log_monitor:use_cwd":
        st.session_state["folder_input"] = os.getcwd()
        _flash("📁 已改為監控目前工作目錄。")
    elif command == "log_monitor:clear_generated":
        _folder_monitor._cleanup_generated(0, force=True)
        _flash("🧹 已清除所有暫存輸出檔案。")


def render() -> None:
    """Render Fortinet folder monitor page with command hooks."""

    apply_dark_theme()
    _dispatch(_consume_command())
    _folder_monitor.app()
