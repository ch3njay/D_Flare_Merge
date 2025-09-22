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
# [ADDED] 明暗主題配色設定
THEME_PRESETS = {
    "dark": {
        "color_mode": "dark",
        "background": "#0f172a",
        "surface": "#1e293b",
        "surface_muted": "#15213b",
        "surface_border": "rgba(148, 163, 184, 0.22)",
        "surface_shadow": "0 32px 55px -32px rgba(8, 15, 27, 0.9)",
        "sidebar_background": "#1e293b",
        "sidebar_text": "#f1f5f9",
        "sidebar_muted": "#94a3b8",
        "sidebar_button_hover": "rgba(148, 163, 184, 0.16)",
        "text_primary": "#f1f5f9",
        "text_secondary": "#94a3b8",
        "card_background": "#1f2937",
        "card_border": "rgba(148, 163, 184, 0.2)",
        "card_shadow": "0 26px 42px -32px rgba(8, 15, 27, 0.9)",
        "button_background": "#2563eb",
        "button_hover": "#1d4ed8",
        "warning_yellow": "#facc15",
        "warning_red": "#ef4444",
        "expander_header": "#243147",
        "expander_background": "#16213b",
        "code_background": "#111827",
        "input_background": "#111827",
        "input_border": "#334155",
        "muted_border": "#27344a",
    },
    "light": {
        "color_mode": "light",
        "background": "#f8fafc",
        "surface": "#f1f5f9",
        "surface_muted": "#e2e8f0",
        "surface_border": "#d2d9e4",
        "surface_shadow": "0 24px 48px -32px rgba(15, 23, 42, 0.14)",
        "sidebar_background": "#e2e8f0",
        "sidebar_text": "#0f172a",
        "sidebar_muted": "#475569",
        "sidebar_button_hover": "rgba(148, 163, 184, 0.32)",
        "text_primary": "#0f172a",
        "text_secondary": "#475569",
        "card_background": "#ffffff",
        "card_border": "#d0d7e3",
        "card_shadow": "0 22px 36px -26px rgba(15, 23, 42, 0.18)",
        "button_background": "#2563eb",
        "button_hover": "#1e40af",
        "warning_yellow": "#ca8a04",
        "warning_red": "#b91c1c",
        "expander_header": "#d9e2ef",
        "expander_background": "#edf2fb",
        "code_background": "#e2e8f0",
        "input_background": "#ffffff",
        "input_border": "#cbd5f5",
        "muted_border": "#cbd5f5",
    },
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
        "eyebrow": "Fortinet 安全平台",
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
# Sidebar tagline removed for a cleaner layout.  # [REMOVED]

_T = TypeVar("_T")


def _ensure_session_defaults() -> None:  # [MODIFIED]
    st.session_state.setdefault("unified_brand", "Fortinet")  # [MODIFIED]
    st.session_state.setdefault("fortinet_menu_collapse", False)  # [MODIFIED]
    st.session_state.setdefault("unified_theme", "dark")  # [ADDED]


def _apply_theme_styles(collapsed: bool, palette: dict[str, str]) -> None:  # [MODIFIED]
    sidebar_width = "88px" if collapsed else "296px"  # [MODIFIED]
    st.markdown(  # [MODIFIED]
        f"""
        <style>
        :root {{
            color-scheme: {palette['color_mode']};
            --app-bg: {palette['background']};
            --app-surface: {palette['surface']};
            --app-surface-muted: {palette['surface_muted']};
            --app-surface-border: {palette['surface_border']};
            --app-surface-shadow: {palette['surface_shadow']};
            --text-primary: {palette['text_primary']};
            --text-secondary: {palette['text_secondary']};
            --accent: {palette['button_background']};
            --accent-hover: {palette['button_hover']};
            --sidebar-bg: {palette['sidebar_background']};
            --sidebar-text: {palette['sidebar_text']};
            --sidebar-muted: {palette['sidebar_muted']};
            --sidebar-button-hover: {palette['sidebar_button_hover']};
            --card-background: {palette['card_background']};
            --card-border: {palette['card_border']};
            --card-shadow: {palette['card_shadow']};
            --warning-yellow: {palette['warning_yellow']};
            --warning-red: {palette['warning_red']};
            --expander-header: {palette['expander_header']};
            --expander-background: {palette['expander_background']};
            --code-background: {palette['code_background']};
            --input-background: {palette['input_background']};
            --input-border: {palette['input_border']};
            --muted-border: {palette['muted_border']};
        }}

        * {{
            transition: background-color 0.25s ease, color 0.25s ease, border-color 0.25s ease;
        }}

        html, body, div[data-testid="stAppViewContainer"] {{
            background-color: var(--app-bg);
        }}

        body {{
            color: var(--text-primary);
            font-family: "Noto Sans TC", "Segoe UI", system-ui, -apple-system, BlinkMacSystemFont, sans-serif;
        }}

        h1, h2, h3, h4, h5, h6 {{
            color: var(--text-primary);
        }}

        p, label, span, li {{
            color: var(--text-primary);
        }}

        small, .stCaption, .stMarkdown small, div[data-testid="stMarkdown"] em {{
            color: var(--text-secondary) !important;
        }}

        a {{
            color: var(--accent);
        }}

        a:hover {{
            color: var(--accent-hover);
        }}

        code, pre {{
            background: var(--code-background);
            color: var(--text-primary);
            border-radius: 10px;
        }}

        div[data-testid="stSidebar"] {{
            width: {sidebar_width};
            min-width: {sidebar_width};
            background: var(--sidebar-bg);
            border-right: 1px solid var(--app-surface-border);
            padding: 1.25rem 0.9rem 2rem;
            transition: width 0.3s ease;
        }}

        div[data-testid="stSidebar"] section[data-testid="stSidebarContent"] {{
            padding: 0;
        }}

        div[data-testid="stSidebar"] h1,
        div[data-testid="stSidebar"] label,
        div[data-testid="stSidebar"] span,
        div[data-testid="stSidebar"] p {{
            color: var(--sidebar-text) !important;
        }}

        div[data-testid="stSidebar"] .stMarkdown small,
        div[data-testid="stSidebar"] .stCaption {{
            color: var(--sidebar-muted) !important;
        }}

        div[data-testid="stSidebar"] hr {{
            margin: 1.5rem 0 0;
            border-color: var(--muted-border);
        }}

        div[data-testid="stSidebar"] .stButton > button {{
            width: 100%;
            background: transparent;
            color: var(--sidebar-text);
            border: 1px solid var(--muted-border);
            border-radius: 12px;
            font-weight: 600;
            padding: 0.55rem 0.75rem;
        }}

        div[data-testid="stSidebar"] .stButton > button:hover {{
            background: var(--sidebar-button-hover);
            border-color: transparent;
            color: var(--sidebar-text);
        }}

        div[data-testid="stSidebar"] .stButton > button:focus-visible {{
            outline: 2px solid var(--accent);
            outline-offset: 2px;
        }}

        .stButton > button {{
            background: var(--accent);
            color: #f8fafc;
            border-radius: 12px;
            border: none;
            font-weight: 600;
            padding: 0.6rem 1.2rem;
            box-shadow: 0 12px 22px -16px rgba(37, 99, 235, 0.65);
        }}

        .stButton > button:hover {{
            background: var(--accent-hover);
        }}

        .stButton > button:focus-visible {{
            outline: 2px solid var(--accent-hover);
            outline-offset: 2px;
        }}

        div[data-testid="stAppViewContainer"] .main {{
            padding: 0;
        }}

        div[data-testid="stAppViewContainer"] .main .block-container {{
            background: var(--app-surface);
            border-radius: 24px;
            border: 1px solid var(--app-surface-border);
            box-shadow: var(--app-surface-shadow);
            padding: 2.4rem 3rem 3.1rem;
        }}

        @media (max-width: 992px) {{
            div[data-testid="stAppViewContainer"] .main .block-container {{
                padding: 1.8rem 1.5rem 2.2rem;
                border-radius: 20px;
            }}
        }}

        div[data-testid="stMarkdown"] p {{
            color: var(--text-primary);
        }}

        hr {{
            border-color: var(--muted-border);
        }}

        .stTabs [role="tablist"] {{
            gap: 0.5rem;
            border-bottom: 1px solid var(--muted-border);
            padding-bottom: 0.25rem;
        }}

        .stTabs [role="tab"] {{
            background: transparent;
            color: var(--text-secondary);
            border: none;
            border-bottom: 2px solid transparent;
            padding: 0.4rem 0.6rem;
            font-weight: 500;
        }}

        .stTabs [role="tab"][aria-selected="true"] {{
            color: var(--text-primary);
            border-color: var(--accent);
            font-weight: 600;
        }}

        div[data-testid="stExpander"] > details {{
            background: var(--expander-background);
            border-radius: 16px;
            border: 1px solid var(--muted-border);
            overflow: hidden;
        }}

        div[data-testid="stExpander"] > details > summary {{
            background: var(--expander-header);
            color: var(--text-primary);
            padding: 0.85rem 1rem;
            font-weight: 600;
        }}

        div[data-testid="stExpander"] > details > summary:hover {{
            filter: brightness(1.05);
        }}

        div[data-testid="stExpander"] > details div[data-testid="stExpanderContent"] {{
            padding: 0.85rem 1rem 1rem;
            color: var(--text-primary);
        }}

        .brand-hero {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 1.5rem;
            padding: 1.8rem 2.1rem;
            border-radius: 22px;
            position: relative;
            overflow: hidden;
            background: linear-gradient(135deg, var(--accent-start), var(--accent-end));
            box-shadow: 0 28px 52px -28px var(--accent-shadow);
            color: #f8fafc;
        }}

        .brand-hero::after {{
            content: "";
            position: absolute;
            inset: 0;
            background: radial-gradient(circle at top right, rgba(255, 255, 255, 0.32), transparent 60%);
            opacity: 0.7;
            pointer-events: none;
        }}

        .brand-hero__content {{
            position: relative;
            z-index: 1;
        }}

        .brand-hero__eyebrow {{
            font-size: 0.82rem;
            text-transform: uppercase;
            letter-spacing: 0.16em;
            font-weight: 600;
            opacity: 0.92;
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
            color: rgba(241, 245, 249, 0.86);
        }}

        .brand-hero__badge {{
            position: relative;
            z-index: 1;
            padding: 0.55rem 1.4rem;
            border-radius: 999px;
            border: 1px solid rgba(255, 255, 255, 0.48);
            background: rgba(15, 23, 42, 0.28);
            font-weight: 600;
            display: inline-flex;
            align-items: center;
            gap: 0.55rem;
            font-size: 0.95rem;
            box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.35);
        }}

        .feature-card {{
            margin-top: 1.25rem;
            padding: 1.2rem 1.3rem;
            border-radius: 20px;
            border: 1px solid var(--card-border);
            background: var(--card-background);
            box-shadow: var(--card-shadow);
            transition: transform 0.2s ease, box-shadow 0.2s ease;
        }}

        .feature-card:hover {{
            transform: translateY(-4px);
            box-shadow: 0 32px 56px -30px rgba(37, 99, 235, 0.35);
        }}

        .feature-card__icon {{
            font-size: 1.75rem;
            margin-bottom: 0.65rem;
        }}

        .feature-card__title {{
            margin: 0 0 0.35rem;
            font-size: 1.05rem;
            font-weight: 600;
            color: var(--text-primary);
        }}

        .feature-card__desc {{
            margin: 0;
            color: var(--text-secondary);
            line-height: 1.6;
            font-size: 0.95rem;
        }}

        .stSelectbox label,
        .stMultiSelect label,
        .stRadio > label,
        .stCheckbox > label {{
            font-weight: 600;
        }}

        .stSelectbox div[data-baseweb="select"],
        .stMultiSelect div[data-baseweb="select"] {{
            border-radius: 12px;
        }}

        .stSelectbox div[data-baseweb="select"] > div,
        .stMultiSelect div[data-baseweb="select"] > div {{
            background: var(--input-background);
            border: 1px solid var(--input-border);
            color: var(--text-primary);
        }}

        .stSelectbox div[data-baseweb="select"] svg,
        .stMultiSelect div[data-baseweb="select"] svg {{
            color: var(--text-secondary);
        }}

        div[data-baseweb="popover"] {{
            background: var(--card-background);
            border-radius: 12px;
            border: 1px solid var(--card-border);
            box-shadow: var(--card-shadow);
        }}

        div[data-baseweb="popover"] ul[role="listbox"] li {{
            color: var(--text-primary);
            background: var(--card-background);
        }}

        div[data-baseweb="popover"] ul[role="listbox"] li:hover {{
            background: var(--app-surface-muted);
        }}

        .stTextInput input,
        .stNumberInput input,
        .stTextArea textarea {{
            background: var(--input-background);
            border: 1px solid var(--input-border);
            color: var(--text-primary);
            border-radius: 12px;
        }}

        .stTextInput input:focus,
        .stNumberInput input:focus,
        .stTextArea textarea:focus {{
            border-color: var(--accent);
            box-shadow: 0 0 0 1px var(--accent);
        }}

        div[data-testid="stSidebar"] .stSelectbox div[data-baseweb="select"] > div {{
            background: var(--input-background);
        }}

        div[data-testid="stSidebar"] .stSelectbox div[data-baseweb="select"] > div:hover {{
            border-color: transparent;
        }}

        .stAlert {{
            border-radius: 16px;
            border: 1px solid var(--muted-border);
            background: var(--app-surface);
        }}

        .stAlert div[role="alert"] p {{
            color: var(--text-primary);
        }}

        .stAlert[data-baseweb="notification"] svg {{
            color: var(--accent);
        }}

        .stAlert[data-baseweb="notification"] [data-icon="warning"] {{
            color: var(--warning-yellow);
        }}

        .stAlert[data-baseweb="notification"] [data-icon="error"] {{
            color: var(--warning-red);
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def _render_sidebar(current_theme: str) -> str:  # [MODIFIED]
    options = list(BRAND_RENDERERS.keys())  # [MODIFIED]
    collapsed = st.session_state.get("fortinet_menu_collapse", False)  # [MODIFIED]

    with st.sidebar:  # [MODIFIED]
        if collapsed:  # [ADDED]
            if st.button("☰", key="unified_sidebar_toggle"):  # [MODIFIED]
                st.session_state["fortinet_menu_collapse"] = False  # [MODIFIED]
            if st.button("🌙 / ☀️", key="unified_theme_toggle"):  # [ADDED]
                st.session_state["unified_theme"] = "light" if current_theme == "dark" else "dark"  # [ADDED]
        else:  # [ADDED]
            toggle_col, theme_col = st.columns(2)  # [MODIFIED]
            with toggle_col:  # [ADDED]
                if st.button("☰", key="unified_sidebar_toggle"):  # [MODIFIED]
                    st.session_state["fortinet_menu_collapse"] = True  # [MODIFIED]
            with theme_col:  # [ADDED]
                if st.button("🌙 / ☀️", key="unified_theme_toggle"):  # [ADDED]
                    st.session_state["unified_theme"] = "light" if current_theme == "dark" else "dark"  # [ADDED]

        if not collapsed:  # [MODIFIED]
            st.title(SIDEBAR_TITLE)  # [MODIFIED]

        label_visibility = "collapsed" if collapsed else "visible"  # [MODIFIED]
        brand = st.selectbox(  # [MODIFIED]
            "選擇品牌",  # [MODIFIED]
            options,  # [MODIFIED]
            key="unified_brand",  # [MODIFIED]
            label_visibility=label_visibility,  # [MODIFIED]
        )

        st.divider()  # [MODIFIED]

    return brand  # [MODIFIED]


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
    _ensure_session_defaults()  # [MODIFIED]
    current_theme = st.session_state.get("unified_theme", "dark")  # [ADDED]
    brand = _render_sidebar(current_theme)  # [MODIFIED]
    collapsed = st.session_state.get("fortinet_menu_collapse", False)  # [ADDED]
    theme_key = st.session_state.get("unified_theme", current_theme)  # [ADDED]
    palette = THEME_PRESETS.get(theme_key, THEME_PRESETS["dark"])  # [ADDED]
    _apply_theme_styles(collapsed, palette)  # [MODIFIED]
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
