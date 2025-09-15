"""Cisco 資料清理模組（Streamlit 版）。"""
from __future__ import annotations

import os
import threading
import time
from datetime import datetime
from typing import List

import streamlit as st

from .log_viewer import get_log_monitor
from .utils import append_log

DEFAULT_EXTENSIONS = [".csv", ".png", ".log"]


class DataCleaner:
    """掌管手動與自動清理流程的控制器。"""

    def __init__(self) -> None:
        self.log_messages: List[str] = []
        self.extensions: List[str] = DEFAULT_EXTENSIONS.copy()
        self.auto_thread: threading.Thread | None = None
        self.stop_event = threading.Event()
        self.running = False
        self.cleaning_lock = threading.Lock()

    def _validate_folder(self, folder: str) -> bool:
        if not folder:
            append_log(self.log_messages, "❗ 請先設定資料夾路徑")
            return False
        if not os.path.isdir(folder):
            append_log(self.log_messages, f"❌ 資料夾不存在：{folder}")
            return False
        return True

    def start_auto(self, folder: str, retention: int, interval: int) -> None:
        if self.running:
            append_log(self.log_messages, "⚠️ 自動清理已啟動")
            return
        if not self._validate_folder(folder):
            return
        self.stop_event.clear()
        self.running = True
        monitor = get_log_monitor()
        self.auto_thread = threading.Thread(
            target=self._auto_loop,
            args=(folder, retention, interval, monitor),
            daemon=True,
        )
        self.auto_thread.start()
        append_log(self.log_messages, f"🟢 自動清理啟動，每 {interval} 小時執行一次")

    def stop_auto(self) -> None:
        if not self.running:
            append_log(self.log_messages, "ℹ️ 自動清理尚未啟動")
            return
        self.stop_event.set()
        if self.auto_thread and self.auto_thread.is_alive():
            self.auto_thread.join(timeout=3)
        self.auto_thread = None
        self.running = False
        append_log(self.log_messages, "⛔ 自動清理已停止")

    def _auto_loop(self, folder: str, retention: int, interval: int, monitor) -> None:
        while not self.stop_event.is_set():
            self._execute_clean(folder, retention, "auto", monitor)
            if self.stop_event.wait(interval * 3600):
                break
        self.running = False

    def manual_clean(self, folder: str, retention: int) -> None:
        if not self._validate_folder(folder):
            return
        monitor = get_log_monitor()
        self._execute_clean(folder, retention, "manual", monitor)

    def batch_delete(self, folder: str) -> None:
        if not self._validate_folder(folder):
            return
        monitor = get_log_monitor()
        self._execute_clean(folder, 0, "batch", monitor)

    def _execute_clean(self, folder: str, retention: int, mode: str, monitor) -> None:
        if self.cleaning_lock.locked():
            append_log(self.log_messages, "⏳ 另一個清理流程進行中，請稍候")
            return
        with self.cleaning_lock:
            if monitor:
                monitor.pause()
            try:
                self._clean_folder(folder, retention, mode)
            finally:
                if monitor:
                    monitor.resume()

    def _clean_folder(self, folder: str, retention: int, mode: str) -> None:
        now = time.time()
        removed, skipped, failed = [], [], []
        for name in os.listdir(folder):
            if not any(name.lower().endswith(ext) for ext in self.extensions):
                continue
            path = os.path.join(folder, name)
            try:
                age_hours = (now - os.path.getmtime(path)) / 3600
            except Exception as exc:  # pragma: no cover
                failed.append(f"{name}（讀取時間失敗：{exc}")
                continue
            need_remove = mode == "batch" or age_hours > retention
            if need_remove:
                try:
                    os.remove(path)
                    removed.append(name)
                except Exception as exc:  # pragma: no cover
                    failed.append(f"{name}（刪除失敗：{exc}")
            else:
                skipped.append(name)
        summary = (
            f"模式：{mode}｜刪除 {len(removed)} 筆，保留 {len(skipped)} 筆，失敗 {len(failed)} 筆"
        )
        append_log(self.log_messages, summary)
        if removed:
            append_log(self.log_messages, f"已刪除：{removed}")
        if failed:
            append_log(self.log_messages, f"發生錯誤：{failed}")
        append_log(self.log_messages, f"完成時間：{datetime.now():%Y-%m-%d %H:%M:%S}")


def get_data_cleaner() -> DataCleaner:
    if "cisco_data_cleaner" not in st.session_state:
        st.session_state["cisco_data_cleaner"] = DataCleaner()
    return st.session_state["cisco_data_cleaner"]


def app() -> None:
    """資料清理主頁面。"""
    cleaner = get_data_cleaner()
    monitor = get_log_monitor()

    st.title("🗑 資料清理模組")
    st.markdown("管理清洗資料夾內的暫存檔案，可設定自動清理排程。")

    folder = st.text_input("目標資料夾", value=monitor.settings.get("clean_csv_dir", ""))
    retention = st.number_input("保留小時數", min_value=1, max_value=168, value=3)
    interval = st.number_input("自動清理間隔（小時）", min_value=1, max_value=168, value=6)

    ext_input = st.text_input(
        "清理副檔名（以逗號分隔）",
        value=",".join(cleaner.extensions),
        help="例如：.csv,.png,.log",
    )
    extensions = [ext.strip() for ext in ext_input.split(",") if ext.strip()]
    cleaner.extensions = [ext if ext.startswith(".") else f".{ext}" for ext in extensions] or DEFAULT_EXTENSIONS

    col1, col2, col3 = st.columns(3)
    if cleaner.running:
        if col1.button("停止自動清理"):
            cleaner.stop_auto()
    else:
        if col1.button("啟動自動清理"):
            cleaner.start_auto(folder, int(retention), int(interval))
    if col2.button("立即手動清理"):
        cleaner.manual_clean(folder, int(retention))
    if col3.button("批次清空所有檔案"):
        cleaner.batch_delete(folder)

    st.markdown("### 清理日誌")
    st.text_area("清理狀態", value="\n".join(cleaner.log_messages), height=280)
