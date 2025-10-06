"""Cisco 模型推論頁面模組。"""
from __future__ import annotations

import html
import os
import tempfile
from typing import Optional

import pandas as pd
import streamlit as st

from .log_monitor import get_log_monitor

# Import required modules with multiple fallback strategies
PipelineConfig = None
execute_pipeline = None
notification_pipeline = None
load_json = None

try:  # First try: package-relative imports when available
    from ..training_pipeline.config import PipelineConfig
    from ..training_pipeline.trainer import execute_pipeline
    from ..notifier import notification_pipeline
    from ..utils_labels import load_json
except (ImportError, ValueError):
    try:  # Second try: direct imports from package directory
        from training_pipeline.config import PipelineConfig  # type: ignore[no-redef]
        from training_pipeline.trainer import execute_pipeline  # type: ignore[no-redef]
        from notifier import notification_pipeline  # type: ignore[no-redef]
        from utils_labels import load_json  # type: ignore[no-redef]
    except ImportError:
        try:  # Third try: absolute imports from Cisco_ui
            from Cisco_ui.training_pipeline.config import PipelineConfig  # type: ignore[no-redef]
            from Cisco_ui.training_pipeline.trainer import execute_pipeline  # type: ignore[no-redef]
            from Cisco_ui.notifier import notification_pipeline  # type: ignore[no-redef]
            from Cisco_ui.utils_labels import load_json  # type: ignore[no-redef]
        except ImportError:
            # Final fallback: create stub functions to prevent crashes
            import warnings
            warnings.warn("Could not import Cisco pipeline modules. Some functionality will be limited.")
            
            class PipelineConfig:  # type: ignore[no-redef]
                def __init__(self, **kwargs):
                    pass
            
            def execute_pipeline(*args, **kwargs):  # type: ignore[no-redef]
                st.error("Pipeline execution not available - missing dependencies")
                return None
            
            def notification_pipeline(*args, **kwargs):  # type: ignore[no-redef]
                st.warning("Notification pipeline not available")
                return None
            
            def load_json(file_path, default=None):  # type: ignore[no-redef]
                import os
                if os.path.exists(file_path):
                    import json
                    with open(file_path, 'r', encoding='utf-8') as f:
                        return json.load(f)
                return default or {}

NOTIFIER_SETTINGS_FILE = "notifier_settings.txt"


def _write_temp_file(upload, suffix: str) -> Optional[str]:
    """將上傳檔案寫入暫存檔，回傳實際路徑。"""
    if upload is None:
        return None
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(upload.getbuffer())
        return tmp.name


def _render_path_preview(label: str, value: str, *, icon: str = "📁") -> None:
    """以一致樣式呈現檔案路徑或名稱。"""

    safe_label = html.escape(label)
    safe_icon = html.escape(icon)
    if value:
        safe_value = html.escape(value)
        extra_class = ""
    else:
        safe_value = "尚未選擇"
        extra_class = " path-preview--empty"

    # 使用 inline flex 讓圖示、標籤、路徑在同一行顯示，避免 emoji 換行
    st.markdown(
        f"""
        <div class="path-preview{extra_class}" style="display:flex;align-items:center;gap:0.5rem;">
            <span class="path-preview__icon" style="flex:0 0 auto;font-size:1.1rem;">{safe_icon}</span>
            <span class="path-preview__text" style="white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">
                <strong class="path-preview__label">{safe_label}</strong>&nbsp;
                <span class="path-preview__path">{safe_value}</span>
            </span>
        </div>
        """,
        unsafe_allow_html=True,
    )


