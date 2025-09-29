"""Fortinet visualization wrapper for unified routing."""
from __future__ import annotations

import streamlit as st

from Forti_ui_app_bundle.ui_pages import apply_dark_theme
from Forti_ui_app_bundle.ui_pages import visualization_ui as _visualization


def _consume_command() -> str | None:
    return st.session_state.pop("fortinet_command_visualization", None)


def _flash(message: str) -> None:
    st.session_state.setdefault("fortinet_flash_messages", []).append(message)


def _dispatch(command: str | None) -> None:
    if not command:
        return
    if command == "visualization:clear_cache":
        st.session_state.pop("last_counts", None)
        st.session_state.pop("last_report_path", None)
        _flash("♻️ 已清除暫存的圖表資料。")
    elif command == "visualization:load_latest":
        report = st.session_state.get("last_report_path")
        if report:
            _flash(f"📊 目前檢視報表：{report}")
        else:
            _flash("ℹ️ 尚未產生報表，可先於 Folder Monitor 執行分析。")


def render() -> None:
    """Render the Fortinet visualization module."""

    apply_dark_theme()
    _dispatch(_consume_command())
    _visualization.app()
