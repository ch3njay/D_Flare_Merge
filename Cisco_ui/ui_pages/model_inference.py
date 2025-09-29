"""Cisco 模型推論頁面模組。"""
from __future__ import annotations

import html
import os
import tempfile
from typing import Optional

import pandas as pd
import streamlit as st

from .log_monitor import get_log_monitor

try:  # Package import when used via ``Cisco_ui``
    from ..training_pipeline.config import PipelineConfig
    from ..training_pipeline.trainer import execute_pipeline
    from ..notifier import notification_pipeline
    from ..utils_labels import load_json
except (ImportError, ValueError):  # Legacy support for running inside package folder
    from training_pipeline.config import PipelineConfig  # type: ignore[no-redef]
    from training_pipeline.trainer import execute_pipeline  # type: ignore[no-redef]
    from notifier import notification_pipeline  # type: ignore[no-redef]
    from utils_labels import load_json  # type: ignore[no-redef]

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

    st.markdown(
        f"""
        <div class="path-preview{extra_class}">
            <span class="path-preview__icon">{safe_icon}</span>
            <div class="path-preview__content">
                <span class="path-preview__label">{safe_label}</span>
                <span class="path-preview__path">{safe_value}</span>
            </div>
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
    can_use_recent = bool(saved_log)
    use_recent_log = st.checkbox(
        "使用最近的監控檔案",
        value=can_use_recent,
        disabled=not can_use_recent,
        key="cisco_use_recent_log_checkbox",
        help="若先前於「Log 擷取」頁面完成分析，可直接重用最新的檔案。",
    )
    if not can_use_recent:
        use_recent_log = False
    if upload_log is not None:
        use_recent_log = False
        st.session_state["cisco_use_recent_log_checkbox"] = False
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
                result = execute_pipeline(config)
                st.success("分析完成！")
                st.json(result)
                st.session_state["cisco_manual_result"] = result

                multi_csv = result.get("multiclass_output_csv")
                if multi_csv and os.path.exists(multi_csv):
                    st.markdown("#### 多元結果預覽")
                    try:
                        df_multi = pd.read_csv(multi_csv)
                        st.dataframe(df_multi.head(50))
                    except Exception as exc:  # pragma: no cover
                        st.warning(f"無法讀取多元結果：{exc}")

                if auto_notify:
                    st.info("自動推播啟動中...")
                    notifier_settings = load_json(NOTIFIER_SETTINGS_FILE, {})
                    fields = notifier_settings.get("convergence_fields", ["source", "destination"])
                    if not isinstance(fields, list):
                        fields = ["source", "destination"]
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
            except Exception as exc:  # pragma: no cover
                st.error(f"執行失敗：{exc}")

    if "cisco_manual_result" in st.session_state:
        st.markdown("### 最近一次分析結果")
        st.json(st.session_state["cisco_manual_result"])
