"""Fortinet GPU ETL wrapper to fit the new router contract."""
from __future__ import annotations

import streamlit as st

from Forti_ui_app_bundle.ui_pages import apply_dark_theme
from Forti_ui_app_bundle.ui_pages import gpu_etl_ui as _gpu_etl


_CHECKBOX_KEYS = ["Run cleaning", "Run mapping", "Run feature engineering"]


def _consume_command() -> str | None:
    return st.session_state.pop("fortinet_command_data_cleaning", None)


def _flash(message: str) -> None:
    st.session_state.setdefault("fortinet_flash_messages", []).append(message)


def _dispatch(command: str | None) -> None:
    if not command:
        return
    if command == "data_cleaning:select_all":
        for key in _CHECKBOX_KEYS:
            st.session_state[key] = True
        _flash("✅ 已開啟所有 ETL 步驟。")
    elif command == "data_cleaning:clear_all":
        for key in _CHECKBOX_KEYS:
            st.session_state[key] = False
        _flash("🚫 已停用所有 ETL 步驟。")
    elif command == "data_cleaning:reset_output":
        st.session_state["Output CSV path"] = "engineered_data.csv"
        _flash("📄 已重設輸出檔名為預設值。")


def render() -> None:
    """Render Fortinet GPU ETL page with sidebar automation hooks."""

    apply_dark_theme()
    _dispatch(_consume_command())
    _gpu_etl.app()
