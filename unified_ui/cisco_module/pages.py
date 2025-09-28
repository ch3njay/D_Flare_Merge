"""Cisco 介面在統一平台中的轉接層。"""
from __future__ import annotations

import html

import streamlit as st

try:
    from streamlit_option_menu import option_menu
except ModuleNotFoundError:  # pragma: no cover - 選用套件
    option_menu = None

from Cisco_ui import ui_app as cisco_app

PAGES = cisco_app.PAGES
PAGE_ICONS = cisco_app.PAGE_ICONS
PAGE_DESCRIPTIONS = cisco_app.PAGE_DESCRIPTIONS

PAGE_EMOJIS = {
    "通知模組": "🔔",
    "Log 擷取": "📡",
    "模型推論": "🤖",
    "圖表預覽": "📊",
    "資料清理": "🧹",
}


def _configure_page() -> None:
    configure = getattr(cisco_app, "_configure_page", None)
    if callable(configure):
        configure()


def render() -> None:
    _configure_page()
    st.session_state.setdefault("fortinet_menu_collapse", False)

    page_keys = list(PAGES.keys())
    page_labels = page_keys

    with st.sidebar:
        if option_menu:
            default_page = st.session_state.get("cisco_active_page", page_keys[0])
            default_index = page_keys.index(default_page) if default_page in page_keys else 0
            st.markdown("<div class='sidebar-nav sidebar-nav--cisco'>", unsafe_allow_html=True)
            selection = option_menu(
                None,
                page_labels,
                icons=[PAGE_ICONS[name] for name in page_keys],
                menu_icon="list",
                default_index=default_index,
                key="cisco_sidebar_menu",
                styles={
                    "container": {"padding": "0", "background-color": "transparent"},
                    "icon": {"color": "var(--df-hero-text)", "font-size": "18px"},
                    "nav-link": {
                        "color": "var(--df-text-strong)",
                        "font-size": "13px",
                        "text-align": "left",
                        "margin": "0px",
                        "--hover-color": "var(--primaryColor)",
                    },
                    "nav-link-selected": {"background-color": "transparent"},
                },
            )
            st.markdown("</div>", unsafe_allow_html=True)
        else:
            default_page = st.session_state.get("cisco_active_page", page_keys[0])
            default_index = page_keys.index(default_page) if default_page in page_keys else 0
            st.markdown("<div class='sidebar-nav sidebar-nav--cisco'>", unsafe_allow_html=True)

            def _format(label: str) -> str:
                emoji = PAGE_EMOJIS.get(label, "📄")
                return f"{emoji}  {label}"

            selection = st.radio(
                "功能選單",
                page_labels,
                index=default_index,
                key="cisco_sidebar_menu",
                label_visibility="collapsed",
                format_func=_format,
            )
            st.markdown("</div>", unsafe_allow_html=True)

        st.session_state["cisco_active_page"] = selection

        description = PAGE_DESCRIPTIONS.get(selection, "")
        if description:
            st.markdown(
                f"<p class='sidebar-menu-description'>{html.escape(description)}</p>",
                unsafe_allow_html=True,
            )

    PAGES[selection]()
