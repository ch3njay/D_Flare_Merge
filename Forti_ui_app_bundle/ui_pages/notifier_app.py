"""Streamlit interface for notification utilities."""

import os
import tempfile
from pathlib import Path
from typing import Dict, List

import streamlit as st

from ..notifier import notify_from_csv, send_discord, send_line_to_all
from . import apply_dark_theme  # [ADDED]

# 設定檔案路徑
SETTINGS_FILE = "forti_notifier_settings.txt"
USER_FILE = "forti_line_users.txt"
LAST_USER_FILE = "forti_last_user.txt"

# 常數定義
DEDUPE_STRATEGY_MTIME = "Filename + mtime"
DEDUPE_STRATEGY_HASH = "File hash"

# 預設設定
DEFAULT_SETTINGS = {
    "gemini_api_key": "",
    "line_channel_secret": "",
    "line_channel_access_token": "",
    "line_webhook_url": "",
    "discord_webhook_url": "",
    "convergence_window_minutes": 10,
    "convergence_fields": ["source", "destination"],
    "risk_levels": [3, 4],
    "dedupe_strategy": DEDUPE_STRATEGY_MTIME
}


def _get_status_buffer() -> List[str]:
    """取得狀態緩衝區"""
    if "forti_notifier_logs" not in st.session_state:
        st.session_state["forti_notifier_logs"] = []
    return st.session_state["forti_notifier_logs"]


def _load_settings() -> Dict[str, str]:
    """載入設定"""
    if "forti_notifier_settings" not in st.session_state:
        try:
            import json
            if os.path.exists(SETTINGS_FILE):
                with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
                    loaded = json.load(f)
                    st.session_state["forti_notifier_settings"] = {**DEFAULT_SETTINGS, **loaded}
            else:
                st.session_state["forti_notifier_settings"] = DEFAULT_SETTINGS.copy()
        except (FileNotFoundError, json.JSONDecodeError):
            st.session_state["forti_notifier_settings"] = (
                DEFAULT_SETTINGS.copy())
    return st.session_state["forti_notifier_settings"]


def _save_settings(data: Dict[str, str]) -> None:
    """儲存設定"""
    st.session_state["forti_notifier_settings"] = data
    try:
        import json
        with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        logs = _get_status_buffer()
        logs.append("✅ 設定已儲存")
        if len(logs) > 100:  # 限制日誌長度
            logs.pop(0)
    except (IOError, PermissionError) as e:
        logs = _get_status_buffer()
        logs.append(f"❌ 設定儲存失敗：{e}")


