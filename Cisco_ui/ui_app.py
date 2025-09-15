"""Cisco Streamlit 主介面。"""
from __future__ import annotations

import streamlit as st
from streamlit.errors import StreamlitAPIException

try:
    from streamlit_option_menu import option_menu
except ModuleNotFoundError:  # pragma: no cover - 選用套件
    option_menu = None

from ui_pages import data_cleaning, log_monitor, model_inference, notifications, visualization

PAGES = {
    "通知模組": notifications.app,
    "Log 擷取": log_monitor.app,
    "模型推論": model_inference.app,
    "圖表預覽": visualization.app,
    "資料清理": data_cleaning.app,
}
PAGE_EMOJIS = {
    "通知模組": "🔔",
    "Log 擷取": "📄",
    "模型推論": "🔍",
    "圖表預覽": "📊",
    "資料清理": "🗑",
}
PAGE_ICONS = {
    "通知模組": "bell",
    "Log 擷取": "folder",
    "模型推論": "cpu",
    "圖表預覽": "bar-chart",
    "資料清理": "trash",
}
PAGE_DESCRIPTIONS = {
    "通知模組": "管理 Gemini、LINE 與 Discord 推播設定。",
    "Log 擷取": "監控 ASA log 並自動觸發清洗與推播。",
    "模型推論": "手動執行全流程 Pipeline。",
    "圖表預覽": "瀏覽二元與多元分析圖表。",
    "資料清理": "排程刪除暫存檔案，維持磁碟整潔。",
}


def _configure_page() -> None:
    try:
        st.set_page_config(page_title="Cisco D-FLARE 控制中心", page_icon="📡", layout="wide")
    except StreamlitAPIException:
        # 在統一介面中可能已設定過 page config，忽略此例外即可。
        pass


def _render_sidebar() -> str:
    if "cisco_menu_collapse" not in st.session_state:
        st.session_state["cisco_menu_collapse"] = False
    sidebar_width = "72px" if st.session_state["cisco_menu_collapse"] else "260px"

    st.markdown(
        f"""
        <style>
        div[data-testid="stSidebar"] {{
            width: {sidebar_width};
            background-color: #0f172a;
            transition: width 0.3s ease;
        }}
        div[data-testid="stSidebar"] .nav-link {{
            color: #e2e8f0;
        }}
        div[data-testid="stSidebar"] .nav-link:hover {{
            background-color: #1e293b;
        }}
        div[data-testid="stSidebar"] .nav-link-selected {{
            background-color: #2563eb;
            color: #ffffff;
        }}
        .menu-collapsed .nav-link span {{
            display: none;
        }}
        .menu-collapsed .nav-link {{
            justify-content: center;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )

    page_keys = list(PAGES.keys())
    page_labels = [f"{PAGE_EMOJIS[name]} {name}" for name in page_keys]

    with st.sidebar:
        st.title("Cisco D-FLARE")
        st.caption("整合 log 擷取、模型分析與通知的控制中心。")
        if option_menu:
            if st.button("☰", key="cisco_menu_toggle"):
                st.session_state["cisco_menu_collapse"] = not st.session_state["cisco_menu_collapse"]
            menu_class = "menu-collapsed" if st.session_state["cisco_menu_collapse"] else "menu-expanded"
            st.markdown(f"<div class='{menu_class}'>", unsafe_allow_html=True)
            label = option_menu(
                None,
                page_labels,
                icons=[PAGE_ICONS[name] for name in page_keys],
                menu_icon="list",
                default_index=0,
                styles={
                    "container": {"padding": "0", "background-color": "#0f172a"},
                    "icon": {"color": "white", "font-size": "16px"},
                    "nav-link": {
                        "color": "#cbd5f5",
                        "font-size": "15px",
                        "text-align": "left",
                        "margin": "0px",
                        "--hover-color": "#1e293b",
                    },
                    "nav-link-selected": {"background-color": "#1d4ed8"},
                },
            )
            st.markdown("</div>", unsafe_allow_html=True)
        else:
            label = st.radio("功能選單", page_labels)

        selection = page_keys[page_labels.index(label)]
        st.markdown(PAGE_DESCRIPTIONS.get(selection, ""))
    return selection


def render() -> None:
    _configure_page()
    selection = _render_sidebar()
    PAGES[selection]()


if __name__ == "__main__":
    render()
