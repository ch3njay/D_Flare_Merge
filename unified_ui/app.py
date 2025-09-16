"""跨品牌統一介面。"""
from __future__ import annotations

import streamlit as st
from streamlit.errors import StreamlitAPIException

if __package__ in (None, ""):
    # Support running "streamlit run unified_ui/app.py" by adding the current
    # directory to ``sys.path`` so the sibling modules can be imported without
    # package context.
    import sys
    from pathlib import Path

    _MODULE_ROOT = Path(__file__).resolve().parent
    if str(_MODULE_ROOT) not in sys.path:
        sys.path.insert(0, str(_MODULE_ROOT))

    from cisco_module import pages as cisco_pages  # type: ignore[import]
    from fortinet_module import pages as fortinet_pages  # type: ignore[import]
else:
    from .cisco_module import pages as cisco_pages
    from .fortinet_module import pages as fortinet_pages

try:
    st.set_page_config(page_title="D-FLARE Unified Dashboard", page_icon="🛡️", layout="wide")
except StreamlitAPIException:
    pass

BRAND_RENDERERS = {
    "Fortinet": fortinet_pages.render,
    "Cisco": cisco_pages.render,
}
BRAND_DESCRIPTIONS = {
    "Fortinet": "Fortinet 版本提供完整的訓練、ETL、推論與通知流程。",
    "Cisco": "Cisco 版本專注於 ASA log 擷取、模型推論與跨平台通知。",
}
BRAND_TITLES = {
    "Fortinet": "Fortinet D-FLARE 控制台",
    "Cisco": "Cisco D-FLARE 控制台",
}
SIDEBAR_TITLE = "D-FLARE Unified"
SIDEBAR_TAGLINE = "跨品牌威脅分析控制台。"


def _ensure_session_defaults() -> None:
    st.session_state.setdefault("unified_brand", "Fortinet")
    st.session_state.setdefault("fortinet_menu_collapse", False)


def _apply_sidebar_style() -> None:
    collapsed = st.session_state.get("fortinet_menu_collapse", False)
    sidebar_width = "72px" if collapsed else "280px"
    st.markdown(
        f"""
        <style>
        div[data-testid="stSidebar"] {{
            width: {sidebar_width};
            min-width: {sidebar_width};
            background-color: #1f2937;
            transition: width 0.3s ease;
        }}
        div[data-testid="stSidebar"] section[data-testid="stSidebarContent"] > div {{
            padding: 0;
        }}
        div[data-testid="stSidebar"] .sidebar-shell {{
            padding: 0.25rem 0.75rem 0.75rem;
        }}
        div[data-testid="stSidebar"] .sidebar-toggle button {{
            width: 100%;
            background-color: transparent;
            color: #f9fafb;
            border: none;
            font-size: 1.35rem;
            padding: 0.25rem 0.5rem;
        }}
        div[data-testid="stSidebar"] .sidebar-toggle button:hover {{
            background-color: rgba(255, 255, 255, 0.08);
        }}
        div[data-testid="stSidebar"] .sidebar-brand-text h1 {{
            font-size: 1.25rem;
            color: #f9fafb;
        }}
        div[data-testid="stSidebar"] .sidebar-brand-text p {{
            color: #9ca3af;
            margin-bottom: 0.25rem;
        }}
        div[data-testid="stSidebar"] .sidebar-brand-select {{
            margin-top: 0.5rem;
        }}
        div[data-testid="stSidebar"] .sidebar-brand-select label {{
            color: #d1d5db;
            font-weight: 600;
        }}
        div[data-testid="stSidebar"] .sidebar-brand-select div[data-baseweb="select"] > div {{
            background-color: #111827;
            border: 1px solid #374151;
            color: #f9fafb;
        }}
        div[data-testid="stSidebar"] .sidebar-brand-select div[data-baseweb="select"] svg {{
            color: #9ca3af;
        }}
        div[data-testid="stSidebar"] .sidebar-brand-hint {{
            color: #9ca3af;
            font-size: 0.85rem;
            margin: 0.5rem 0 0;
        }}
        .menu-collapsed .sidebar-brand-text,
        .menu-collapsed .sidebar-brand-hint {{
            display: none;
        }}
        .menu-collapsed .sidebar-brand-select label {{
            display: none;
        }}
        .menu-collapsed .sidebar-toggle button {{
            text-align: center;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def _render_sidebar() -> str:
    options = list(BRAND_RENDERERS.keys())
    collapsed = st.session_state.get("fortinet_menu_collapse", False)

    with st.sidebar:
        menu_class = "menu-collapsed" if collapsed else "menu-expanded"
        st.markdown(f"<div class='sidebar-shell {menu_class}'>", unsafe_allow_html=True)
        st.markdown("<div class='sidebar-toggle'>", unsafe_allow_html=True)
        if st.button("☰", key="unified_sidebar_toggle"):
            st.session_state["fortinet_menu_collapse"] = not collapsed
            st.experimental_rerun()
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("<div class='sidebar-brand-text'>", unsafe_allow_html=True)
        st.title(SIDEBAR_TITLE)
        st.caption(SIDEBAR_TAGLINE)
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("<div class='sidebar-brand-select'>", unsafe_allow_html=True)
        label_visibility = "collapsed" if collapsed else "visible"
        brand = st.selectbox(
            "選擇品牌",
            options,
            key="unified_brand",
            label_visibility=label_visibility,
        )
        st.markdown("</div>", unsafe_allow_html=True)

        if not collapsed:
            hint = BRAND_DESCRIPTIONS.get(brand)
            if hint:
                st.markdown(f"<p class='sidebar-brand-hint'>{hint}</p>", unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)
        st.divider()

    return brand


def _render_main_header(brand: str) -> None:
    title = BRAND_TITLES.get(brand, f"{brand} D-FLARE 控制台")
    st.title(title)
    description = BRAND_DESCRIPTIONS.get(brand, "")
    if description:
        st.caption(description)
    st.divider()


def main() -> None:
    _ensure_session_defaults()
    _apply_sidebar_style()
    brand = _render_sidebar()
    _render_main_header(brand)

    renderer = BRAND_RENDERERS.get(brand)
    if renderer is None:
        st.warning("選擇的品牌尚未提供統一介面內容。")
        return

    renderer()


if __name__ == "__main__":
    main()