def app() -> None:
    apply_dark_theme()  # [ADDED]
    st.title("🔔 Notification System")
    st.info(
        "Upload a result CSV to send high-risk events to Discord/LINE. "
        "Settings are automatically saved."
    )

    # 載入設定
    settings = _load_settings()

    with st.expander("Notification Settings", expanded=False):
        webhook = st.text_input(
            "Discord Webhook URL",
            value=settings.get("discord_webhook_url", ""),
            key="discord_webhook"
        )
        gemini_key = st.text_input(
            "Gemini API Key",
            type="password",
            value=settings.get("gemini_api_key", ""),
            key="gemini_key"
        )
        line_token = st.text_input(
            "LINE Channel Access Token",
            type="password",
            value=settings.get("line_channel_access_token", ""),
            key="line_token"
        )

        default_risks = settings.get("risk_levels", [3, 4])
        risk_levels = st.multiselect(
            "High-risk levels", [1, 2, 3, 4], default=default_risks)
        
        default_dedupe = settings.get("dedupe_strategy", DEDUPE_STRATEGY_MTIME)
        dedupe_strategy = st.selectbox(
            "Deduplication strategy",
            [DEDUPE_STRATEGY_MTIME, DEDUPE_STRATEGY_HASH],
            index=0 if default_dedupe == DEDUPE_STRATEGY_MTIME else 1
        )

        st.markdown("---")
        st.markdown("#### Notification convergence")
        
        default_window = settings.get("convergence_window_minutes", 10)
        window_minutes = st.slider(
            "Time window (minutes)",
            min_value=1,
            max_value=120,
            value=int(default_window or 10),
            help="Merge similar alerts that occur within the time range.",
        )
        field_options = {
            "source": "Source IP",
            "destination": "Destination IP",
            "protocol": "Protocol",
            "port": "Destination Port",
        }
        default_fields = settings.get(
            "convergence_fields", ["source", "destination"])
        selected_fields = st.multiselect(
            "Similarity conditions",
            options=list(field_options.keys()),
            default=default_fields,
            format_func=lambda key: field_options[key],
            help="Alerts sharing these attributes will be merged.",
        )
        # 準備要儲存的設定
        pending_settings = {
            "gemini_api_key": gemini_key,
            "discord_webhook_url": webhook,
            "line_channel_access_token": line_token,
            "convergence_window_minutes": window_minutes,
            "convergence_fields": selected_fields,
            "risk_levels": risk_levels,
            "dedupe_strategy": dedupe_strategy
        }

        # 儲存設定按鈕
        if st.button("💾 儲存所有設定", use_container_width=True):
            _save_settings(pending_settings)

        # 更新session state用於convergence
        st.session_state["forti_convergence"] = {
            "window_minutes": window_minutes,
            "group_fields": selected_fields,
        }

    dedupe_cache = st.session_state.setdefault(
        "dedupe_cache", {"strategy": "mtime", "keys": set()}
    )
    strategy = "hash" if dedupe_strategy == DEDUPE_STRATEGY_HASH else "mtime"
    dedupe_cache["strategy"] = strategy
    
    st.caption("Actions")
    action_cols = st.columns(2)
    with action_cols[0]:
        if st.button("Send Discord test notification",
                     use_container_width=True):
            if webhook:
                test_msg = "This is a test notification from D-FLARE."
                ok, info = send_discord(webhook, test_msg)
                if ok:
                    st.success("Test notification sent")
                else:
                    st.error(f"Failed to send: {info}")
            else:
                st.warning("Please set the Discord Webhook URL first")
    with action_cols[1]:
        if st.button("Send LINE test notification", use_container_width=True):
            token_value = line_token or st.session_state.get("line_token", "")
            if token_value:
                test_msg = "This is a test notification from D-FLARE."
                if send_line_to_all(token_value, test_msg):
                    st.success("LINE test notification sent")
                else:
                    st.error("Failed to send LINE notification")
            else:
                st.warning("Please set the LINE Channel Access Token first")

    uploaded = st.file_uploader("Select result CSV", type=["csv"])
    if uploaded is not None:
        temp_dir = tempfile.gettempdir()
        tmp_path = Path(temp_dir) / uploaded.name
        with open(tmp_path, "wb") as fh:
            fh.write(uploaded.getbuffer())

        if st.button("Parse and notify", use_container_width=True):

            if not webhook and not line_token:
                st.info("Notifications will be displayed only in this app.")
            progress = st.progress(0)
            results = notify_from_csv(
                str(tmp_path),
                webhook,
                gemini_key,
                risk_levels={str(r) for r in risk_levels},
                ui_log=st.write,
                dedupe_cache=dedupe_cache,
                progress_cb=lambda frac: progress.progress(int(frac * 100)),
                line_token=line_token,
                convergence=st.session_state.get("forti_convergence"),
            )
            progress.progress(100)
            success = sum(1 for _, ok, _ in results if ok)
            fail = sum(1 for _, ok, _ in results if not ok)
            st.info(f"Succeeded {success}, failed {fail}")

    # 顯示狀態日誌
    st.markdown("### 推播狀態回饋")
    logs = _get_status_buffer()
    if logs:
        st.text_area("通知日誌", value="\n".join(logs), height=150)

