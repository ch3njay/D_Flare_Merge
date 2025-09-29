"""Unified Streamlit entry point that routes to brand-specific UIs."""
from __future__ import annotations

from typing import Callable, Dict

import streamlit as st
from streamlit.delta_generator import DeltaGenerator

import cisco_ui
import fortinet_ui
from theme_controller import apply_theme, available_themes

BRAND_ROUTERS: Dict[str, Callable[[], None]] = {
    "Fortinet": fortinet_ui.render,
    "Cisco": cisco_ui.render,
}

BRAND_ICONS = {"Fortinet": "🛡️", "Cisco": "📡"}
BRAND_DESCRIPTIONS = {
    "Fortinet": "整合訓練、GPU ETL、推論與通知的 Fortinet 品牌控制台。",
    "Cisco": "專注 ASA log 擷取與推論的 Cisco 品牌控制台。",
}


def _select_brand(container: DeltaGenerator) -> str:
    options = list(BRAND_ROUTERS.keys())
    default = st.session_state.get("selected_brand", options[0])
    index = options.index(default) if default in options else 0
    with container:
        brand = st.selectbox(
            "選擇品牌",
            options,
            index=index,
            format_func=lambda x: f"{BRAND_ICONS[x]} {x}",
        )
    st.session_state["selected_brand"] = brand
    return brand


def _select_theme(container: DeltaGenerator) -> str:
    themes = available_themes()
    keys = list(themes.keys())
    default = st.session_state.get("active_theme", keys[0])
    index = keys.index(default) if default in keys else 0
    with container:
        theme = st.selectbox(
            "按鈕主題",
            keys,
            index=index,
            format_func=lambda key: themes[key],
        )
    return theme


def main() -> None:
    """Streamlit app entry point used by ``streamlit run ui_app.py``."""

    st.set_page_config(page_title="D-FLARE Unified Dashboard", page_icon="🛡️", layout="wide")

    st.sidebar.image("LOGO.png", use_column_width=True)

    brand_col, theme_col = st.columns([1, 1])
    brand = _select_brand(brand_col)
    theme_key = _select_theme(theme_col)
    apply_theme(theme_key)

    icon = BRAND_ICONS.get(brand, "🛡️")
    st.title(f"{icon} {brand} D-FLARE 控制台")
    st.caption(BRAND_DESCRIPTIONS.get(brand, ""))

    BRAND_ROUTERS[brand]()


if __name__ == "__main__":
    main()
