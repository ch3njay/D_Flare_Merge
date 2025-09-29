"""Cisco 通知模組（Streamlit 版）。"""
from __future__ import annotations

import os
from typing import Dict, List

import streamlit as st

try:  # Prefer package-relative imports when available
    from ..notifier import send_discord
    from ..utils_labels import append_log, load_json, save_json
except (ImportError, ValueError):  # Fallback for running inside package folder directly
    from notifier import send_discord  # type: ignore[no-redef]
    from utils_labels import append_log, load_json, save_json  # type: ignore[no-redef]

SETTINGS_FILE = "notifier_settings.txt"
USER_FILE = "line_users.txt"
LAST_USER_FILE = "last_user.txt"
DEFAULT_SETTINGS = {
    "gemini_api_key": "",
    "line_channel_secret": "",
    "line_channel_access_token": "",
    "line_webhook_url": "",
    "discord_webhook_url": "",
    "convergence_window_minutes": 10,
    "convergence_fields": ["source", "destination"],
}


def _get_status_buffer() -> List[str]:
    if "cisco_notifier_logs" not in st.session_state:
        st.session_state["cisco_notifier_logs"] = []
    return st.session_state["cisco_notifier_logs"]


def _load_settings() -> Dict[str, str]:
    if "cisco_notifier_settings" not in st.session_state:
        st.session_state["cisco_notifier_settings"] = load_json(SETTINGS_FILE, DEFAULT_SETTINGS)
    return st.session_state["cisco_notifier_settings"]


def _save_settings(data: Dict[str, str]) -> None:
    st.session_state["cisco_notifier_settings"] = data
    save_json(SETTINGS_FILE, data)
    append_log(_get_status_buffer(), "✅ 設定已儲存")


def _get_last_user_id() -> str | None:
    if os.path.exists(LAST_USER_FILE):
        with open(LAST_USER_FILE, "r", encoding="utf-8") as handle:
            content = handle.read().strip()
            if content:
                return content
    if os.path.exists(USER_FILE):
        with open(USER_FILE, "r", encoding="utf-8") as handle:
            ids = [line.strip() for line in handle if line.strip()]
            if ids:
                return ids[-1]
    return None


def _send_line_test(settings: Dict[str, str]) -> None:
    buffer = _get_status_buffer()
    user_id = _get_last_user_id()
    if not user_id:
        append_log(buffer, "❌ 找不到 LINE 使用者 ID，請先透過 Bot 綁定")
        return
    token = settings.get("line_channel_access_token", "").strip()
    if not token:
        append_log(buffer, "❌ 請先設定 LINE Channel Access Token")
        return
    try:
        from linebot.v3.messaging import MessagingApi, Configuration, ApiClient
        from linebot.v3.messaging.models import TextMessage, PushMessageRequest
    except Exception as exc:  # pragma: no cover - 無套件環境
        append_log(buffer, f"❌ 無法載入 LINE SDK：{exc}")
        return
    try:
        config = Configuration(access_token=token)
        with ApiClient(config) as api_client:
            line_api = MessagingApi(api_client)
            msg = TextMessage(text="✅ 已發送 LINE 測試通知 (D-FLARE)")
            req = PushMessageRequest(to=user_id, messages=[msg])
            line_api.push_message(push_message_request=req)
        append_log(buffer, "✅ 已發送 LINE 測試通知")
    except Exception as exc:  # pragma: no cover
        append_log(buffer, f"❌ LINE 發送失敗：{exc}")


def _send_discord_test(settings: Dict[str, str]) -> None:
    buffer = _get_status_buffer()
    url = settings.get("discord_webhook_url", "").strip()
    if not url:
        append_log(buffer, "❌ 請先輸入 Discord Webhook URL")
        return
    send_discord(url, "💬 D-FLARE 測試通知", callback=lambda msg: append_log(buffer, msg))


def app() -> None:
    """通知模組主畫面。"""
    st.title("🔔 通知設定與推播")
    st.markdown("設定 Gemini、LINE 與 Discord 參數，並可立即進行測試推播。")

    settings = _load_settings()

    gemini = st.text_input("Gemini API Key", value=settings.get("gemini_api_key", ""), type="password")
    line_secret = st.text_input("LINE Channel Secret", value=settings.get("line_channel_secret", ""), type="password")
    line_token = st.text_input(
        "LINE Channel Access Token",
        value=settings.get("line_channel_access_token", ""),
        type="password",
    )
    line_webhook = st.text_input("LINE Webhook URL", value=settings.get("line_webhook_url", ""))
    discord_url = st.text_input("Discord Webhook URL", value=settings.get("discord_webhook_url", ""))

    default_fields = settings.get("convergence_fields", ["source", "destination"])
    if not isinstance(default_fields, list):
        default_fields = ["source", "destination"]

    with st.expander("🔁 通知收斂條件", expanded=False):
        window_minutes = st.slider(
            "時間收斂範圍（分鐘）",
            min_value=1,
            max_value=120,
            value=int(settings.get("convergence_window_minutes", 10) or 10),
            step=1,
            help="在設定的時間範圍內合併相似告警，以降低 Gemini token 消耗並避免重複推播。",
        )
        field_options = {
            "source": "來源 IP",
            "destination": "目的 IP",
            "protocol": "通訊協定",
            "port": "目的 Port",
        }
        selected_fields = st.multiselect(
            "收斂條件欄位",
            options=list(field_options.keys()),
            default=default_fields,
            format_func=lambda key: field_options[key],
            help="選擇需要相同的欄位才會被視為相似告警，留空則僅依據時間窗收斂。",
        )
        st.caption("所有外部通知（Gemini、LINE、Discord）均會套用這組收斂條件。")

    pending_settings = {
        "gemini_api_key": gemini,
        "line_channel_secret": line_secret,
        "line_channel_access_token": line_token,
        "line_webhook_url": line_webhook,
        "discord_webhook_url": discord_url,
        "convergence_window_minutes": window_minutes,
        "convergence_fields": selected_fields,
    }

    action_cols = st.columns(3)
    if action_cols[0].button("💾 儲存所有設定", use_container_width=True):
        _save_settings(pending_settings)
    if action_cols[1].button("🟩 發送 LINE 測試通知", use_container_width=True):
        _send_line_test(pending_settings)
    if action_cols[2].button("💬 發送 Discord 測試通知", use_container_width=True):
        _send_discord_test(pending_settings)

    st.markdown("### 推播狀態回饋")
    st.text_area("通知日誌", value="\n".join(_get_status_buffer()), height=260)
