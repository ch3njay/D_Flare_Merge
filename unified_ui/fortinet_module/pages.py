"""Fortinet 介面在統一平台的渲染邏輯。"""
from __future__ import annotations

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
PAGE_EMOJIS = {
    "Training Pipeline": "🛠️",
    "GPU ETL Pipeline": "🚀",
    "Model Inference": "🔍",
    "Folder Monitor": "📁",
    "Visualization": "📊",
    "Notifications": "🔔",
}
PAGE_ICONS = {
    "Training Pipeline": "cpu",
    "GPU ETL Pipeline": "gpu",
    "Model Inference": "search",
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
    if "fortinet_menu_collapse" not in st.session_state:
        st.session_state["fortinet_menu_collapse"] = False
    collapsed = st.session_state["fortinet_menu_collapse"]

    st.markdown(
        """
        <style>
        div[data-testid="stSidebar"] .fortinet-menu .nav-link {
            color: #d1d5db;
        }
        div[data-testid="stSidebar"] .fortinet-menu .nav-link:hover {
            background-color: #374151;
        }
        div[data-testid="stSidebar"] .fortinet-menu .nav-link-selected {
            background-color: #111827;
            color: #f9fafb;
        }
        .menu-collapsed .fortinet-menu .nav-link span {
            display: none;
        }
        .menu-collapsed .fortinet-menu .nav-link {
            justify-content: center;
        }
        div[data-testid="stSidebar"] .fortinet-menu-description {
            color: #9ca3af;
            font-size: 0.85rem;
            margin-top: 0.75rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    page_keys = list(PAGES.keys())
    page_labels = [f"{PAGE_EMOJIS[name]} {name}" for name in page_keys]

    with st.sidebar:
        menu_class = "menu-collapsed" if collapsed else "menu-expanded"
        if option_menu:
            st.markdown(f"<div class='fortinet-menu {menu_class}'>", unsafe_allow_html=True)
            label = option_menu(
                None,
                page_labels,
                icons=[PAGE_ICONS[name] for name in page_keys],
                menu_icon="cast",
                default_index=0,
                styles={
                    "container": {"padding": "0", "background-color": "transparent"},
                    "icon": {"color": "white", "font-size": "16px"},
                    "nav-link": {
                        "color": "#d1d5db",
                        "font-size": "16px",
                        "text-align": "left",
                        "margin": "0px",
                        "--hover-color": "#374151",
                    },
                    "nav-link-selected": {"background-color": "#111827"},
                },
            )
            st.markdown("</div>", unsafe_allow_html=True)
        else:
            label_visibility = "collapsed" if collapsed else "visible"
            label = st.radio("功能選單", page_labels, label_visibility=label_visibility)

        selection = page_keys[page_labels.index(label)]
        if not collapsed:
            description = PAGE_DESCRIPTIONS.get(selection, "")
            if description:
                st.markdown(
                    f"<p class='fortinet-menu-description'>{description}</p>",
                    unsafe_allow_html=True,
                )

    PAGES[selection]()
