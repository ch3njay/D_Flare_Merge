"""Cisco 版本的 Log 監聽與自動清洗模組（Streamlit 版）。

此模組將原本集中於 PyQt5 介面的程式碼重構為 Streamlit 相容的寫法，
完整保留自動監聽、資料清洗、模型推論與通知串接的功能，並補強
執行緒控管與日誌呈現，方便在網頁化介面中維護與擴充。
"""
from __future__ import annotations

import html
import os
import shutil
import subprocess
import sys
import tempfile
import threading
import time
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

import pandas as pd
import streamlit as st

try:  # Prefer package-relative imports when available
    from ..training_pipeline.config import PipelineConfig
    from ..training_pipeline.trainer import execute_pipeline
    from ..notifier import notification_pipeline
    from ..utils_labels import append_log, load_json, save_json
except (ImportError, ValueError):  # Support running within the package directory directly
    from training_pipeline.config import PipelineConfig  # type: ignore[no-redef]
    from training_pipeline.trainer import execute_pipeline  # type: ignore[no-redef]
    from notifier import notification_pipeline  # type: ignore[no-redef]
    from utils_labels import append_log, load_json, save_json  # type: ignore[no-redef]

# 設定檔路徑與預設值定義
LOG_SETTINGS_FILE = "logfetcher_settings.json"
NOTIFIER_SETTINGS_FILE = "notifier_settings.txt"
DEFAULT_LOG_SETTINGS = {
    "save_dir": "",
    "binary_model_path": "",
    "model_path": "",
    "clean_csv_dir": "",
}
DEFAULT_NOTIFIER_SETTINGS = {
    "gemini_api_key": "",
    "line_channel_secret": "",
    "line_channel_access_token": "",
    "line_webhook_url": "",
    "discord_webhook_url": "",
}

PATH_BROWSER_ROOT = Path(tempfile.gettempdir()) / "df_cisco_paths"


