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
    sidebar_width = "72px" if st.session_state["fortinet_menu_collapse"] else "260px"

    st.markdown(
        f"""
        <style>
        div[data-testid="stSidebar"] {{
            width: {sidebar_width};
            background-color: #1f2937;
            transition: width 0.3s ease;
        }}
        div[data-testid="stSidebar"] .nav-link {{ color: #e5e7eb; }}
        div[data-testid="stSidebar"] .nav-link-selected {{ background-color: #2563eb; color: white; }}
        .menu-collapsed .nav-link span {{ display: none; }}
        .menu-collapsed .nav-link {{ justify-content: center; }}
        </style>
        """,
        unsafe_allow_html=True,
    )

    page_keys = list(PAGES.keys())
    page_labels = [f"{PAGE_EMOJIS[name]} {name}" for name in page_keys]

    with st.sidebar:
        st.title("Fortinet D-FLARE")
        st.caption("訓練、推論、視覺化與通知的一站式平台。")
        if option_menu:
            if st.button("☰", key="fortinet_menu_toggle"):
                st.session_state["fortinet_menu_collapse"] = not st.session_state["fortinet_menu_collapse"]
            menu_class = "menu-collapsed" if st.session_state["fortinet_menu_collapse"] else "menu-expanded"
            st.markdown(f"<div class='{menu_class}'>", unsafe_allow_html=True)
            label = option_menu(
                None,
                page_labels,
                icons=[PAGE_ICONS[name] for name in page_keys],
                menu_icon="cast",
                default_index=0,
                styles={
                    "container": {"padding": "0", "background-color": "#1f2937"},
                    "icon": {"color": "white", "font-size": "16px"},
                    "nav-link": {
                        "color": "#d1d5db",
                        "font-size": "16px",
                        "text-align": "left",
                        "margin": "0px",
                        "--hover-color": "#4b5563",
                    },
                    "nav-link-selected": {"background-color": "#111827"},
                },
            )
            st.markdown("</div>", unsafe_allow_html=True)
        else:
            label = st.radio("功能選單", page_labels)
        selection = page_keys[page_labels.index(label)]
        st.markdown(PAGE_DESCRIPTIONS.get(selection, ""))

    PAGES[selection]()
