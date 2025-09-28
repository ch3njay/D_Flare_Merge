"""跨品牌統一介面的現代化版本。"""
from __future__ import annotations

import html
import sys
from pathlib import Path
from typing import Iterator, Sequence, Tuple, TypeVar

import streamlit as st
from streamlit.errors import StreamlitAPIException

# 添加專案根目錄到 Python 路徑
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

# 添加 unified_ui 目錄到 Python 路徑
_MODULE_ROOT = Path(__file__).resolve().parent
if str(_MODULE_ROOT) not in sys.path:
    sys.path.insert(0, str(_MODULE_ROOT))

from unified_ui import theme_controller  # noqa: E402

if __package__ in (None, ""):
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
    st.set_page_config(
        page_title="D-FLARE Unified Dashboard",
        page_icon="🛡️",
        layout="wide",
    )
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
DEFAULT_THEME = {
    "gradient": "linear-gradient(135deg, var(--primaryColor), color-mix(in srgb, var(--primaryColor) 70%, var(--textColor) 30%))",
    "icon": "🧭",
    "eyebrow": "Unified Threat Analytics",
}
BRAND_THEMES = {
    "Fortinet": {
        "gradient": "linear-gradient(135deg, #ff6a00, #ff8c42)",
        "icon": "🛡️",
        "eyebrow": "Fortinet 安全平台",
    },
    "Cisco": {
        "gradient": "linear-gradient(135deg, #0072ff, #00c6ff)",
        "icon": "📡",
        "eyebrow": "Cisco 安全平台",
    },
}
Highlight = Tuple[str, str, str]
BRAND_HIGHLIGHTS: dict[str, list[Highlight]] = {
    "Fortinet": [
        ("🧠", "全流程管控", "訓練、ETL、推論到通知一次就緒，支援多階段自動化。"),
        ("🚀", "GPU ETL 加速", "透過 GPU 與批次策略處理大量 log，縮短等待時間。"),
        ("🔔", "智慧告警", "串接 Discord、LINE 與 Gemini，將關鍵事件即時推播給 SOC。"),
    ],
    "Cisco": [
        ("📡", "ASA 日誌擷取", "針對 Cisco ASA 日誌格式優化的擷取與清洗流程。"),
        ("🤖", "模型推論指引", "依步驟完成資料上傳、模型載入與結果檢視，降低操作門檻。"),
        ("🌐", "跨平台告警", "彈性整合多種通訊渠道，將分析結果分送至各平台。"),
    ],
}
FEATURE_VARIANTS = {
    "全流程管控": "primary",
    "GPU ETL 加速": "secondary",
    "智慧告警": "alert",
    "ASA 日誌擷取": "primary",
    "模型推論指引": "secondary",
    "跨平台告警": "alert",
}
SIDEBAR_TITLE = "D-FLARE Unified"

_T = TypeVar("_T")


def _chunked(seq: Sequence[_T], size: int) -> Iterator[Sequence[_T]]:
    for idx in range(0, len(seq), size):
        yield seq[idx : idx + size]


def _ensure_session_defaults() -> None:
    theme_controller.inject_global_styles()
    st.session_state.setdefault("unified_brand", "Fortinet")
    if "fortinet_active_page" not in st.session_state:
        fortinet_pages_keys = list(getattr(fortinet_pages, "PAGES", {}).keys())
        if fortinet_pages_keys:
            st.session_state["fortinet_active_page"] = fortinet_pages_keys[0]
    if "cisco_active_page" not in st.session_state:
        cisco_pages_keys = list(getattr(cisco_pages, "PAGES", {}).keys())
        if cisco_pages_keys:
            st.session_state["cisco_active_page"] = cisco_pages_keys[0]


def _render_sidebar() -> str:
    options = list(BRAND_RENDERERS.keys())
    current_brand = st.session_state.get("unified_brand", options[0])
    default_index = options.index(current_brand) if current_brand in options else 0

    with st.sidebar:
        st.markdown(
            f"""
            <div class="sidebar-heading">
                <span class="sidebar-eyebrow">Unified Platform</span>
                <h1 class="sidebar-title">{html.escape(SIDEBAR_TITLE)}</h1>
            </div>
            """,
            unsafe_allow_html=True,
        )

        brand = st.selectbox(
            "選擇品牌",
            options,
            index=default_index,
            key="unified_brand",
        )

        st.markdown(
            f"<span class='sidebar-badge'>目前品牌：{html.escape(brand)}</span>",
            unsafe_allow_html=True,
        )

        st.markdown(
            "<p class='sidebar-note'>所有模組共用一致的互動風格，主題請使用右上角的官方切換按鈕。</p>",
            unsafe_allow_html=True,
        )

        st.divider()

    return brand


def _render_brand_highlights(brand: str) -> bool:
    highlights = BRAND_HIGHLIGHTS.get(brand)
    if not highlights:
        return False

    st.markdown('<div class="feature-cards-container">', unsafe_allow_html=True)

    data_brand = brand if brand in BRAND_THEMES else "Neutral"
    for row in _chunked(highlights, 3):
        columns = st.columns(len(row))
        for column, (icon, title, desc) in zip(columns, row):
            variant = FEATURE_VARIANTS.get(title, "secondary")
            column.markdown(
                f"""
                <div class="feature-card" data-brand="{html.escape(data_brand)}" data-variant="{html.escape(variant)}">
                    <div class="feature-card__icon">{html.escape(icon)}</div>
                    <h4 class="feature-card__title">{html.escape(title)}</h4>
                    <p class="feature-card__desc">{html.escape(desc)}</p>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.markdown('</div>', unsafe_allow_html=True)
    return True


def _render_main_header(brand: str) -> None:
    title = BRAND_TITLES.get(brand, f"{brand} D-FLARE 控制台")
    description = BRAND_DESCRIPTIONS.get(brand, "")
    theme = BRAND_THEMES.get(brand, DEFAULT_THEME)
    gradient = theme.get("gradient", DEFAULT_THEME["gradient"])
    description_html = f"<p>{html.escape(description)}</p>" if description else ""

    logo_src = theme_controller.get_logo_data_uri()
    visual_html = ""
    if logo_src:
        visual_html = (
            f"<div class=\"brand-hero__visual\"><img src=\"{logo_src}\" alt=\"{html.escape(title)} 標誌\" /></div>"
        )

    st.markdown(
        f"""
        <section class="brand-hero" data-brand="{html.escape(brand)}" style="background-image: {gradient};">
            {visual_html}
            <div class="brand-hero__content">
                <div class="brand-hero__eyebrow">{html.escape(theme.get('eyebrow', DEFAULT_THEME['eyebrow']))}</div>
                <h1>{html.escape(title)}</h1>
                {description_html}
            </div>
            <span class="brand-hero__badge">{html.escape(theme.get('icon', DEFAULT_THEME['icon']))} {html.escape(brand)}</span>
        </section>
        """,
        unsafe_allow_html=True,
    )


def main() -> None:
    """主應用程式入口點。"""

    _ensure_session_defaults()
    brand = _render_sidebar()

    if not brand:
        st.warning("請選擇品牌以載入內容。")
        return

    _render_main_header(brand)
    _render_brand_highlights(brand)
    st.divider()

    renderer = BRAND_RENDERERS.get(brand)
    if renderer is None:
        st.warning("選擇的品牌尚未提供統一介面內容。")
        return

    renderer()


if __name__ == "__main__":
    main()