class LogMonitor:
    """負責維護資料夾監控狀態與自動清洗流程的核心物件。"""

    def __init__(self) -> None:
        self.settings: Dict[str, str] = load_json(LOG_SETTINGS_FILE, DEFAULT_LOG_SETTINGS)
        self.log_messages: List[str] = []
        self.listening = False
        self.stop_event = threading.Event()
        self.monitor_thread: Optional[threading.Thread] = None
        self.socket_process: Optional[subprocess.Popen[str]] = None
        self.processed_files: Set[Tuple[str, int, float]] = set()
        self.notified_multiclass_files: Set[str] = set()
        self.last_file_checked = ""
        self.last_file_size = 0
        self.file_stable_count = 0
        self.last_processed_file = ""
        self.cleaning_lock = threading.Lock()
        self.latest_result: Optional[Dict[str, object]] = None
        self.paused = False
        self._last_folder_error: Optional[str] = None

    # ==== 狀態管理 ====
    def update_settings(self, **kwargs: str) -> None:
        """更新監控設定並立即寫入設定檔。"""
        self.settings.update({k: v.strip() for k, v in kwargs.items()})
        save_json(LOG_SETTINGS_FILE, self.settings)
        append_log(self.log_messages, "✅ 監控設定已儲存")

    def start_listening(self) -> None:
        """啟動資料夾監控與背景掃描執行緒。"""
        if self.listening:
            append_log(self.log_messages, "⚠️ 監聽已在執行中")
            return

        required = {
            "log 儲存資料夾": self.settings.get("save_dir", ""),
            "二元模型路徑": self.settings.get("binary_model_path", ""),
            "多元模型路徑": self.settings.get("model_path", ""),
            "清洗輸出資料夾": self.settings.get("clean_csv_dir", ""),
        }
        missing = [label for label, value in required.items() if not value]
        if missing:
            append_log(self.log_messages, f"❗ 缺少必要設定：{'、'.join(missing)}")
            return

        save_dir = required["log 儲存資料夾"]
        if not os.path.exists(save_dir):
            append_log(self.log_messages, f"❌ 監控資料夾不存在：{save_dir}")
            return
        if not os.access(save_dir, os.W_OK):
            append_log(self.log_messages, f"❌ 無法寫入監控資料夾：{save_dir}")
            return

        self.stop_event.clear()
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        self.listening = True
        append_log(self.log_messages, f"🟢 已啟動監聽，路徑：{save_dir}")
        self._start_socket_process(save_dir)

    def _start_socket_process(self, save_dir: str) -> None:
        """若專屬 socket 腳本存在則同步啟動子程序。"""
        script_path = os.path.join(os.getcwd(), "socket_5.py")
        if not os.path.exists(script_path):
            append_log(self.log_messages, "ℹ️ 找不到 socket_5.py，僅啟動資料夾監控。")
            return
        try:
            self.socket_process = subprocess.Popen(
                [sys.executable, script_path, save_dir],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
            )
            append_log(self.log_messages, "🚀 已啟動 socket_5.py 子程序")
            threading.Thread(target=self._capture_socket_output, daemon=True).start()
        except Exception as exc:
            append_log(self.log_messages, f"❌ 無法啟動 socket 子程序：{exc}")
            self.socket_process = None

    def _capture_socket_output(self) -> None:
        """持續讀取 socket 子程序輸出並記錄於日誌。"""
        if not self.socket_process or not self.socket_process.stdout:
            return
        for line in self.socket_process.stdout:
            line = line.strip()
            if line:
                append_log(self.log_messages, f"[socket] {line}")
        append_log(self.log_messages, "🛑 socket 子程序已結束")

    def stop_listening(self) -> None:
        """停止監控與所有背景工作。"""
        if not self.listening:
            append_log(self.log_messages, "⚠️ 尚未啟動監聽")
            return
        self.stop_event.set()
        if self.monitor_thread and self.monitor_thread.is_alive():
            self.monitor_thread.join(timeout=3)
        self.monitor_thread = None
        self.listening = False
        append_log(self.log_messages, "⛔ 已停止監聽")

        if self.socket_process:
            try:
                self.socket_process.terminate()
                self.socket_process.wait(timeout=3)
                append_log(self.log_messages, "🛑 socket 子程序已終止")
            except Exception as exc:
                append_log(self.log_messages, f"⚠️ socket 子程序終止失敗：{exc}")
            finally:
                self.socket_process = None

    # ==== 資料夾掃描邏輯 ====
    def _monitor_loop(self) -> None:
        """背景執行緒：每 5 秒掃描一次資料夾。"""
        while not self.stop_event.is_set():
            if not self.paused:
                self._inspect_folder()
            time.sleep(5)

    def _inspect_folder(self, manual: bool = False) -> None:
        """掃描資料夾，若找到穩定的最新檔案便啟動自動清洗。"""
        folder = self.settings.get("save_dir", "").strip()
        if not folder:
            if manual:
                append_log(self.log_messages, "⚠️ 請先設定 log 儲存資料夾")
            return
        if not os.path.isdir(folder):
            if manual or self._last_folder_error != folder:
                append_log(self.log_messages, f"❗ 監控資料夾不存在：{folder}")
                self._last_folder_error = folder
            return
        self._last_folder_error = None

        try:
            files = [
                f
                for f in os.listdir(folder)
                if f.endswith(".csv") and f.startswith("asa_logs_") and "_result" not in f
            ]
        except Exception as exc:
            append_log(self.log_messages, f"❌ 無法讀取資料夾：{exc}")
            return

        if not files:
            if manual:
                append_log(self.log_messages, "ℹ️ 目前資料夾沒有新的 log 檔案")
            return

        files.sort(key=lambda name: os.path.getmtime(os.path.join(folder, name)), reverse=True)
        latest_file = os.path.join(folder, files[0])
        current_size = os.path.getsize(latest_file) if os.path.exists(latest_file) else 0
        now = time.time()

        # 移除超過一小時的紀錄
        self.processed_files = {
            item for item in self.processed_files if now - item[2] < 3600
        }
        if any(item[0] == latest_file and item[1] == current_size for item in self.processed_files):
            return

        if latest_file != self.last_file_checked:
            self.last_file_checked = latest_file
            self.last_file_size = current_size
            self.file_stable_count = 1
            append_log(self.log_messages, f"🆕 偵測到新檔案：{latest_file}，等待大小穩定")
            return

        if current_size == self.last_file_size:
            self.file_stable_count += 1
            append_log(self.log_messages, f"📈 檔案大小連續第 {self.file_stable_count} 次穩定：{current_size} bytes")
        else:
            self.file_stable_count = 1
            self.last_file_size = current_size
            append_log(self.log_messages, f"🔁 檔案大小變動為 {current_size}，重新計數")
            return

        if self.file_stable_count >= 2:
            self.last_processed_file = latest_file
            self.processed_files.add((latest_file, current_size, now))
            append_log(self.log_messages, f"🚀 檔案穩定，準備自動分析：{latest_file}")
            self._launch_auto_clean(latest_file)

    def scan_once(self) -> None:
        """供 UI 手動觸發一次資料夾掃描。"""
        append_log(self.log_messages, "🔍 手動觸發資料夾掃描")
        self._inspect_folder(manual=True)

    # ==== 自動清洗與推論 ====
    def _launch_auto_clean(self, file_path: str) -> None:
        if self.cleaning_lock.locked():
            append_log(self.log_messages, "⏳ 前一次自動分析尚未完成，略過本次觸發")
            return
        threading.Thread(target=self._run_auto_clean, args=(file_path,), daemon=True).start()

    def _run_auto_clean(self, file_path: str) -> None:
        with self.cleaning_lock:
            append_log(self.log_messages, "⚙️ 開始執行自動清洗與推論流程")
            binary_model = self.settings.get("binary_model_path", "").strip()
            multi_model = self.settings.get("model_path", "").strip()
            output_dir = self.settings.get("clean_csv_dir", "").strip()

            missing = []
            if not binary_model:
                missing.append("二元模型")
            if not multi_model:
                missing.append("多元模型")
            if not output_dir:
                missing.append("清洗輸出資料夾")
            if not os.path.exists(file_path):
                missing.append("log 檔案")
            if missing:
                append_log(self.log_messages, f"❌ 自動分析缺少必要項目：{'、'.join(missing)}")
                return

            os.makedirs(output_dir, exist_ok=True)

            try:
                config = PipelineConfig(
                    raw_log_path=file_path,
                    binary_model_path=binary_model,
                    multiclass_model_path=multi_model,
                    output_dir=output_dir,
                    show_progress=False,
                )
                result = execute_pipeline(config)
                self.latest_result = result
                append_log(
                    self.log_messages,
                    f"✅ 自動分析完成，輸出 CSV：{result.get('binary_output_csv', '-')}",
                )
                if result.get("binary_output_pie"):
                    append_log(
                        self.log_messages,
                        f"📊 二元圓餅圖：{result.get('binary_output_pie')}",
                    )
                if result.get("multiclass_output_csv"):
                    append_log(
                        self.log_messages,
                        f"📊 多元結果：{result.get('multiclass_output_csv')}",
                    )
                self._handle_auto_notification(result)
            except Exception as exc:  # pragma: no cover - 盡量避免中斷
                append_log(self.log_messages, f"❌ 自動分析失敗：{exc}")

    def _handle_auto_notification(self, result: Dict[str, object]) -> None:
        """根據多元結果啟動通知模組。"""
        multi_csv = result.get("multiclass_output_csv")
        if not multi_csv:
            append_log(self.log_messages, "ℹ️ 本批次無攻擊流量，未產生多元結果")
            return
        if not isinstance(multi_csv, str) or not os.path.exists(multi_csv):
            append_log(self.log_messages, f"⚠️ 找不到多元結果檔案：{multi_csv}")
            return
        if multi_csv in self.notified_multiclass_files:
            append_log(self.log_messages, "ℹ️ 該多元結果已推播過，略過重複通知")
            return

        try:
            df = pd.read_csv(multi_csv)
        except Exception as exc:
            append_log(self.log_messages, f"❌ 讀取多元結果失敗：{exc}")
            return

        if "Severity" not in df.columns:
            append_log(self.log_messages, "ℹ️ 多元結果缺少 Severity 欄位，無法自動推播")
            return
        if not df["Severity"].astype(str).isin(["1", "2", "3"]).any():
            append_log(self.log_messages, "ℹ️ 本批次無高風險事件，未啟動推播")
            return

        settings = load_json(NOTIFIER_SETTINGS_FILE, DEFAULT_NOTIFIER_SETTINGS)
        append_log(self.log_messages, "🔔 偵測到高風險事件，啟動通知模組")
        group_fields = settings.get("convergence_fields", ["source", "destination"])
        if not isinstance(group_fields, list):
            group_fields = ["source", "destination"]
        convergence_cfg = {
            "window_minutes": int(settings.get("convergence_window_minutes", 10) or 10),
            "group_fields": group_fields,
        }
        notification_pipeline(
            result_csv=multi_csv,
            gemini_api_key=settings.get("gemini_api_key", ""),
            line_channel_access_token=settings.get("line_channel_access_token", ""),
            line_webhook_url=settings.get("line_webhook_url", ""),
            discord_webhook_url=settings.get("discord_webhook_url", ""),
            ui_callback=lambda msg: append_log(self.log_messages, msg),
            convergence_config=convergence_cfg,
        )
        self.notified_multiclass_files.add(multi_csv)

    # ==== 供資料清理模組呼叫的暫停控制 ====
    def pause(self) -> None:
        if not self.paused:
            self.paused = True
            append_log(self.log_messages, "⏸️ 主流程已暫停，等待資料清理完成")

    def resume(self) -> None:
        if self.paused:
            self.paused = False
            append_log(self.log_messages, "▶️ 主流程已恢復")

    def manual_auto_clean(self, file_path: str) -> None:
        """供 UI 手動指定檔案並觸發自動分析。"""
        if not file_path:
            append_log(self.log_messages, "⚠️ 請輸入要分析的 log 檔案路徑")
            return
        if not os.path.exists(file_path):
            append_log(self.log_messages, f"❌ 指定檔案不存在：{file_path}")
            return
        self.last_processed_file = file_path
        self._launch_auto_clean(file_path)


