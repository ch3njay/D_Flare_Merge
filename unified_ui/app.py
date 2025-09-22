"""跨品牌統一介面。"""
from __future__ import annotations

import html
from typing import Iterator, Sequence, Tuple, TypeVar

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
DEFAULT_THEME = {
    "start": "#6366f1",
    "end": "#8b5cf6",
    "shadow": "rgba(99, 102, 241, 0.45)",
    "icon": "🧭",
    "eyebrow": "Unified Threat Analytics",
}
BRAND_THEMES = {
    "Fortinet": {
        "start": "#f97316",
        "end": "#ef4444",
        "shadow": "rgba(239, 68, 68, 0.45)",
        "icon": "🛡️",
        "eyebrow": "Fortinet 生態整合",
    },
    "Cisco": {
        "start": "#38bdf8",
        "end": "#2563eb",
        "shadow": "rgba(37, 99, 235, 0.45)",
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
SIDEBAR_TITLE = "D-FLARE Unified"
SIDEBAR_TAGLINE = "跨品牌威脅分析控制台。"

_T = TypeVar("_T")


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
        div[data-testid="stAppViewContainer"] {{
            background: radial-gradient(circle at top left, rgba(148, 163, 184, 0.25), transparent 45%),
                        radial-gradient(circle at 20% 80%, rgba(59, 130, 246, 0.18), transparent 40%),
                        linear-gradient(180deg, #0f172a 0%, #111827 38%, #1f2937 100%);
        }}
        div[data-testid="stAppViewContainer"] .main .block-container {{
            padding: 2.5rem 3rem 3.25rem;
            border-radius: 24px;
            background: rgba(248, 250, 252, 0.92);
            box-shadow: 0 32px 60px -25px rgba(15, 23, 42, 0.6);
            border: 1px solid rgba(148, 163, 184, 0.22);
            backdrop-filter: blur(18px);
        }}
        @media (max-width: 992px) {{
            div[data-testid="stAppViewContainer"] .main .block-container {{
                padding: 1.75rem 1.5rem 2.25rem;
                border-radius: 20px;
            }}
        }}
        .brand-hero {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 1.5rem;
            padding: 1.75rem 2rem;
            border-radius: 20px;
            position: relative;
            overflow: hidden;
            background: linear-gradient(135deg, var(--accent-start), var(--accent-end));
            color: #f9fafb;
            box-shadow: 0 28px 48px -28px var(--accent-shadow);
        }}
        .brand-hero::after {{
            content: "";
            position: absolute;
            inset: 0;
            background: radial-gradient(circle at top right, rgba(255, 255, 255, 0.35), transparent 60%);
            opacity: 0.65;
            pointer-events: none;
        }}
        .brand-hero__content {{
            position: relative;
            z-index: 1;
        }}
        .brand-hero__eyebrow {{
            font-size: 0.85rem;
            text-transform: uppercase;
            letter-spacing: 0.12em;
            font-weight: 600;
            opacity: 0.85;
        }}
        .brand-hero h1 {{
            margin: 0.35rem 0 0.75rem;
            font-size: 2rem;
            font-weight: 700;
            letter-spacing: 0.02em;
        }}
        .brand-hero p {{
            margin: 0;
            font-size: 1.05rem;
            line-height: 1.6;
            color: rgba(249, 250, 251, 0.85);
        }}
        .brand-hero__badge {{
            position: relative;
            z-index: 1;
            padding: 0.65rem 1.6rem;
            border-radius: 999px;
            border: 1px solid rgba(255, 255, 255, 0.45);
            background: rgba(15, 23, 42, 0.28);
            font-weight: 600;
            display: inline-flex;
            align-items: center;
            gap: 0.55rem;
            font-size: 1rem;
            box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.35);
        }}
        .feature-card {{
            margin-top: 1.2rem;
            padding: 1.25rem 1.35rem;
            border-radius: 18px;
            border: 1px solid rgba(148, 163, 184, 0.25);
            background: linear-gradient(135deg, rgba(255, 255, 255, 0.95), rgba(226, 232, 240, 0.8));
            box-shadow: 0 26px 45px -28px rgba(30, 41, 59, 0.55);
            transition: transform 0.2s ease, box-shadow 0.2s ease;
        }}
        .feature-card:hover {{
            transform: translateY(-4px);
            box-shadow: 0 32px 56px -26px rgba(30, 41, 59, 0.55);
        }}
        .feature-card__icon {{
            font-size: 1.75rem;
            margin-bottom: 0.65rem;
        }}
        .feature-card__title {{
            margin: 0 0 0.35rem;
            font-size: 1.05rem;
            font-weight: 600;
            color: #0f172a;
        }}
        .feature-card__desc {{
            margin: 0;
            color: #475569;
            line-height: 1.6;
            font-size: 0.95rem;
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


def _chunked(seq: Sequence[_T], size: int) -> Iterator[Sequence[_T]]:
    for idx in range(0, len(seq), size):
        yield seq[idx : idx + size]


def _render_brand_highlights(brand: str) -> bool:
    highlights = BRAND_HIGHLIGHTS.get(brand)
    if not highlights:
        return False

    for row in _chunked(highlights, 3):
        columns = st.columns(len(row))
        for column, (icon, title, desc) in zip(columns, row):
            column.markdown(
                f"""
                <div class="feature-card">
                    <div class="feature-card__icon">{html.escape(icon)}</div>
                    <h4 class="feature-card__title">{html.escape(title)}</h4>
                    <p class="feature-card__desc">{html.escape(desc)}</p>
                </div>
                """,
                unsafe_allow_html=True,
            )
    return True


def _render_main_header(brand: str) -> None:
    title = BRAND_TITLES.get(brand, f"{brand} D-FLARE 控制台")
    description = BRAND_DESCRIPTIONS.get(brand, "")
    theme = BRAND_THEMES.get(brand, DEFAULT_THEME)
    description_html = f"<p>{html.escape(description)}</p>" if description else ""
    st.markdown(
        f"""
        <div class="brand-hero" style="--accent-start: {theme['start']}; --accent-end: {theme['end']}; --accent-shadow: {theme['shadow']}">
            <div class="brand-hero__content">
                <div class="brand-hero__eyebrow">{html.escape(theme['eyebrow'])}</div>
                <h1>{html.escape(title)}</h1>
                {description_html}
            </div>
            <span class="brand-hero__badge">{html.escape(theme['icon'])} {html.escape(brand)}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )


def main() -> None:
    _ensure_session_defaults()
    _apply_sidebar_style()
    brand = _render_sidebar()
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
