"""Cisco 圖表預覽模組。"""
from __future__ import annotations

import os
from typing import Dict

import streamlit as st

from ui_pages.log_monitor import get_log_monitor

CHART_FILES: Dict[str, str] = {
    "二元長條圖": "binary_bar.png",
    "二元圓餅圖": "binary_pie.png",
    "多元長條圖": "multiclass_bar.png",
    "多元圓餅圖": "multiclass_pie.png",
}


def _get_folder() -> str:
    if "cisco_visual_folder" not in st.session_state:
        monitor = get_log_monitor()
        st.session_state["cisco_visual_folder"] = monitor.settings.get("clean_csv_dir", "")
    return st.session_state["cisco_visual_folder"]


def app() -> None:
    """顯示自動產生的圖表，提供路徑同步按鈕。"""
    st.title("📊 圖表產生與檢視")
    st.markdown("可預覽自動分析後輸出的 PNG 圖表，方便資安人員快速確認趨勢。")

    folder = st.text_input("圖表資料夾", value=_get_folder())
    st.session_state["cisco_visual_folder"] = folder

    if st.button("同步自動清洗輸出路徑"):
        monitor = get_log_monitor()
        st.session_state["cisco_visual_folder"] = monitor.settings.get("clean_csv_dir", "")
        st.experimental_rerun()

    col1, col2, col3, col4 = st.columns(4)
    buttons = list(CHART_FILES.keys())
    cols = [col1, col2, col3, col4]
    for col, label in zip(cols, buttons):
        if col.button(label):
            st.session_state["cisco_visual_selected"] = label

    selected = st.session_state.get("cisco_visual_selected", buttons[0])
    filename = CHART_FILES[selected]
    st.markdown(f"#### 目前檢視：{selected}")

    path = os.path.join(st.session_state["cisco_visual_folder"], filename)
    if folder and os.path.exists(path):
        st.image(path, caption=f"{selected} ({path})", use_column_width=True)
    else:
        st.warning(f"找不到圖表檔案：{path}")
