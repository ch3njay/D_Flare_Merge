"""Streamlit interface for notification utilities."""

import tempfile
from pathlib import Path

import streamlit as st

from ..notifier import notify_from_csv, send_discord, send_line_to_all
from . import apply_dark_theme  # [ADDED]


def app() -> None:
    apply_dark_theme()  # [ADDED]
    st.title("Notification System")
    st.info(
        "Upload a result CSV to send high-risk events to Discord/LINE. Configure "
        "webhook and AI settings in the expandable section below."
    )

    with st.expander("Notification Settings", expanded=False):
        webhook = st.text_input("Discord Webhook URL", key="discord_webhook")
        gemini_key = st.text_input(
            "Gemini API Key", type="password", key="gemini_key"
        )
        line_token = st.text_input(
            "LINE Channel Access Token", type="password", key="line_token"
        )

        risk_levels = st.multiselect("High-risk levels", [1, 2, 3, 4], default=[3, 4])
        dedupe_strategy = st.selectbox(
            "Deduplication strategy", ["Filename + mtime", "File hash"]
        )

    dedupe_cache = st.session_state.setdefault(
        "dedupe_cache", {"strategy": "mtime", "keys": set()}
    )
    dedupe_cache["strategy"] = "hash" if dedupe_strategy == "File hash" else "mtime"
    st.caption("Actions")
    if st.button("Send Discord test notification"):
        if webhook:
            ok, info = send_discord(webhook, "This is a test notification from D-FLARE.")
            if ok:
                st.success("Test notification sent")
            else:
                st.error(f"Failed to send: {info}")
        else:
            st.warning("Please set the Discord Webhook URL first")

    if st.button("Send LINE test notification"):
        token = st.session_state.get("line_token", "")
        if token:
            if send_line_to_all(token, "This is a test notification from D-FLARE."):
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

        if st.button("Parse and notify"):

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
            )
            progress.progress(100)
            success = sum(1 for _, ok, _ in results if ok)
            fail = sum(1 for _, ok, _ in results if not ok)
            st.info(f"Succeeded {success}, failed {fail}")

