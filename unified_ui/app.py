"""跨品牌統一介面。"""
from __future__ import annotations

import streamlit as st
from streamlit.errors import StreamlitAPIException

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


def _select_brand() -> str:
    if "unified_brand" not in st.session_state:
        st.session_state["unified_brand"] = "Fortinet"
    current = st.session_state["unified_brand"]
    options = list(BRAND_RENDERERS.keys())

    col1, col2 = st.columns([1, 3])
    with col1:
        brand = st.selectbox("選擇品牌", options, index=options.index(current))
    with col2:
        st.title("D-FLARE 跨品牌控制台")
        st.caption(BRAND_DESCRIPTIONS.get(brand, ""))
    st.session_state["unified_brand"] = brand
    st.divider()
    return brand


def main() -> None:
    brand = _select_brand()
    BRAND_RENDERERS[brand]()


if __name__ == "__main__":
    main()
