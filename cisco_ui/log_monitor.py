"""Cisco brand log monitor wrapper with sidebar integrations."""
from __future__ import annotations

from typing import Callable, Dict

import streamlit as st

from Cisco_ui.ui_pages import apply_dark_theme
from Cisco_ui.ui_pages import log_monitor as _log_monitor

_CommandHandler = Callable[[_log_monitor.LogMonitor], None]


def _flash(message: str) -> None:
    st.session_state.setdefault("cisco_flash_messages", []).append(message)


def _start(monitor: _log_monitor.LogMonitor) -> None:
    monitor.start_listening()
    _flash("🟢 已透過側邊欄啟動資料夾監控。")


def _stop(monitor: _log_monitor.LogMonitor) -> None:
    monitor.stop_listening()
    _flash("⛔ 已停止資料夾監控。")


def _scan(monitor: _log_monitor.LogMonitor) -> None:
    monitor.scan_once()
    _flash("🔁 已手動掃描一次監控資料夾。")


def _consume_command() -> str | None:
    return st.session_state.pop("cisco_command_log_monitor", None)


_HANDLERS: Dict[str, _CommandHandler] = {
    "log_monitor:start": _start,
    "log_monitor:stop": _stop,
    "log_monitor:scan": _scan,
}


def _dispatch(command: str | None) -> None:
    if not command:
        return
    handler = _HANDLERS.get(command)
    if not handler:
        return
    monitor = _log_monitor.get_log_monitor()
    handler(monitor)


def render() -> None:
    """Render the Cisco log monitor page after dispatching queued commands."""

    apply_dark_theme()
    _dispatch(_consume_command())
    _log_monitor.app()
