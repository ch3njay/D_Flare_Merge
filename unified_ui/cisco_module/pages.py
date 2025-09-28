"""Cisco 介面在統一平台中的轉接層。"""
from __future__ import annotations

import html
from urllib.parse import urlencode

import streamlit as st

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

QUERY_KEY = "cisco_page"


def _format_label(label: str) -> str:
    icon_name = PAGE_ICONS.get(label)
    if icon_name and st.session_state.get("_unified_bootstrap_icons"):
        icon_markup = f"<i class='bi bi-{html.escape(icon_name)}'></i>"
    else:
        icon_markup = html.escape(PAGE_EMOJIS.get(label, "📄"))
    text = html.escape(label)
    return f"<span class='sidebar-nav__icon'>{icon_markup}</span><span class='sidebar-nav__label'>{text}</span>"


def _build_href(params: dict[str, list[str]]) -> str:
    return "?" + urlencode(params, doseq=True)


def _render_navigation(page_keys: list[str]) -> str:
    query_params = st.experimental_get_query_params()
    state_key = "cisco_active_page"
    default_page = st.session_state.get(state_key, page_keys[0])
    current = query_params.get(QUERY_KEY, [default_page])[0]
    if current not in page_keys:
        current = page_keys[0]

    st.session_state[state_key] = current

    params_serializable = {
        key: value[0] if isinstance(value, list) and len(value) == 1 else value
        for key, value in query_params.items()
    }
    if params_serializable.get(QUERY_KEY) != current:
        params_serializable[QUERY_KEY] = current
        st.experimental_set_query_params(**params_serializable)

    nav_items: list[str] = []
    for label in page_keys:
        merged_params = {**query_params, QUERY_KEY: [label]}
        href = html.escape(_build_href(merged_params), quote=True)
        nav_items.append(
            f"<a class='sidebar-nav__item' data-active={'true' if label == current else 'false'} href='{href}'>{_format_label(label)}</a>"
        )

    st.markdown("<div class='sidebar-nav sidebar-nav--cisco'>" + "".join(nav_items) + "</div>", unsafe_allow_html=True)
    return current


def _configure_page() -> None:
    configure = getattr(cisco_app, "_configure_page", None)
    if callable(configure):
        configure()


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
