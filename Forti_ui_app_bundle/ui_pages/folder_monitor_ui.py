import os
import time
import io
import re
import contextlib
import threading
from pathlib import Path

import pandas as pd
import joblib
import streamlit as st
from . import apply_dark_theme  # [ADDED]

try:
    from streamlit_autorefresh import st_autorefresh
except ModuleNotFoundError:  # pragma: no cover - optional dependency
    st_autorefresh = None

from ..etl_pipeliner import run_pipeline
from ..etl_pipeline import log_cleaning as LC
from ..notifier import notify_from_csv


def _rerun() -> None:
    """Trigger a Streamlit rerun across versions."""
    rerun = getattr(st, "rerun", getattr(st, "experimental_rerun", None))
    if rerun is not None:  # pragma: no branch
        rerun()


try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler
except Exception:  # pragma: no cover - watchdog may not be installed
    Observer = None
    FileSystemEventHandler = object


class _FileMonitorHandler(FileSystemEventHandler):
    """Watchdog handler that records supported file events."""

    SUPPORTED_EXTS = (
        ".csv",
        ".txt",
        ".log",
        ".csv.gz",
        ".txt.gz",
        ".log.gz",
        ".zip",
    )
    
    # ETL 產生的檔案後綴，應該被過濾掉（更嚴格的過濾）
    ETL_SUFFIXES = (
        "_clean.csv",
        "_preprocessed.csv", 
        "_engineered.csv",
        "_result.csv",
        "_processed.csv",
        "_output.csv",
        "_report.csv",
        "_mapping_report.json",
        # 也過濾壓縮版本
        "_clean.csv.gz",
        "_preprocessed.csv.gz",
        "_engineered.csv.gz",
        "_result.csv.gz",
        "_processed.csv.gz",
        "_output.csv.gz",
        "_report.csv.gz",
    )

    def __init__(self):
        self.events = []
        self.processed_files = set()  # 已處理的檔案集合
        self.event_signatures = set()  # 追蹤事件簽章避免重複
        self.monitor_thread = None
        self.stop_event = threading.Event()
        self.folder_path = None
        self.use_watchdog = True
        self.log_messages = []

    def _is_etl_generated_file(self, path: str) -> bool:
        """檢查檔案是否為 ETL 產生的中間檔案"""
        path_lower = path.lower()
        # 檢查檔案名稱中是否包含 ETL 後綴
        for suffix in self.ETL_SUFFIXES:
            if suffix in path_lower:
                return True
        return False
    
    def _is_already_processed(self, path: str) -> bool:
        """檢查檔案是否已被處理過"""
        # 使用檔案路徑和修改時間作為唯一標識
        try:
            stat = os.stat(path)
            file_key = f"{path}_{stat.st_mtime}_{stat.st_size}"
            return file_key in self.processed_files
        except OSError:
            return False
    
    def _mark_as_processed(self, path: str) -> None:
        """標記檔案為已處理"""
        try:
            stat = os.stat(path)
            file_key = f"{path}_{stat.st_mtime}_{stat.st_size}"
            self.processed_files.add(file_key)
        except OSError:
            pass

    def _should_process_file(self, path: str) -> bool:
        """判斷檔案是否應該被處理"""
        # 先過濾 ETL 產生的檔案（最高優先級）
        if self._is_etl_generated_file(path):
            return False
        
        # 檢查副檔名
        if not path.lower().endswith(self.SUPPORTED_EXTS):
            return False
            
        # 檢查是否已處理過
        if self._is_already_processed(path):
            return False
            
        return True

    def _track(self, event_type: str, path: str) -> None:
        """Record events for supported files that should be processed."""
        # 建立事件簽章避免短時間內的重複事件
        event_sig = f"{event_type}:{path}"
        if event_sig in self.event_signatures:
            return
            
        if self._should_process_file(path):
            self.events.append((event_type, path))
            self._mark_as_processed(path)
            self.event_signatures.add(event_sig)
            # 定期清理舊的事件簽章（保留最近 1000 個）
            if len(self.event_signatures) > 1000:
                self.event_signatures = set(list(self.event_signatures)[-500:])

    def on_created(self, event):  # pragma: no cover - filesystem events
        if not event.is_directory:
            self._track("created", event.src_path)

    def on_modified(self, event):  # pragma: no cover - filesystem events
        if not event.is_directory:
            self._track("modified", event.src_path)

    def start_monitoring(self, folder_path: str, use_watchdog: bool = True):
        """開始監控指定資料夾"""
        self.folder_path = folder_path
        self.use_watchdog = use_watchdog
        self.stop_event.clear()
        
        if self.monitor_thread is None or not self.monitor_thread.is_alive():
            self.monitor_thread = threading.Thread(
                target=self._monitor_loop,
                daemon=True,
                name="FortiFileMonitor"
            )
            self.monitor_thread.start()
            self.log_messages.append(f"✅ 開始監控資料夾: {folder_path}")
            return True
        return False

    def stop_monitoring(self):
        """停止監控"""
        self.stop_event.set()
        if self.monitor_thread and self.monitor_thread.is_alive():
            self.monitor_thread.join(timeout=5.0)
        self.log_messages.append("⏹️ 監控已停止")

    def _monitor_loop(self):
        """持續監控循環 - 支援長時間運行"""
        sleep_interval = 5  # 每5秒檢查一次
        cleanup_counter = 0
        
        self.log_messages.append("🔄 監控循環啟動")
        
        while not self.stop_event.is_set():
            try:
                if self.use_watchdog:
                    # Watchdog 模式：處理累積的事件
                    self._process_watchdog_events()
                else:
                    # 輪詢模式：掃描資料夾
                    self._inspect_folder()
                
                # 每10次循環清理一次舊記錄
                cleanup_counter += 1
                if cleanup_counter >= 10:
                    self._cleanup_old_records()
                    cleanup_counter = 0
                
                # 可中斷的睡眠
                for _ in range(sleep_interval):
                    if self.stop_event.is_set():
                        break
                    time.sleep(1)
                    
            except Exception as e:
                self.log_messages.append(f"監控循環錯誤：{e}")
                time.sleep(5)  # 錯誤恢復等待
        
        self.log_messages.append("🏁 監控循環結束")

    def _process_watchdog_events(self):
        """處理 Watchdog 累積的事件"""
        if not self.events:
            return
        
        new_events = [event for event in self.events if self._should_process_event(event)]
        
        for event_type, path in new_events:
            if self.stop_event.is_set():
                break
                
            try:
                if os.path.exists(path) and self._is_file_stable(path):
                    self._process_single_file(path)
            except Exception as e:
                self.log_messages.append(f"處理檔案錯誤 {path}: {e}")

    def _inspect_folder(self):
        """輪詢模式：掃描資料夾中的新檔案"""
        if not self.folder_path or not os.path.exists(self.folder_path):
            return
        
        try:
            for file_path in Path(self.folder_path).rglob("*"):
                if self.stop_event.is_set():
                    break
                    
                if (file_path.is_file() and 
                    self._should_process_file(str(file_path)) and
                    self._is_file_stable(str(file_path))):
                    
                    self._process_single_file(str(file_path))
                    
        except Exception as e:
            self.log_messages.append(f"資料夾掃描錯誤：{e}")

    def _should_process_event(self, event):
        """檢查事件是否應該處理"""
        event_type, path = event
        return (os.path.exists(path) and 
                self._should_process_file(path) and
                not self._is_already_processed(path))

    def _is_file_stable(self, path: str, stable_seconds: int = 3) -> bool:
        """檢查檔案是否穩定（未在寫入中）"""
        try:
            return time.time() - os.path.getmtime(path) > stable_seconds
        except OSError:
            return False

    def _process_single_file(self, path: str):
        """處理單個檔案 - 添加到事件佇列供外部處理"""
        try:
            # 檢查是否已在事件佇列中
            event_exists = any(event[1] == path for event in self.events if len(event) >= 2)
            if not event_exists:
                # 添加到事件佇列，讓外部的 _process_events 函數處理
                self.events.append(("file_detected", path, time.time()))
                self.log_messages.append(f"📁 發現新檔案: {os.path.basename(path)}")
                
                # 觸發 Streamlit 重新整理以處理新事件
                if hasattr(st, 'rerun'):
                    # 使用非阻塞方式通知有新事件
                    pass
                
        except Exception as e:
            self.log_messages.append(f"檔案偵測失敗 {path}: {e}")
            
    def trigger_event_processing(self):
        """觸發事件處理 - 供外部呼叫"""
        return len(self.events) > 0

    def _cleanup_old_records(self):
        """清理舊記錄，避免記憶體洩漏"""
        current_time = time.time()
        
        # 清理 24 小時前的事件
        self.events = [
            event for event in self.events 
            if hasattr(event, '__len__') and len(event) >= 3 and 
            current_time - event[2] < 86400
        ] if hasattr(self.events[0] if self.events else None, '__len__') else self.events
        
        # 保留最近 1000 個處理記錄
        if len(self.processed_files) > 1000:
            processed_list = list(self.processed_files)
            self.processed_files = set(processed_list[-1000:])
        
        # 保留最近 500 個事件簽章
        if len(self.event_signatures) > 500:
            signatures_list = list(self.event_signatures)
            self.event_signatures = set(signatures_list[-500:])
        
        # 保留最近 100 條日誌訊息
        if len(self.log_messages) > 100:
            self.log_messages = self.log_messages[-100:]

    def get_status(self):
        """取得監控狀態資訊"""
        is_running = (self.monitor_thread and 
                     self.monitor_thread.is_alive() and 
                     not self.stop_event.is_set())
        
        return {
            'is_running': is_running,
            'folder_path': self.folder_path or 'N/A',
            'use_watchdog': self.use_watchdog,
            'processed_count': len(self.processed_files),
            'pending_events': len(self.events),
            'method': 'Watchdog (即時)' if self.use_watchdog else '輪詢 (定期)',
            'last_messages': self.log_messages[-5:] if self.log_messages else []
        }