def get_log_monitor() -> LogMonitor:
    """取得儲存在 Streamlit session 中的 LogMonitor 單例。"""
    if "cisco_log_monitor" not in st.session_state:
        st.session_state["cisco_log_monitor"] = LogMonitor()
    return st.session_state["cisco_log_monitor"]


def _persist_uploaded_model(uploaded_file, prefix: str) -> str:
    """儲存使用者上傳的模型檔案並回傳路徑。"""

    store = Path(tempfile.gettempdir()) / "cisco_model_store"
    store.mkdir(parents=True, exist_ok=True)
    original_name = getattr(uploaded_file, "name", f"{prefix}.pkl") or f"{prefix}.pkl"
    suffix = Path(original_name).suffix or ".pkl"
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    target_path = store / f"{prefix}_{timestamp}{suffix}"

    uploaded_file.seek(0)
    with open(target_path, "wb") as destination:
        destination.write(uploaded_file.getbuffer())

    return str(target_path)


def _render_path_preview(label: str, path: str, *, icon: str = "📁") -> None:
    """使用統一樣式呈現路徑資訊。"""

    safe_label = html.escape(label)
    safe_icon = html.escape(icon)
    if path:
        display_path = html.escape(path)
        extra_class = ""
    else:
        display_path = "尚未選擇"
        extra_class = " path-preview--empty"

    st.markdown(
        f"""
        <div class="path-preview{extra_class}">
            <span class="path-preview__icon">{safe_icon}</span>
            <div class="path-preview__content">
                <span class="path-preview__label">{safe_label}</span>
                <span class="path-preview__path">{display_path}</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _persist_uploaded_manual_file(uploaded_file, monitor: LogMonitor) -> str:
    """將使用者上傳的手動分析檔案落地保存並回傳路徑。"""

    base_dir = monitor.settings.get("save_dir", "")
    if base_dir and os.path.isdir(base_dir):
        target_dir = Path(base_dir)
    else:
        target_dir = Path(tempfile.gettempdir()) / "cisco_manual_logs"
    target_dir.mkdir(parents=True, exist_ok=True)

    timestamp = time.strftime("%Y%m%d_%H%M%S")
    original_name = Path(getattr(uploaded_file, "name", "uploaded.log") or "uploaded.log").name
    safe_name = original_name.replace(" ", "_")
    target_path = target_dir / f"manual_{timestamp}_{safe_name}"

    uploaded_file.seek(0)
    with open(target_path, "wb") as destination:
        destination.write(uploaded_file.getbuffer())

    return str(target_path)


def render_directory_selector(
    label: str,
    state_key: str,
    *,
    default: str = "",
    help_text: str | None = None,
) -> str:
    """提供使用者以瀏覽按鈕或手動輸入設定資料夾路徑。"""

    session_key = f"{state_key}_path"
    display_key = f"{session_key}_display"
    PATH_BROWSER_ROOT.mkdir(parents=True, exist_ok=True)

    if session_key not in st.session_state:
        st.session_state[session_key] = default.strip()
    if display_key not in st.session_state:
        st.session_state[display_key] = st.session_state[session_key]

    current_path = st.session_state[session_key]
    with st.container():
        st.text_input(
            label,
            value=st.session_state[display_key],
            key=display_key,
            disabled=True,
            placeholder="使用下方瀏覽按鈕選擇資料夾",
        )
        uploaded_files = st.file_uploader(
            "瀏覽",
            key=f"{session_key}_uploader",
            label_visibility="collapsed",
            accept_multiple_files=True,
            help=help_text
            or "透過瀏覽按鈕挑選資料夾中的檔案，系統會建立可監控的目錄。",
        )

    if uploaded_files:
        target_dir = PATH_BROWSER_ROOT / state_key
        if target_dir.exists():
            shutil.rmtree(target_dir)
        target_dir.mkdir(parents=True, exist_ok=True)
        for file_obj in uploaded_files:
            file_obj.seek(0)
            destination = target_dir / file_obj.name
            with open(destination, "wb") as handle:
                handle.write(file_obj.getbuffer())
        current_path = str(target_dir)
        st.session_state[session_key] = current_path
        st.session_state[display_key] = current_path
        st.success(f"已建立瀏覽資料夾：{current_path}")

    manual_key = f"{session_key}_manual"
    with st.expander("需要手動輸入路徑？", expanded=False):
        manual_value = st.text_input(
            "手動輸入自訂路徑",
            value=st.session_state.get(manual_key, st.session_state[session_key]),
            key=manual_key,
        )
        manual_value = manual_value.strip()
        if manual_value and manual_value != st.session_state[session_key]:
            st.session_state[session_key] = manual_value
            st.session_state[display_key] = manual_value
            current_path = manual_value

    return st.session_state.get(session_key, current_path)


def app() -> None:
    """Streamlit 版的 Log 擷取頁面。"""
    monitor = get_log_monitor()

    st.title("📄 Cisco Log 擷取與自動分析")
    st.markdown("此頁面負責監控 ASA log、執行資料清洗與自動推播。")

    st.session_state.setdefault("cisco_binary_model_path", monitor.settings.get("binary_model_path", ""))
    st.session_state.setdefault("cisco_multi_model_path", monitor.settings.get("model_path", ""))

    st.subheader("監控設定")
    with st.form("log_settings"):
        col_paths = st.columns(2)
        with col_paths[0]:
            save_dir = render_directory_selector(
                "log 儲存資料夾",
                "cisco_save_dir",
                default=monitor.settings.get("save_dir", ""),
                help_text="透過瀏覽按鈕選擇欲監控的資料夾，系統會建立可供監聽的目錄。",
            )
        with col_paths[1]:
            clean_dir = render_directory_selector(
                "清洗輸出資料夾",
                "cisco_clean_dir",
                default=monitor.settings.get("clean_csv_dir", ""),
                help_text="透過瀏覽按鈕建立或選擇清洗輸出的目錄，亦可於下方展開手動調整。",
            )

        st.markdown("##### 模型檔案")
        current_binary = st.session_state.get(
            "cisco_binary_model_path", monitor.settings.get("binary_model_path", "")
        )
        binary_upload = st.file_uploader(
            "選擇二元模型檔 (.pkl/.joblib)",
            type=["pkl", "joblib"],
            key="cisco_binary_model_upload",
            help="透過瀏覽按鈕挑選二元分類模型，將自動儲存並套用於監控流程。",
        )
        _render_path_preview("目前使用的二元模型", current_binary, icon="🧠")

        current_multi = st.session_state.get(
            "cisco_multi_model_path", monitor.settings.get("model_path", "")
        )
        multi_upload = st.file_uploader(
            "選擇多元模型檔 (.pkl/.joblib)",
            type=["pkl", "joblib"],
            key="cisco_multi_model_upload",
            help="透過瀏覽按鈕挑選多元分類模型，將自動儲存並套用於監控流程。",
        )
        _render_path_preview("目前使用的多元模型", current_multi, icon="🗂️")

        submitted = st.form_submit_button("💾 儲存設定")
        if submitted:
            binary_path = current_binary
            multi_path = current_multi
            if binary_upload is not None:
                binary_path = _persist_uploaded_model(binary_upload, "binary_model")
            if multi_upload is not None:
                multi_path = _persist_uploaded_model(multi_upload, "multiclass_model")

            st.session_state["cisco_binary_model_path"] = binary_path
            st.session_state["cisco_multi_model_path"] = multi_path
            monitor.update_settings(
                save_dir=save_dir,
                binary_model_path=binary_path,
                model_path=multi_path,
                clean_csv_dir=clean_dir,
            )
            st.success("監控設定已更新")

    col1, col2, col3 = st.columns(3)
    if col1.button("▶️ 啟動監聽", use_container_width=True):
        monitor.start_listening()
    if col2.button("⏹️ 停止監聽", use_container_width=True):
        monitor.stop_listening()
    if col3.button("🔁 手動掃描一次", use_container_width=True):
        monitor.scan_once()

    st.markdown("### 手動分析")
    manual_path = st.session_state.get("cisco_manual_uploaded_path", monitor.last_processed_file)
    uploaded_manual = st.file_uploader(
        "選擇要分析的 log 檔案",
        type=["log", "txt", "csv"],
        accept_multiple_files=False,
        help="透過瀏覽按鈕挑選 ASA log，系統會自動儲存並帶入分析流程。",
        key="cisco_manual_file_uploader",
    )
    if uploaded_manual is not None:
        manual_path = _persist_uploaded_manual_file(uploaded_manual, monitor)
        st.session_state["cisco_manual_uploaded_path"] = manual_path
        monitor.last_processed_file = manual_path
        st.success(f"已準備檔案：{manual_path}")

    _render_path_preview("目前選擇的檔案", manual_path or "", icon="📄")
    if not manual_path:
        st.caption("請先透過上方瀏覽按鈕選擇欲分析的檔案。")

    if st.button("⚙️ 立即執行自動分析", use_container_width=True):
        if manual_path:
            monitor.manual_auto_clean(manual_path)
        else:
            st.warning("請先選擇要分析的檔案。")

    st.markdown("### 監控狀態")
    status = "🟢 監聽中" if monitor.listening else "⛔ 已停止"
    st.markdown(f"目前狀態：**{status}**")
    if monitor.latest_result:
        st.success("顯示最新自動分析結果：")
        st.json(monitor.latest_result)

    st.markdown("### 執行日誌")
    st.text_area(
        "執行日誌",
        value="\n".join(monitor.log_messages),
        height=320,
    )
