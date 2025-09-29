"""Cisco 介面在統一平台中的轉接層。"""
from __future__ import annotations

import html

import streamlit as st

from Cisco_ui import ui_app as cisco_app

PAGES = cisco_app.PAGES
PAGE_ICON_EMOJI = {
    "通知模組": "🔔",
    "Log 擷取": "🗂️",
    "模型推論": "🧠",
    "圖表預覽": "📊",
    "資料清理": "🧹",
}

PAGE_DESCRIPTIONS = cisco_app.PAGE_DESCRIPTIONS

_SIDEBAR_STYLE_FLAG = "_cisco_sidebar_styles"


def _configure_page() -> None:
    configure = getattr(cisco_app, "_configure_page", None)
    if callable(configure):
        configure()


def _ensure_sidebar_styles() -> None:
    if st.session_state.get(_SIDEBAR_STYLE_FLAG):
        return

    st.markdown(
        """
        <style>
        .sidebar-section-heading {
            display: flex;
            align-items: center;
            gap: 0.6rem;
            font-weight: 700;
            font-size: calc(var(--font-label) + 0.2px);
            margin: 1.4rem 0 0.8rem;
            color: var(--sidebar-text);
        }
        .sidebar-section-heading .bi {
            font-size: 1rem;
            color: var(--sidebar-icon);
        }
        .sidebar-radio {
            padding: 0.35rem;
            border-radius: 1.05rem;
            background: color-mix(in srgb, var(--sidebar-bg) 92%, var(--app-surface) 8%);
            border: 1px solid var(--muted-border);
            box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.04);
        }
        .sidebar-radio div[data-testid="stRadio"] > div[role="radiogroup"] {
            display: flex;
            flex-direction: column;
            gap: 0.55rem;
        }
        .sidebar-radio div[data-testid="stRadio"] input[type="radio"] {
            display: none;
        }
        .sidebar-radio div[data-testid="stRadio"] label {
            border-radius: 0.95rem;
            padding: 0.7rem 1rem;
            border: 1px solid transparent;
            background: transparent;
            font-weight: 600;
            color: var(--sidebar-text);
            display: flex;
            align-items: center;
            gap: 0.55rem;
            transition: all 0.2s ease;
            cursor: pointer;
        }
        .sidebar-radio div[data-testid="stRadio"] label:hover {
            border-color: color-mix(in srgb, var(--primary) 32%, transparent);
            background: color-mix(in srgb, var(--primary) 12%, transparent);
        }
        .sidebar-radio div[data-testid="stRadio"] label > div:first-child {
            display: none;
        }
        .sidebar-radio div[data-testid="stRadio"] label span {
            display: inline-flex;
            align-items: center;
            gap: 0.55rem;
        }
        .sidebar-radio div[data-testid="stRadio"] label[data-baseweb="radio"] {
            background: transparent;
        }
        .sidebar-radio div[data-testid="stRadio"] label:has(div[role="radio"][aria-checked="true"]) {
            background: linear-gradient(135deg, var(--primary), var(--primary-hover));
            color: var(--text-on-primary);
            border-color: transparent;
            box-shadow: var(--hover-glow);
        }
        .sidebar-radio div[data-testid="stRadio"] label:has(div[role="radio"][aria-checked="true"]) span {
            color: inherit;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
    st.session_state[_SIDEBAR_STYLE_FLAG] = True


def _render_navigation(page_keys: list[str]) -> str:
    _ensure_sidebar_styles()

    st.markdown(
        """
        <div class="sidebar-section-heading">
            <i class="bi bi-diagram-3"></i>
            <span>功能目錄</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    default_page = st.session_state.get("cisco_active_page", page_keys[0])
    default_index = page_keys.index(default_page) if default_page in page_keys else 0

    glyphs = {name: PAGE_ICON_EMOJI.get(name, "•") for name in page_keys}
    with st.container():
        st.markdown("<div class='sidebar-radio sidebar-radio--cisco'>", unsafe_allow_html=True)
        selection = st.radio(
            "功能選單",
            options=page_keys,
            index=default_index,
            format_func=lambda key: f"{glyphs[key]} {key}",
            key="cisco_sidebar_menu",
            label_visibility="collapsed",
        )
        st.markdown("</div>", unsafe_allow_html=True)

    st.session_state["cisco_active_page"] = selection
    return selection


def render() -> None:
    _configure_page()
    st.session_state.setdefault("fortinet_menu_collapse", False)

    page_keys = list(PAGES.keys())

    with st.sidebar:
        selection = _render_navigation(page_keys)

        description = PAGE_DESCRIPTIONS.get(selection, "")
        if description:
            st.markdown(
                f"<p class='sidebar-menu-description'>{html.escape(description)}</p>",
                unsafe_allow_html=True,
            )

    PAGES[selection]()