ANSI_RE = re.compile(r"\x1b\[[0-9;]*[A-Za-z]")


def _log_toast(msg: str) -> None:
    """Append *msg* to log and show a toast if supported."""
    st.session_state.log_lines.append(msg)
    if hasattr(st, "toast"):
        st.toast(msg)
    else:  # pragma: no cover - toast not available
        st.write(msg)


def _run_etl_and_infer(
    path: str, progress_bar, status_placeholder, 
    handler: _FileMonitorHandler = None
) -> None:
    """Run ETL pipeline and model inference on *path*.

    Parameters
    ----------
    path: str
        The path to the file being processed.
    progress_bar: streamlit.delta_generator.DeltaGenerator
        Progress bar widget used for simple progress feedback.
    status_placeholder: streamlit.delta_generator.DeltaGenerator
        Placeholder used to display textual status updates to the user.
    handler: _FileMonitorHandler, optional
        The file monitor handler to mark generated files as processed.
    """
    bin_model = st.session_state.get("binary_model")
    mul_model = st.session_state.get("multi_model")
    if not (bin_model and mul_model):
        status_placeholder.text("Models not uploaded; skipping")
        st.session_state.log_lines.append("Models not uploaded; skipping")
        return

    p = Path(path)
    while p.suffix in {".gz", ".zip"}:
        p = p.with_suffix("")

    ext = p.suffix.lower()
    stem = p.stem.lower()

    clean_csv = path
    do_map = True
    do_fe = True

    if ext in {".txt", ".log"}:
        clean_csv = str(p.with_name(p.stem + "_clean.csv"))

        _log_toast("Running cleaning for raw log")
        LC.clean_logs(quiet=True, paths=[path], clean_csv=clean_csv)
    else:
        clean_csv = path
        if stem.endswith("_engineered"):
            do_map = False
            do_fe = False
        elif stem.endswith("_preprocessed"):
            do_map = False
            do_fe = True

    base = p.with_suffix("")
    pre_csv = clean_csv if not do_map else f"{base}_preprocessed.csv"
    fe_csv = pre_csv if not do_fe else f"{base}_engineered.csv"

    try:
        status_placeholder.text(f"Detected new file: {path}")
        _log_toast(f"Detected new file: {path}")
        buf = io.StringIO()
        status_placeholder.text("Running ETL pipeline...")
        with contextlib.redirect_stdout(buf):
            run_pipeline(
                do_clean=False,
                do_map=do_map,
                do_fe=do_fe,
                clean_out=clean_csv,
                preproc_out=pre_csv,
                fe_out=fe_csv,
            )
        for line in ANSI_RE.sub("", buf.getvalue()).splitlines():
            if line.strip():
                st.session_state.log_lines.append(line.strip())



        # feature engineered data for model inference

        df = pd.read_csv(fe_csv)
        if df.isna().any().any():
            _log_toast("Detected NaNs; filling with 0")
            df.fillna(0, inplace=True)


        # original data retained for notification context
        raw_df = pd.read_csv(clean_csv)
        if raw_df.isna().any().any():
            fill_values = {
                col: 0 if pd.api.types.is_numeric_dtype(raw_df[col]) else ""
                for col in raw_df.columns
            }
            raw_df.fillna(value=fill_values, inplace=True)


        features = [c for c in df.columns if c not in {"is_attack", "crlevel"}]

        bin_clf = bin_model
        bin_features = list(getattr(bin_clf, "feature_names_in_", features))
        missing = [f for f in bin_features if f not in df.columns]
        if missing:
            _log_toast(f"Missing features for binary model: {missing}; filling with 0")
        df_bin = df.reindex(columns=bin_features, fill_value=0)

        status_placeholder.text("Running binary classification...")
        _log_toast("Running binary classification")
        bin_pred = bin_clf.predict(df_bin)
        result = raw_df.copy()

        result["is_attack"] = bin_pred
        result["crlevel"] = 0
        mask = result["is_attack"] == 1
        _log_toast(f"Binary classification found {mask.sum()} attack rows")
        if mask.any():
            mul_clf = mul_model
            mul_features = list(getattr(mul_clf, "feature_names_in_", features))
            missing_mul = [f for f in mul_features if f not in df.columns]
            if missing_mul:
                _log_toast(
                    f"Missing features for multiclass model: {missing_mul}; filling with 0"
                )
            df_mul = df.loc[mask].reindex(columns=mul_features, fill_value=0)

            status_placeholder.text(
                "Running multiclass classification for attack rows..."
            )
            _log_toast("Running multiclass classification for attack rows")
            result.loc[mask, "crlevel"] = mul_clf.predict(df_mul)
        else:
            status_placeholder.text(
                "No attacks detected; skipping multiclass classification"
            )
            _log_toast("No attacks detected; skipping multiclass classification")


        report_path = f"{base}_report.csv"
        result.to_csv(report_path, index=False)
        gen_files = {report_path}
        for f in (clean_csv, pre_csv, fe_csv):
            if f != path:
                gen_files.add(f)
        st.session_state.generated_files.update(gen_files)
        webhook = st.session_state.get("discord_webhook", "")
        gemini_key = st.session_state.get("gemini_key", "")
        line_token = st.session_state.get("line_token", "")
        convergence = st.session_state.get(
            "forti_convergence", {"window_minutes": 10, "group_fields": ["source", "destination"]}
        )


        def _log(msg: str) -> None:
            st.session_state.log_lines.append(msg)
            st.write(msg)

        # 根據用戶設定決定是否啟用通知和視覺化更新
        enable_notifications = st.session_state.get("enable_notifications", True)
        enable_visualization_sync = st.session_state.get("enable_visualization_sync", True)
        
        if enable_notifications:
            notify_from_csv(
                report_path,
                webhook,
                gemini_key,
                risk_levels={"3", "4"},
                ui_log=_log,
                line_token=line_token,
                convergence=convergence,
            )

        # store counts for visualization
        st.session_state.last_counts = {
            "is_attack": result["is_attack"].value_counts().reindex([0, 1], fill_value=0),
            "crlevel": result["crlevel"].value_counts().reindex([0, 1, 2, 3, 4], fill_value=0),
        }
        st.session_state.last_critical = result[result["crlevel"] >= 4]
        st.session_state.last_report_path = report_path
        
        # 觸發視覺化同步更新
        if enable_visualization_sync:
            st.session_state.visualization_needs_update = True
            st.session_state.visualization_last_update = time.time()

        status_placeholder.text(f"Processed {path} -> {report_path}")
        _log_toast(f"Processed {path} -> {report_path}")
        
        # 如果有 handler，將 ETL 產生的檔案標記為已處理，避免重複處理
        if handler:
            for generated_file in gen_files:
                handler._mark_as_processed(generated_file)
        
        for pct in range(0, 101, 20):
            progress_bar.progress(pct)
            time.sleep(0.05)
    except Exception as exc:  # pragma: no cover - processing errors
        _log_toast(f"Processing failed {path}: {exc}")


