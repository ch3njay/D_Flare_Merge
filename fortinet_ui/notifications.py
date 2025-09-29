"""Fortinet notification wrapper compatible with the router."""
from __future__ import annotations

import streamlit as st

from Forti_ui_app_bundle.notifier import notify_from_csv, send_discord, send_line_to_all
from Forti_ui_app_bundle.ui_pages import apply_dark_theme
from Forti_ui_app_bundle.ui_pages import notifier_app as _notifier_app


def _consume_command() -> str | None:
    return st.session_state.pop("fortinet_command_notifications", None)


def _flash(message: str) -> None:
    st.session_state.setdefault("fortinet_flash_messages", []).append(message)


def _dispatch(command: str | None) -> None:
    if not command:
        return
    if command == "notifications:reset_fields":
        for key in ["discord_webhook", "gemini_key", "line_token"]:
            st.session_state[key] = ""
        _flash("🧽 已清空通知設定欄位。")
    elif command == "notifications:test_discord":
        url = st.session_state.get("discord_webhook", "")
        if url:
            ok, info = send_discord(url, "This is a test notification from D-FLARE.")
            _flash("💬 Discord 測試成功。" if ok else f"⚠️ Discord 測試失敗：{info}")
        else:
            _flash("⚠️ 尚未設定 Discord Webhook URL。")
    elif command == "notifications:test_line":
        token = st.session_state.get("line_token", "")
        if token:
            ok = send_line_to_all(token, "This is a test notification from D-FLARE.")
            _flash("🟩 LINE 測試成功。" if ok else "⚠️ LINE 測試失敗。")
        else:
            _flash("⚠️ 尚未設定 LINE Channel Access Token。")
    elif command == "notifications:preview":
        csv_path = st.session_state.get("last_report_path")
        if csv_path:
            results = notify_from_csv(
                csv_path,
                st.session_state.get("discord_webhook", ""),
                st.session_state.get("gemini_key", ""),
                risk_levels={"3", "4"},
                ui_log=lambda msg: None,
                dedupe_cache=st.session_state.get("dedupe_cache"),
                line_token=st.session_state.get("line_token", ""),
                convergence=st.session_state.get("forti_convergence"),
            )
            success = sum(1 for _, ok, _ in results if ok)
            _flash(f"🔔 已預覽最近報表，共 {success} 則通知。")
        else:
            _flash("ℹ️ 尚未產生報表，可先於 Folder Monitor 執行分析。")


def render() -> None:
    """Render the Fortinet notification page with sidebar commands."""

    apply_dark_theme()
    _dispatch(_consume_command())
    _notifier_app.app()
