"""Cisco visualization wrapper used by the router."""
from __future__ import annotations

import itertools

import streamlit as st

from Cisco_ui.ui_pages import apply_dark_theme
from Cisco_ui.ui_pages import visualization as _visualization
from Cisco_ui.ui_pages.log_monitor import get_log_monitor


def _consume_command() -> str | None:
    return st.session_state.pop("cisco_command_visualization", None)


def _dispatch(command: str | None) -> None:
    if not command:
        return
    if command == "visualization:sync":
        monitor = get_log_monitor()
        st.session_state["cisco_visual_folder"] = monitor.settings.get("clean_csv_dir", "")
        st.session_state.setdefault("cisco_flash_messages", []).append("📂 已同步圖表資料夾位置。")
    elif command == "visualization:cycle":
        buttons = list(_visualization.CHART_FILES.keys())
        current = st.session_state.get("cisco_visual_selected", buttons[0])
        cycle = itertools.cycle(buttons)
        for label in cycle:
            if label == current:
                st.session_state["cisco_visual_selected"] = next(cycle)
                break
        st.session_state.setdefault("cisco_flash_messages", []).append("🔄 已切換到下一個圖表。")


def render() -> None:
    """Render the Cisco visualization page."""

    apply_dark_theme()
    _dispatch(_consume_command())
    _visualization.app()
