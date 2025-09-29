"""Cisco data cleaning wrapper for router orchestration."""
from __future__ import annotations

from typing import Callable, Dict

import streamlit as st

from Cisco_ui.ui_pages import apply_dark_theme
from Cisco_ui.ui_pages import data_cleaning as _data_cleaning
from Cisco_ui.ui_pages import log_monitor as _log_monitor

_CommandHandler = Callable[[_data_cleaning.DataCleaner], None]


def _flash(message: str) -> None:
    st.session_state.setdefault("cisco_flash_messages", []).append(message)


def _current_folder() -> str:
    monitor = _log_monitor.get_log_monitor()
    return st.session_state.get("cisco_clean_dir", monitor.settings.get("clean_csv_dir", ""))


def _current_retention() -> int:
    return int(st.session_state.get("保留小時數", 3))


def _current_interval() -> int:
    return int(st.session_state.get("自動清理間隔（小時）", 6))


def _start_auto(cleaner: _data_cleaning.DataCleaner) -> None:
    cleaner.start_auto(_current_folder(), _current_retention(), _current_interval())
    _flash("🟢 已啟動自動清理排程。")


def _stop_auto(cleaner: _data_cleaning.DataCleaner) -> None:
    cleaner.stop_auto()
    _flash("⛔ 已停止自動清理排程。")


def _manual(cleaner: _data_cleaning.DataCleaner) -> None:
    cleaner.manual_clean(_current_folder(), _current_retention())
    _flash("🧹 已執行一次手動清理。")


def _batch(cleaner: _data_cleaning.DataCleaner) -> None:
    cleaner.batch_delete(_current_folder())
    _flash("🗑️ 已批次清除目標資料夾內的檔案。")


def _consume_command() -> str | None:
    return st.session_state.pop("cisco_command_data_cleaning", None)


_HANDLERS: Dict[str, _CommandHandler] = {
    "data_cleaning:start_auto": _start_auto,
    "data_cleaning:stop_auto": _stop_auto,
    "data_cleaning:manual": _manual,
    "data_cleaning:purge": _batch,
}


def _dispatch(command: str | None) -> None:
    if not command:
        return
    handler = _HANDLERS.get(command)
    if not handler:
        return
    cleaner = _data_cleaning.get_data_cleaner()
    handler(cleaner)


def render() -> None:
    """Render the Cisco data cleaning page with queued command support."""

    apply_dark_theme()
    _dispatch(_consume_command())
    _data_cleaning.app()
