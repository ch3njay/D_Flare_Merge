"""Cisco 模型推論頁面模組。"""
from __future__ import annotations

import os
import tempfile
from typing import Optional

import pandas as pd
import streamlit as st

from training_pipeline.config import PipelineConfig
from training_pipeline.trainer import execute_pipeline
from notifier import notification_pipeline

from ui_pages.log_monitor import get_log_monitor
from utils_labels import load_json

NOTIFIER_SETTINGS_FILE = "notifier_settings.txt"


def _write_temp_file(upload, suffix: str) -> Optional[str]:
    """將上傳檔案寫入暫存檔，回傳實際路徑。"""
    if upload is None:
        return None
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(upload.getbuffer())
        return tmp.name


def app() -> None:
    """提供手動執行完整 Pipeline 的頁面。"""
    st.title("🔍 Cisco 模型推論與批次分析")
    st.markdown("可手動選擇原始 log 檔與模型，立即執行 Cisco ASA 全流程分析。")

    monitor = get_log_monitor()
    default_output = monitor.settings.get("clean_csv_dir", "")

    st.markdown("#### 1. 選擇輸入檔案")
    upload_log = st.file_uploader("上傳原始 log (CSV/TXT/GZ)", type=["csv", "txt", "gz"])
    manual_log_path = st.text_input("或輸入既有 log 路徑", value=monitor.last_processed_file)

    st.markdown("#### 2. 模型設定")
    upload_binary = st.file_uploader("上傳二元模型 (.pkl)", type=["pkl"], key="binary_upload")
    manual_binary_path = st.text_input("或輸入二元模型路徑", value=monitor.settings.get("binary_model_path", ""))

    upload_multi = st.file_uploader("上傳多元模型 (.pkl)", type=["pkl"], key="multi_upload")
    manual_multi_path = st.text_input("或輸入多元模型路徑", value=monitor.settings.get("model_path", ""))

    st.markdown("#### 3. 輸出設定")
    output_dir = st.text_input("輸出資料夾", value=default_output)
    auto_notify = st.checkbox("自動觸發通知模組", value=True)

    if st.button("🚀 執行 Pipeline"):
        log_path = _write_temp_file(upload_log, suffix=os.path.splitext(upload_log.name)[1]) if upload_log else manual_log_path
        binary_path = _write_temp_file(upload_binary, suffix=".pkl") if upload_binary else manual_binary_path
        multi_path = _write_temp_file(upload_multi, suffix=".pkl") if upload_multi else manual_multi_path

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
                    notification_pipeline(
                        result_csv=result.get("multiclass_output_csv", ""),
                        gemini_api_key=notifier_settings.get("gemini_api_key", ""),
                        line_channel_access_token=notifier_settings.get("line_channel_access_token", ""),
                        line_webhook_url=notifier_settings.get("line_webhook_url", ""),
                        discord_webhook_url=notifier_settings.get("discord_webhook_url", ""),
                        ui_callback=lambda msg: st.write(msg),
                    )
            except Exception as exc:  # pragma: no cover
                st.error(f"執行失敗：{exc}")

    if "cisco_manual_result" in st.session_state:
        st.markdown("### 最近一次分析結果")
        st.json(st.session_state["cisco_manual_result"])