def app() -> None:
    """提供手動執行完整 Pipeline 的頁面。"""
    st.title("🔍 Cisco 模型推論與批次分析")
    st.markdown("可手動選擇原始 log 檔與模型，立即執行 Cisco ASA 全流程分析。")

    monitor = get_log_monitor()
    default_output = monitor.settings.get("clean_csv_dir", "")
    saved_log = monitor.last_processed_file
    saved_binary = st.session_state.get("cisco_binary_model_path", monitor.settings.get("binary_model_path", ""))
    saved_multi = st.session_state.get("cisco_multi_model_path", monitor.settings.get("model_path", ""))

    st.markdown("#### 1. 選擇輸入檔案")
    upload_log = st.file_uploader(
        "上傳原始 log (CSV/TXT/GZ)",
        type=["csv", "txt", "gz"],
        key="cisco_inference_log_uploader",
    )

    # 決定 checkbox 的預設可用性（在 widget 建立前設定 session_state）
    can_use_recent = bool(saved_log) and (upload_log is None)
    # 確保 session_state 在建立 widget 前有預設值，避免後續直接修改造成 Streamlit 錯誤
    st.session_state.setdefault("cisco_use_recent_log_checkbox", can_use_recent)

    use_recent_log = st.checkbox(
        "使用最近的監控檔案",
        disabled=not can_use_recent,
        key="cisco_use_recent_log_checkbox",
        help="若先前於「Log 擷取」頁面完成分析，可直接重用最新的檔案。",
    )

    # 根據上傳或選擇顯示路徑預覽
    if upload_log is not None:
        # 當使用者上傳新檔案時，視為不使用最近檔案
        use_recent_log = False
        _render_path_preview("上傳的 log 檔案", upload_log.name, icon="📄")
    elif use_recent_log and saved_log:
        _render_path_preview("最近的監控檔案", saved_log, icon="📄")
    else:
        _render_path_preview("目前選擇的 log 檔案", "", icon="📄")
        if not saved_log:
            st.caption("尚未有監控紀錄，可於「Log 擷取」頁面執行自動分析後再回到此處。")

    st.markdown("#### 2. 模型設定")
    upload_binary = st.file_uploader(
        "上傳二元模型 (.pkl/.joblib)",
        type=["pkl", "joblib"],
        key="binary_upload",
    )
    if upload_binary is not None:
        _render_path_preview("上傳的二元模型", upload_binary.name, icon="🧠")
    else:
        _render_path_preview("目前儲存的二元模型", saved_binary, icon="🧠")
        if not saved_binary:
            st.caption("尚未設定二元模型，可於「Log 擷取」頁面上傳並儲存。")

    upload_multi = st.file_uploader(
        "上傳多元模型 (.pkl/.joblib)",
        type=["pkl", "joblib"],
        key="multi_upload",
    )
    if upload_multi is not None:
        _render_path_preview("上傳的多元模型", upload_multi.name, icon="🗂️")
    else:
        _render_path_preview("目前儲存的多元模型", saved_multi, icon="🗂️")
        if not saved_multi:
            st.caption("尚未設定多元模型，可於「Log 擷取」頁面上傳並儲存。")

    st.markdown("#### 3. 輸出設定")
    output_dir = st.text_input(
        "輸出資料夾",
        value=default_output,
        placeholder="例如：/data/cisco/output",
    )
    auto_notify = st.checkbox("自動觸發通知模組", value=True)

    if st.button("🚀 執行 Pipeline"):
        log_path = None
        if upload_log is not None:
            log_suffix = os.path.splitext(upload_log.name)[1] or ".log"
            log_path = _write_temp_file(upload_log, suffix=log_suffix)
        elif use_recent_log and saved_log:
            log_path = saved_log

        binary_path = None
        if upload_binary is not None:
            binary_suffix = os.path.splitext(upload_binary.name)[1] or ".pkl"
            binary_path = _write_temp_file(upload_binary, suffix=binary_suffix)
        else:
            binary_path = saved_binary

        multi_path = None
        if upload_multi is not None:
            multi_suffix = os.path.splitext(upload_multi.name)[1] or ".pkl"
            multi_path = _write_temp_file(upload_multi, suffix=multi_suffix)
        else:
            multi_path = saved_multi

        errors = []
        if not log_path or not os.path.exists(log_path):
            errors.append("原始 log")
        if not binary_path or not os.path.exists(binary_path):
            errors.append("二元模型")
        if not multi_path or not os.path.exists(multi_path):
            errors.append("多元模型")
        if not output_dir:
            errors.append("輸出資料夾")
        if errors:
            st.error("請確認以下項目：" + "、".join(errors))
        else:
            os.makedirs(output_dir, exist_ok=True)
            try:
                config = PipelineConfig(
                    raw_log_path=log_path,
                    binary_model_path=binary_path,
                    multiclass_model_path=multi_path,
                    output_dir=output_dir,
                    show_progress=False,
                )
                # 診斷檔案是否存在
                st.write("檔案檢查:")
                st.write(f"- log_path: {log_path}, exists: {os.path.exists(log_path) if log_path else False}")
                st.write(f"- binary_path: {binary_path}, exists: {os.path.exists(binary_path) if binary_path else False}")
                st.write(f"- multi_path: {multi_path}, exists: {os.path.exists(multi_path) if multi_path else False}")
                
                # 執行 pipeline，使用防護式錯誤處理以取得更清楚的錯誤訊息
                try:
                    result = execute_pipeline(config)
                    st.write("Pipeline result:", result)
                except Exception as pipe_exc:
                    st.error(f"Pipeline 執行錯誤: {pipe_exc}")
                    # 嘗試將原始 exception traceback 顯示給開發者
                    import traceback
                    tb = traceback.format_exc()
                    st.text_area("Pipeline Traceback", tb, height=200)
                    result = None

                if result is None:
                    st.error("分析未產生結果 (pipeline 回傳 None)。請檢查輸入或 pipeline 設定。")
                    # 顯示 debug 訊息（如果有）
                    if result and "debug" in result:
                        st.warning(f"[Debug] {result['debug']}")
                else:
                    st.success("分析完成！")
                    try:
                        st.json(result)
                    except Exception:
                        st.write("分析結果：", str(result))
                    st.session_state["cisco_manual_result"] = result
                    # 顯示 debug 訊息（如果有）
                    if result and "debug" in result:
                        st.info(f"[Debug] {result['debug']}")

                multi_csv = result.get("multiclass_output_csv") if result else None
                if multi_csv and os.path.exists(multi_csv):
                    st.markdown("#### 多元結果預覽")
                    try:
                        df_multi = pd.read_csv(multi_csv)
                        st.dataframe(df_multi.head(50))
                    except Exception as exc:  # pragma: no cover
                        st.warning(f"無法讀取多元結果：{exc}")
                elif result is None:
                    st.warning("無法預覽多元結果，因為 pipeline 執行失敗或未產生結果。")

                if auto_notify:
                    st.info("自動推播啟動中...")
                    notifier_settings = load_json(NOTIFIER_SETTINGS_FILE, {})
                    fields = notifier_settings.get("convergence_fields", ["source", "destination"])
                    if not isinstance(fields, list):
                        fields = ["source", "destination"]
                    if result:
                        notification_pipeline(
                            result_csv=result.get("multiclass_output_csv", ""),
                            gemini_api_key=notifier_settings.get("gemini_api_key", ""),
                            line_channel_access_token=notifier_settings.get("line_channel_access_token", ""),
                            line_webhook_url=notifier_settings.get("line_webhook_url", ""),
                            discord_webhook_url=notifier_settings.get("discord_webhook_url", ""),
                            ui_callback=lambda msg: st.write(msg),
                            convergence_config={
                                "window_minutes": int(
                                    notifier_settings.get("convergence_window_minutes", 10) or 10
                                ),
                                "group_fields": fields,
                            },
                        )
                    else:
                        st.warning("自動推播未啟動，因為 pipeline 執行失敗或未產生結果。")
            except Exception as exc:  # pragma: no cover
                st.error(f"執行失敗：{exc}")

    if "cisco_manual_result" in st.session_state:
        st.markdown("### 最近一次分析結果")
        st.json(st.session_state["cisco_manual_result"])