def _cleanup_generated(hours: int, *, force: bool = False) -> None:
    """Remove generated files older than *hours* or all if *force* is True."""
    now = time.time()
    to_remove = []
    for f in list(st.session_state.get("generated_files", set())):
        try:
            if force or now - os.path.getmtime(f) > hours * 3600:
                os.remove(f)
                to_remove.append(f)
        except OSError:
            to_remove.append(f)
    for f in to_remove:
        st.session_state.generated_files.discard(f)
        st.session_state.log_lines.append(f"Removed {f}")


def _process_events(handler: _FileMonitorHandler, progress_bar, status_placeholder) -> None:
    """Process newly detected files."""
    # 獲取上次處理的事件數量
    last_processed_count = len(st.session_state.get("processed_events", []))
    new_events = handler.events[last_processed_count:]
    
    # 如果沒有新事件，直接返回
    if not new_events:
        return
    
    processed_in_this_batch = 0
    for event_type, path in new_events:
        # 多層檢查避免重複處理
        
        # 1. 檢查是否為 ETL 產生的檔案
        if handler._is_etl_generated_file(path):
            continue
        
        # 2. 檢查是否在 generated_files 集合中
        if path in st.session_state.get("generated_files", set()):
            continue
        
        # 3. 檢查是否在 processed_files 集合中
        if path in st.session_state.get("processed_files", set()):
            continue
        
        # 4. 檢查檔案是否存在且穩定（避免處理正在寫入的檔案）
        try:
            if not os.path.exists(path):
                continue
            # 等待檔案穩定（最近 5 秒內未修改）
            if time.time() - os.path.getmtime(path) < 5:
                continue
        except OSError:
            continue
        
        # 處理檔案
        try:
            _run_etl_and_infer(path, progress_bar, status_placeholder, handler)
            st.session_state.setdefault("processed_files", set()).add(path)
            processed_in_this_batch += 1
        except Exception as exc:
            _log_toast(f"Error processing {path}: {exc}")
    
    # 更新已處理事件記錄
    st.session_state.processed_events = handler.events[:]
    
    # 記錄處理統計
    if processed_in_this_batch > 0:
        _log_toast(f"Processed {processed_in_this_batch} new file(s) in this batch")

