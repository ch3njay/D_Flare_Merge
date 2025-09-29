"""Cisco model inference wrapper with streamlined sidebar hooks."""
from __future__ import annotations

import streamlit as st

from Cisco_ui.ui_pages import apply_dark_theme
from Cisco_ui.ui_pages import model_inference as _model_inference


def _consume_command() -> str | None:
    return st.session_state.pop("cisco_command_model_inference", None)


def _dispatch(command: str | None) -> None:
    if not command:
        return
    if command == "model_inference:use_recent":
        st.session_state["cisco_use_recent_log_checkbox"] = True
        st.session_state.setdefault("cisco_flash_messages", []).append(
            "📁 已切換為使用最近的監控檔案。"
        )
    elif command == "model_inference:clear_uploads":
        for key in [
            "cisco_inference_log_uploader",
            "binary_upload",
            "multi_upload",
        ]:
            st.session_state.pop(key, None)
        st.session_state.setdefault("cisco_flash_messages", []).append(
            "🧼 已清除上傳的模型與檔案選擇。"
        )
    elif command == "model_inference:focus_output":
        monitor = _model_inference.get_log_monitor()
        target = monitor.settings.get("clean_csv_dir", "")
        st.session_state["輸出資料夾"] = target
        st.session_state.setdefault("cisco_flash_messages", []).append(
            "📦 已同步輸出資料夾至自動清洗目錄。"
        )


def render() -> None:
    """Render Cisco model inference page after processing sidebar commands."""

    apply_dark_theme()
    _dispatch(_consume_command())
    _model_inference.app()
