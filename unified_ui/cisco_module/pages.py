"""Cisco 介面在統一平台中的轉接層。"""
from __future__ import annotations

import streamlit as st

try:
    from streamlit_option_menu import option_menu
except ModuleNotFoundError:  # pragma: no cover - 選用套件
    option_menu = None

from Cisco_ui import ui_app as cisco_app

PAGES = cisco_app.PAGES
PAGE_EMOJIS = cisco_app.PAGE_EMOJIS
PAGE_ICONS = cisco_app.PAGE_ICONS
PAGE_DESCRIPTIONS = cisco_app.PAGE_DESCRIPTIONS


def _configure_page() -> None:
    configure = getattr(cisco_app, "_configure_page", None)
    if callable(configure):
        configure()


def render() -> None:
    _configure_page()
    if "fortinet_menu_collapse" not in st.session_state:
        st.session_state["fortinet_menu_collapse"] = False
    collapsed = st.session_state["fortinet_menu_collapse"]

    st.markdown(
        """
        <style>
        div[data-testid="stSidebar"] .cisco-menu .nav-link {
            color: #dbeafe;
        }
        div[data-testid="stSidebar"] .cisco-menu .nav-link:hover {
            background-color: #1e3a8a;
        }
        div[data-testid="stSidebar"] .cisco-menu .nav-link-selected {
            background-color: #1d4ed8;
            color: #ffffff;
        }
        .menu-collapsed .cisco-menu .nav-link span {
            display: none;
        }
        .menu-collapsed .cisco-menu .nav-link {
            justify-content: center;
        }
        div[data-testid="stSidebar"] .cisco-menu-description {
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
            st.markdown(f"<div class='cisco-menu {menu_class}'>", unsafe_allow_html=True)
            label = option_menu(
                None,
                page_labels,
                icons=[PAGE_ICONS[name] for name in page_keys],
                menu_icon="list",
                default_index=0,
                styles={
                    "container": {"padding": "0", "background-color": "transparent"},
                    "icon": {"color": "white", "font-size": "16px"},
                    "nav-link": {
                        "color": "#bfdbfe",
                        "font-size": "15px",
                        "text-align": "left",
                        "margin": "0px",
                        "--hover-color": "#1e3a8a",
                    },
                    "nav-link-selected": {"background-color": "#2563eb"},
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
                    f"<p class='cisco-menu-description'>{description}</p>",
                    unsafe_allow_html=True,
                )

    PAGES[selection]()
