"""Fortinet model inference wrapper to support router commands."""
from __future__ import annotations

import streamlit as st

from Forti_ui_app_bundle.ui_pages import apply_dark_theme
from Forti_ui_app_bundle.ui_pages import inference_ui as _inference

_UPLOAD_KEYS = ["Upload data CSV", "Upload binary model", "Upload multiclass model"]


def _consume_command() -> str | None:
    return st.session_state.pop("fortinet_command_model_inference", None)


def _flash(message: str) -> None:
    st.session_state.setdefault("fortinet_flash_messages", []).append(message)


def _dispatch(command: str | None) -> None:
    if not command:
        return
    if command == "model_inference:reset_inputs":
        for key in _UPLOAD_KEYS:
            st.session_state.pop(key, None)
        st.session_state.pop("prediction_results", None)
        _flash("🧹 已清除上傳的資料與模型。")
    elif command == "model_inference:clear_results":
        st.session_state.pop("prediction_results", None)
        _flash("🗑️ 已移除先前的推論結果。")
    elif command == "model_inference:prefill":
        st.session_state["Upload data CSV"] = None
        st.session_state["Upload binary model"] = None
        st.session_state["Upload multiclass model"] = None
        _flash("📄 請上傳新的資料與模型檔案。")


def render() -> None:
    """Render Fortinet inference page with sidebar automation hooks."""

    apply_dark_theme()
    _dispatch(_consume_command())
    _inference.app()