def app() -> None:
    apply_dark_theme()  # [ADDED]
    st.title("Folder Monitor")
    st.info(
        "Select a folder to monitor for CSV/TXT/log files including compressed "
        "formats (.gz, .zip). Files are processed after 5 seconds of inactivity, "
        "and only new data is read to conserve memory."
    )

    if "folder" not in st.session_state:
        st.session_state.folder = os.getcwd()
    previous_folder = st.session_state.folder  # [ADDED]



    if "observer" not in st.session_state:
        st.session_state.observer = None
        st.session_state.handler = None
    st.session_state.setdefault("log_lines", [])
    st.session_state.setdefault("processed_events", [])
    st.session_state.setdefault("generated_files", set())
    st.session_state.setdefault("folder_uploads", set())  # [ADDED]

    # 資料夾設定區域
    st.subheader("📁 資料夾監控設定")
    
    col1, col2, col3 = st.columns([4, 1.5, 1.5])
    with col1:
        # 使用選擇的路徑或預設值
        display_value = (st.session_state.get("selected_folder_path") or 
                        st.session_state.get("folder", os.getcwd()))
        
        # 使用唯一的 key 來強制重新渲染
        unique_key = f"folder_input_{hash(display_value)}"
        
        folder_input = st.text_input(
            "監控資料夾路徑",
            value=display_value,
            placeholder="輸入要監控的資料夾路徑...",
            help="請輸入有效的資料夾路徑進行監控",
            key=unique_key
        )
        
        # 清除選擇狀態，避免重複使用
        if "selected_folder_path" in st.session_state:
            del st.session_state.selected_folder_path

    def _use_cwd() -> None:
        current = os.getcwd()
        st.session_state.folder = current
        st.session_state.selected_folder_path = current  # 新的狀態變數
        st.rerun()

    def _browse_folder() -> None:
        # 簡化的資料夾瀏覽建議
        st.session_state.show_folder_examples = True
        _rerun()

    with col2:
        st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)  # 垂直對齊
        st.button(
            "📂 瀏覽",
            on_click=_browse_folder,
            help="顯示常用資料夾路徑範例",
            use_container_width=True,
        )

    with col3:
        st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)  # 垂直對齊
        st.button(
            "🏠 目前位置",
            on_click=_use_cwd,
            help="使用目前工作目錄作為監控資料夾",
            use_container_width=True,
        )

    # 處理常用資料夾選擇
    if st.session_state.get("show_folder_examples", False):
        st.info("💡 **常用資料夾範例 - 點擊選擇：**")
        example_cols = st.columns(3)
        
        common_folders = [
            ("📁 桌面", os.path.expanduser("~/Desktop")),
            ("📁 文件", os.path.expanduser("~/Documents")),
            ("📁 下載", os.path.expanduser("~/Downloads")),
        ]
        
        for i, (name, path) in enumerate(common_folders):
            with example_cols[i % 3]:
                # 創建安全的按鈕鍵值
                safe_path = path.replace('/', '_').replace('\\', '_')
                button_key = f"folder_example_{i}_{safe_path}"
                if st.button(name, key=button_key, use_container_width=True):
                    st.session_state.show_folder_examples = False
                    # 只更新內部狀態，不觸碰 widget 的 session_state
                    st.session_state.folder = path
                    st.session_state.selected_folder_path = path  # 新的狀態變數
                    st.success(f"✅ 已選擇資料夾：{path}")
                    st.rerun()

    # 使用用戶輸入的路徑或預設值
    folder_candidate = folder_input.strip() if folder_input else ""
    if folder_candidate:
        folder_path = Path(folder_candidate).expanduser()
        # 更新 session state 以保持同步
        st.session_state.folder = folder_candidate
    else:
        folder_path = Path(st.session_state.get("folder", os.getcwd()))

    folder_error = None
    try:
        folder_path.mkdir(parents=True, exist_ok=True)
        folder_path = folder_path.resolve()
    except OSError as exc:
        folder_error = str(exc)
        folder_valid = False
    else:
        folder_valid = folder_path.is_dir()

    if folder_valid:
        resolved_folder = str(folder_path)
        if resolved_folder != previous_folder:
            st.session_state.folder_uploads = set()
        st.session_state.folder = resolved_folder
        st.success(f"✅ 監控路徑：{folder_path}")
    else:
        if folder_candidate:
            if folder_error:
                st.error(f"❌ 無法使用資料夾：{folder_error}")
            else:
                st.error("❌ 提供的路徑不是有效的資料夾")
        st.warning("⚠️ 請輸入有效的資料夾路徑")

    # 檔案上傳區域
    st.subheader("📤 檔案上傳")
    uploaded_logs = st.file_uploader(
        "上傳日誌檔案或壓縮包到監控資料夾",
        type=["csv", "txt", "log", "gz", "zip"],
        accept_multiple_files=True,
        help="檔案將保存到監控資料夾中並自動處理",
        key="folder_monitor_upload",
    )

    if uploaded_logs:  # [ADDED]
        if folder_valid:  # [ADDED]
            processed_uploads = st.session_state.get("folder_uploads", set())  # [ADDED]
            saved_count = 0  # [ADDED]
            progress_bar_upload = st.progress(0)
            status_placeholder_upload = st.empty()
            
            for uploaded in uploaded_logs:  # [ADDED]
                signature = (uploaded.name, uploaded.size)  # [ADDED]
                if signature in processed_uploads:  # [ADDED]
                    continue  # [ADDED]
                destination = folder_path / uploaded.name  # [ADDED]
                with open(destination, "wb") as dest_file:  # [ADDED]
                    dest_file.write(uploaded.getbuffer())  # [ADDED]
                processed_uploads.add(signature)  # [ADDED]
                saved_count += 1  # [ADDED]
                _log_toast(f"Uploaded {destination}")  # [ADDED]
                
                # 立即處理上傳的檔案，不等待 watchdog 事件
                has_models = (st.session_state.get("binary_model") and
                              st.session_state.get("multi_model"))
                if has_models:
                    try:
                        status_placeholder_upload.text(
                            f"Processing uploaded file: {uploaded.name}")
                        # 嘗試獲取當前的 handler，用於標記產生檔案
                        current_handler = st.session_state.get("handler")
                        _run_etl_and_infer(str(destination), 
                                           progress_bar_upload, 
                                           status_placeholder_upload,
                                           current_handler)
                        processed_files = st.session_state.setdefault(
                            "processed_files", set())
                        processed_files.add(str(destination))
                        _log_toast(
                            f"Immediately processed uploaded file: {uploaded.name}")
                    except Exception as exc:
                        _log_toast(
                            f"Failed to process uploaded file {uploaded.name}: {exc}")
                else:
                    _log_toast(
                        f"Models not loaded, {uploaded.name} will be processed "
                        "when monitoring starts")
                    
            st.session_state.folder_uploads = processed_uploads  # [ADDED]
            if saved_count:  # [ADDED]
                st.success(f"Saved and processed {saved_count} file(s) to {folder_path}")  # [ADDED]
            else:  # [ADDED]
                st.info("Uploaded files are already available in the monitored folder.")  # [ADDED]
        else:  # [ADDED]
            st.error("Enter a valid folder path before uploading files.")  # [ADDED]

    # 模型載入區域
    st.subheader("⚙️ 機器學習模型")
    
    model_cols = st.columns(2)
    
    with model_cols[0]:
        bin_upload = st.file_uploader(
            "📊 二元分類模型",
            type=["pkl", "joblib"],
            help="用於判斷是否為攻擊的二元分類模型 (最大檔案大小：2GB)",
            key="binary_model_upload",
        )
        if bin_upload is not None:
            try:
                st.session_state.binary_model = joblib.load(bin_upload)
                st.success("✅ 二元分類模型已載入")
            except Exception:
                st.error("❌ 二元分類模型載入失敗")
                st.session_state.log_lines.append("Failed to load binary model")

    with model_cols[1]:
        mul_upload = st.file_uploader(
            "🎯 多元分類模型",
            type=["pkl", "joblib"],
            help="用於判斷攻擊嚴重程度的多元分類模型 (最大檔案大小：2GB)",
            key="multi_model_upload",
        )
        if mul_upload is not None:
            try:
                st.session_state.multi_model = joblib.load(mul_upload)
                st.success("✅ 多元分類模型已載入")
            except Exception:
                st.error("❌ 多元分類模型載入失敗")
                st.session_state.log_lines.append("Failed to load multiclass model")

    # 顯示模型狀態
    if st.session_state.get("binary_model") and st.session_state.get("multi_model"):
        st.info("🟢 **所有模型已就緒，可以開始監控處理**")
    elif st.session_state.get("binary_model") or st.session_state.get("multi_model"):
        st.warning("🟡 **部分模型已載入，需要兩個模型才能完整處理**")
    else:
        st.warning("🔴 **請先上傳兩個機器學習模型才能進行監控處理**")

    # 設定區域
    st.subheader("⚙️ 監控設定")
    
    settings_cols = st.columns([2, 1])
    with settings_cols[0]:
        retention = st.number_input(
            "自動清理檔案 (小時，0=關閉)",
            min_value=0,
            value=0,
            step=1,
            key="cleanup_hours",
            help="自動刪除超過指定小時數的生成檔案",
        )
    
    with settings_cols[1]:
        st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)
        if st.button("🗑️ 立即清理", use_container_width=True, 
                     help="立即清理所有生成的檔案"):
            _cleanup_generated(0, force=True)
            st.success("已清理所有生成檔案")

    # 控制按鈕區域
    st.subheader("🎛️ 監控控制")
    action_cols = st.columns(2)

    if Observer is None:
        st.error("❌ **watchdog 套件未安裝**，無法使用檔案監控功能")
        return

    folder = st.session_state.folder
    is_monitoring = st.session_state.observer is not None
    start_disabled = is_monitoring or not folder_valid
    stop_disabled = not is_monitoring

    status_placeholder = st.empty()
    start_help = ("請先輸入有效的資料夾路徑" if not folder_valid 
                  else "監控已啟動" if is_monitoring else "開始監控指定資料夾")

    with action_cols[0]:
        start_button_text = "🔴 監控運行中" if is_monitoring else "▶️ 開始監控"
        if st.button(
            start_button_text,
            disabled=start_disabled,
            help=start_help,
            use_container_width=True,
            type="secondary" if is_monitoring else "primary",
        ):
            # 建立增強版的處理器
            handler = _FileMonitorHandler()
            
            # 啟動 Watchdog 觀察器
            observer = Observer()
            observer.schedule(handler, folder, recursive=False)
            observer.start()
            
            # 啟動持續監控循環
            use_watchdog = Observer is not None
            handler.start_monitoring(folder, use_watchdog)
            
            # 儲存到 session state
            st.session_state.observer = observer
            st.session_state.handler = handler
            status_placeholder.success(f"✅ 已開始監控：{folder}")
            _log_toast(f"Enhanced monitoring started on {folder}")

    with action_cols[1]:
        stop_button_text = "⏹️ 停止監控"
        if st.button(stop_button_text, disabled=stop_disabled, 
                     use_container_width=True, type="secondary"):
            # 停止持續監控
            handler = st.session_state.get("handler")
            if handler:
                handler.stop_monitoring()
            
            # 停止 Watchdog 觀察器
            observer = st.session_state.observer
            if observer is not None:
                observer.stop()
                observer.join()
                
            # 清理 session state
            st.session_state.observer = None
            st.session_state.handler = None
            status_placeholder.info("⏹️ 監控已停止")
            _log_toast("Enhanced monitoring stopped")

    # 處理進度和狀態顯示
    st.subheader("📊 處理狀態")
    
    # 顯示詳細監控狀態
    handler = st.session_state.get("handler")
    if handler:
        status_info = handler.get_status()
        
        # 狀態概覽
        status_cols = st.columns([2, 2, 2])
        with status_cols[0]:
            status_emoji = "🟢" if status_info['is_running'] else "🔴"
            status_text = "監控中" if status_info['is_running'] else "已停止"
            st.metric("監控狀態", f"{status_emoji} {status_text}")
            
        with status_cols[1]:
            st.metric("已處理檔案", f"{status_info['processed_count']} 個")
            
        with status_cols[2]:
            st.metric("待處理事件", f"{status_info['pending_events']} 個")
        
        # 詳細狀態表格
        st.markdown("**📋 詳細監控資訊**")
        status_data = {
            "項目": ["監控資料夾", "監控方式", "運行狀態", "已處理檔案", "待處理事件"],
            "內容": [
                status_info['folder_path'],
                status_info['method'],
                "🟢 運行中" if status_info['is_running'] else "🔴 已停止",
                f"{status_info['processed_count']} 個檔案",
                f"{status_info['pending_events']} 個事件"
            ]
        }
        st.table(pd.DataFrame(status_data))
        
        # 最近活動訊息
        if status_info['last_messages']:
            st.markdown("**📢 最近活動**")
            for msg in status_info['last_messages']:
                st.text(f"• {msg}")
    
    progress_bar = st.progress(0)

    if st.session_state.observer is not None:
        _process_events(st.session_state.handler, progress_bar, 
                        status_placeholder)
        _cleanup_generated(retention)

    # 報告結果顯示
    report_path = st.session_state.get("last_report_path")
    if report_path:
        st.success(f"📋 **報告已生成**：{report_path}")
        
        # 顯示簡易統計預覽
        counts = st.session_state.get("last_counts")
        if counts:
            preview_cols = st.columns(3)
            with preview_cols[0]:
                total = int(counts["is_attack"].sum())
                st.metric("總事件數", f"{total:,}")
            with preview_cols[1]:
                attacks = int(counts["is_attack"].get(1, 0))
                attack_percentage = (attacks/total*100) if total > 0 else 0
                st.metric("攻擊事件", f"{attacks:,}", 
                         delta=f"{attack_percentage:.1f}% 攻擊率" if total > 0 else "0% 攻擊率",
                         help=f"在 {total:,} 個總事件中，有 {attacks:,} 個被識別為攻擊事件，攻擊率為 {attack_percentage:.1f}%")
            with preview_cols[2]:
                cr_counts = counts.get("crlevel")
                if cr_counts is not None and not cr_counts.empty:
                    high_risk = int(cr_counts.loc[cr_counts.index >= 3].sum())
                    st.metric("高風險事件", f"{high_risk:,}")
                else:
                    st.metric("高風險事件", "0")
        
        # 提供直接查看視覺化的提示
        st.info("💡 **請前往 'Visualization' 頁面查看詳細圖表和分析結果**")
        
        # 顯示報告檔案位置
        st.caption(f"📁 報告檔案位置：{report_path}")

    # 日誌區域
    st.subheader("📝 處理日誌")
    log_container = st.container()
    with log_container:
        if st.session_state.log_lines:
            # 顯示最新的日誌條目
            recent_logs = st.session_state.log_lines[-10:]  # 最新10條
            for log_line in recent_logs:
                st.text(log_line)
            
            if len(st.session_state.log_lines) > 10:
                if st.button("📜 顯示完整日誌"):
                    st.text_area("完整日誌", 
                               "\n".join(st.session_state.log_lines), 
                               height=200)
        else:
            st.info("暫無處理日誌")

    # 持續監控和自動重新整理
    if st.session_state.observer is not None:
        handler = st.session_state.handler
        
        # 檢查監控狀態和新事件
        if handler:
            status_info = handler.get_status()
            is_monitoring = status_info.get('is_running', False)
            has_pending_events = status_info.get('pending_events', 0) > 0
            
            # 顯示即時監控狀態
            if is_monitoring:
                st.info(f"🔄 持續監控中... 待處理事件: {status_info.get('pending_events', 0)} 個")
            
            # 如果正在監控，使用短間隔自動重新整理
            if is_monitoring or has_pending_events:
                if st_autorefresh is not None:
                    st_autorefresh(interval=2000, key="continuous_monitor_refresh")
                else:  # pragma: no cover - fallback when autorefresh missing
                    time.sleep(1)
                    _rerun()
            else:
                # 監控停止時，使用較長間隔檢查
                if st_autorefresh is not None:
                    st_autorefresh(interval=5000, key="monitor_idle_check")

