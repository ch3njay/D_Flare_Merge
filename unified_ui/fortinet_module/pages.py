"""Fortinet 介面在統一平台的渲染邏輯。"""
from __future__ import annotations

import html

import streamlit as st

try:
    from streamlit_option_menu import option_menu
except ModuleNotFoundError:  # pragma: no cover
    option_menu = None

from Forti_ui_app_bundle.ui_pages import (
    folder_monitor_ui,
    gpu_etl_ui,
    inference_ui,
    notifier_app,
    training_ui,
    visualization_ui,
)

PAGES = {
    "Training Pipeline": training_ui.app,
    "GPU ETL Pipeline": gpu_etl_ui.app,
    "Model Inference": inference_ui.app,
    "Folder Monitor": folder_monitor_ui.app,
    "Visualization": visualization_ui.app,
    "Notifications": notifier_app.app,
}
PAGE_ICONS = {
    "Training Pipeline": "gear",
    "GPU ETL Pipeline": "speedometer2",
    "Model Inference": "cpu",
    "Folder Monitor": "folder",
    "Visualization": "bar-chart",
    "Notifications": "bell",
}
PAGE_DESCRIPTIONS = {
    "Training Pipeline": "設定訓練流程與參數。",
    "GPU ETL Pipeline": "啟動 GPU 加速的 ETL 任務。",
    "Model Inference": "使用已訓練模型進行推論。",
    "Folder Monitor": "監控資料夾並自動清洗檔案。",
    "Visualization": "瀏覽數據可視化結果。",
    "Notifications": "管理通知與 Gemini 建議。",
}


def render() -> None:
    # 維持舊狀態鍵以免其他模組存取時發生 KeyError。
    st.session_state.setdefault("fortinet_menu_collapse", False)

    page_keys = list(PAGES.keys())
    page_labels = page_keys

    with st.sidebar:
        if option_menu:
            default_page = st.session_state.get("fortinet_active_page", page_keys[0])
            default_index = page_keys.index(default_page) if default_page in page_keys else 0
            st.markdown("<div class='sidebar-nav sidebar-nav--fortinet'>", unsafe_allow_html=True)
            selection = option_menu(
                None,
                page_labels,
                icons=[PAGE_ICONS[name] for name in page_keys],
                menu_icon="cast",
                default_index=default_index,
                key="fortinet_sidebar_menu",
                styles={
                    "container": {"padding": "0", "background-color": "transparent"},
                    "icon": {"color": "var(--sidebar-icon)", "font-size": "18px"},
                    "nav-link": {
                        "color": "var(--sidebar-text)",
                        "font-size": "15px",
                        "text-align": "left",
                        "margin": "0px",
                        "--hover-color": "var(--sidebar-button-hover)",
                    },
                    "nav-link-selected": {"background-color": "transparent"},
                },
            )
            st.markdown("</div>", unsafe_allow_html=True)
        else:
            selection = st.radio("功能選單", page_labels, key="fortinet_sidebar_menu")

        st.session_state["fortinet_active_page"] = selection

        description = PAGE_DESCRIPTIONS.get(selection, "")
        if description:
            st.markdown(
                f"<p class='sidebar-menu-description'>{html.escape(description)}</p>",
                unsafe_allow_html=True,
            )

    PAGES[selection]()
