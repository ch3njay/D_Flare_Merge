"""跨品牌統一介面的現代化版本。"""
from __future__ import annotations

import html
from typing import Iterator, Sequence, Tuple, TypeVar

import streamlit as st
from streamlit.errors import StreamlitAPIException

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
THEME_PRESETS = {
    "dark": {
        "color_mode": "dark",
        "background": "#0b101f",
        "surface": "#11182a",
        "surface_muted": "#15203a",
        "surface_border": "rgba(148, 163, 184, 0.18)",
        "surface_shadow": "0 42px 88px -48px rgba(8, 12, 24, 0.92)",
        "sidebar_background": "#0f172a",
        "sidebar_text": "#f8fafc",
        "sidebar_muted": "#94a3b8",
        "sidebar_button_hover": "rgba(148, 163, 184, 0.16)",
        "sidebar_icon": "#f8fafc",
        "sidebar_icon_hover": "#ffb48a",
        "text_primary": "#e2e8f0",
        "text_secondary": "#94a3b8",
        "card_background": "#18233a",
        "card_border": "rgba(148, 163, 184, 0.22)",
        "card_shadow": "0 32px 62px -38px rgba(3, 7, 18, 0.85)",
        "primary": "#E85C1F",
        "primary_hover": "#FF6B2C",
        "primary_shadow": "rgba(232, 92, 31, 0.45)",
        "secondary_start": "#1ABC9C",
        "secondary_end": "#9B59B6",
        "secondary_hover": "#23cfb0",
        "warning": "#FFC107",
        "warning_emphasis": "#FF9800",
        "alert_icon_bg": "rgba(255, 193, 7, 0.18)",
        "alert_icon_color": "#ffffff",
        "expander_header": "#1b2740",
        "expander_background": "#111a2c",
        "code_background": "#0b1220",
        "input_background": "#0f172a",
        "input_border": "#334155",
        "muted_border": "rgba(148, 163, 184, 0.3)",
        "upload_background": "#13203a",
        "upload_border": "rgba(255, 255, 255, 0.18)",
        "upload_text": "#f8fafc",
        "hover_glow": "0 28px 60px -32px rgba(232, 92, 31, 0.55)",
        "sidebar_badge_background": "rgba(232, 92, 31, 0.18)",
    },
    "light": {
        "color_mode": "light",
        "background": "#f5f7fb",
        "surface": "#ffffff",
        "surface_muted": "#eef2ff",
        "surface_border": "#d8e0f0",
        "surface_shadow": "0 32px 64px -46px rgba(15, 23, 42, 0.2)",
        "sidebar_background": "#f1f5f9",
        "sidebar_text": "#0f172a",
        "sidebar_muted": "#64748b",
        "sidebar_button_hover": "rgba(15, 23, 42, 0.08)",
        "sidebar_icon": "#0f172a",
        "sidebar_icon_hover": "#FF6B2C",
        "text_primary": "#1f2937",
        "text_secondary": "#475569",
        "card_background": "#ffffff",
        "card_border": "#d9e2f1",
        "card_shadow": "0 24px 54px -34px rgba(15, 23, 42, 0.22)",
        "primary": "#FF6B2C",
        "primary_hover": "#FF834D",
        "primary_shadow": "rgba(255, 107, 44, 0.32)",
        "secondary_start": "#1ABC9C",
        "secondary_end": "#9B59B6",
        "secondary_hover": "#22a68c",
        "warning": "#FFC107",
        "warning_emphasis": "#ff9800",
        "alert_icon_bg": "rgba(255, 193, 7, 0.18)",
        "alert_icon_color": "#7a5200",
        "expander_header": "#e4ecfb",
        "expander_background": "#f5f8ff",
        "code_background": "#eef2ff",
        "input_background": "#ffffff",
        "input_border": "#d0d6eb",
        "muted_border": "#d8e0f0",
        "upload_background": "#ffffff",
        "upload_border": "#ffd4bc",
        "upload_text": "#0f172a",
        "hover_glow": "0 28px 60px -32px rgba(255, 107, 44, 0.35)",
        "sidebar_badge_background": "rgba(255, 107, 44, 0.16)",
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


def _ensure_session_defaults() -> None:
    st.session_state.setdefault("unified_brand", "Fortinet")
    st.session_state.setdefault("unified_theme", "dark")
    st.session_state.setdefault("fortinet_menu_collapse", False)
    st.session_state.setdefault("cisco_menu_collapse", False)


def _apply_theme_styles(palette: dict[str, str]) -> None:
    st.markdown(
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
            --sidebar-bg: {palette['sidebar_background']};
            --sidebar-text: {palette['sidebar_text']};
            --sidebar-muted: {palette['sidebar_muted']};
            --sidebar-button-hover: {palette['sidebar_button_hover']};
            --sidebar-icon: {palette['sidebar_icon']};
            --sidebar-icon-hover: {palette['sidebar_icon_hover']};
            --card-background: {palette['card_background']};
            --card-border: {palette['card_border']};
            --card-shadow: {palette['card_shadow']};
            --primary: {palette['primary']};
            --primary-hover: {palette['primary_hover']};
            --primary-shadow: {palette['primary_shadow']};
            --secondary-start: {palette['secondary_start']};
            --secondary-end: {palette['secondary_end']};
            --secondary-hover: {palette['secondary_hover']};
            --warning: {palette['warning']};
            --warning-emphasis: {palette['warning_emphasis']};
            --alert-icon-bg: {palette['alert_icon_bg']};
            --alert-icon-color: {palette['alert_icon_color']};
            --expander-header: {palette['expander_header']};
            --expander-background: {palette['expander_background']};
            --code-background: {palette['code_background']};
            --input-background: {palette['input_background']};
            --input-border: {palette['input_border']};
            --muted-border: {palette['muted_border']};
            --upload-background: {palette['upload_background']};
            --upload-border: {palette['upload_border']};
            --upload-text: {palette['upload_text']};
            --hover-glow: {palette['hover_glow']};
            --sidebar-badge-bg: {palette['sidebar_badge_background']};
            --accent: {palette['primary']};
            --accent-hover: {palette['primary_hover']};
        }}

        * {{
            transition: background-color 0.25s ease, color 0.25s ease, border-color 0.25s ease,
                box-shadow 0.25s ease, transform 0.25s ease;
        }}

        html, body, div[data-testid="stAppViewContainer"] {{
            background-color: var(--app-bg);
        }}

        body {{
            color: var(--text-primary);
            font-family: "Noto Sans TC", "Inter", "Segoe UI", system-ui, -apple-system,
                BlinkMacSystemFont, sans-serif;
        }}

        header, #MainMenu {{
            display: none;
        }}

        footer {{
            visibility: hidden;
        }}

        div[data-testid="stDecoration"] {{
            display: none !important;
        }}

        div[data-testid="stSidebar"] {{
            width: 296px;
            min-width: 296px;
            background: var(--sidebar-bg);
            border-right: 1px solid var(--app-surface-border);
            padding: 1.6rem 1.25rem 2.8rem;
        }}

        @media (max-width: 992px) {{
            div[data-testid="stSidebar"] {{
                width: 100%;
                min-width: 0;
            }}
        }}

        div[data-testid="stSidebar"] section[data-testid="stSidebarContent"] {{
            padding: 0;
        }}

        div[data-testid="stSidebar"] h1,
        div[data-testid="stSidebar"] h2,
        div[data-testid="stSidebar"] h3,
        div[data-testid="stSidebar"] h4,
        div[data-testid="stSidebar"] h5,
        div[data-testid="stSidebar"] h6,
        div[data-testid="stSidebar"] label,
        div[data-testid="stSidebar"] span,
        div[data-testid="stSidebar"] p {{
            color: var(--sidebar-text) !important;
        }}

        div[data-testid="stSidebar"] .sidebar-heading {{
            margin-bottom: 1.4rem;
        }}

        div[data-testid="stSidebar"] .sidebar-eyebrow {{
            display: inline-flex;
            align-items: center;
            font-size: 0.78rem;
            letter-spacing: 0.18em;
            text-transform: uppercase;
            color: var(--sidebar-muted);
            font-weight: 600;
        }}

        div[data-testid="stSidebar"] .sidebar-title {{
            font-size: 1.45rem;
            font-weight: 700;
            margin: 0.3rem 0 0.4rem;
            color: var(--sidebar-text);
        }}

        div[data-testid="stSidebar"] .sidebar-tagline {{
            font-size: 0.9rem;
            line-height: 1.5;
            color: var(--sidebar-muted);
            margin: 0;
        }}

        div[data-testid="stSidebar"] .sidebar-note {{
            margin: 1.25rem 0 0;
            font-size: 0.82rem;
            color: var(--sidebar-muted);
        }}

        div[data-testid="stSidebar"] div[data-testid="stToggle"] {{
            border: 1px solid var(--muted-border);
            border-radius: 14px;
            padding: 0.75rem 0.85rem;
            background: var(--app-surface);
            box-shadow: 0 24px 38px -32px var(--primary-shadow);
            margin: 1.1rem 0 1.6rem;
        }}

        div[data-testid="stSidebar"] div[data-testid="stToggle"] label {{
            color: var(--sidebar-text);
            font-weight: 600;
            width: 100%;
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 0.75rem;
        }}

        div[data-testid="stSidebar"] div[data-testid="stToggle"] [role="switch"] {{
            background: var(--sidebar-button-hover);
            border-radius: 999px;
        }}

        div[data-testid="stSidebar"] .stSelectbox > label {{
            font-size: 0.9rem;
            font-weight: 600;
            color: var(--sidebar-muted) !important;
            margin-bottom: 0.45rem;
        }}

        div[data-testid="stSidebar"] .stSelectbox div[data-baseweb="select"] > div {{
            background: transparent;
            border: 1px solid var(--muted-border);
            border-radius: 12px;
            color: var(--sidebar-text);
            padding: 0.25rem 0.5rem;
        }}

        div[data-testid="stSidebar"] .stSelectbox div[data-baseweb="select"] > div:hover {{
            border-color: var(--primary);
            box-shadow: var(--hover-glow);
        }}

        div[data-testid="stSidebar"] .stSelectbox div[data-baseweb="select"] span {{
            color: var(--sidebar-text);
        }}

        div[data-testid="stSidebar"] .sidebar-nav {{
            margin-top: 1.35rem;
            display: flex;
            flex-direction: column;
            gap: 0.35rem;
        }}

        div[data-testid="stSidebar"] .sidebar-nav .nav-link {{
            color: var(--sidebar-text) !important;
            border-radius: 12px !important;
            padding: 0.65rem 0.85rem !important;
            font-weight: 600;
            font-size: 0.98rem;
            background: transparent !important;
            border: 1px solid transparent !important;
            display: flex !important;
            align-items: center;
            gap: 0.65rem;
        }}

        div[data-testid="stSidebar"] .sidebar-nav .nav-link:hover {{
            background: var(--sidebar-button-hover) !important;
            color: var(--sidebar-text) !important;
            transform: translateX(4px);
            box-shadow: var(--hover-glow);
        }}

        div[data-testid="stSidebar"] .sidebar-nav .nav-link i {{
            color: var(--sidebar-icon) !important;
            font-size: 1rem !important;
            transition: color 0.2s ease;
        }}

        div[data-testid="stSidebar"] .sidebar-nav .nav-link:hover i {{
            color: var(--sidebar-icon-hover) !important;
        }}

        div[data-testid="stSidebar"] .sidebar-nav .nav-link-selected {{
            background: linear-gradient(135deg, var(--primary), var(--primary-hover)) !important;
            color: #ffffff !important;
            box-shadow: var(--hover-glow);
            transform: translateX(4px);
        }}

        div[data-testid="stSidebar"] .sidebar-nav .nav-link-selected i {{
            color: #ffffff !important;
        }}

        div[data-testid="stSidebar"] .sidebar-menu-description {{
            color: var(--sidebar-muted) !important;
            font-size: 0.85rem;
            margin: 0.4rem 0 1.25rem;
            line-height: 1.45;
        }}

        div[data-testid="stSidebar"] hr {{
            border-color: var(--muted-border);
            margin: 1.6rem 0 1.2rem;
        }}

        div[data-testid="stSidebar"] .sidebar-badge {{
            display: inline-flex;
            align-items: center;
            gap: 0.45rem;
            padding: 0.45rem 0.75rem;
            border-radius: 999px;
            background: var(--sidebar-badge-bg);
            color: var(--sidebar-text);
            font-weight: 600;
            font-size: 0.82rem;
        }}

        .stButton > button,
        .stDownloadButton > button,
        .stFormSubmitButton > button {{
            background: linear-gradient(135deg, var(--primary), var(--primary-hover));
            color: #ffffff;
            border: none;
            border-radius: 14px;
            padding: 0.75rem 1.45rem;
            font-weight: 600;
            font-size: 0.98rem;
            box-shadow: var(--hover-glow);
        }}

        .stButton > button:hover,
        .stDownloadButton > button:hover,
        .stFormSubmitButton > button:hover {{
            transform: translateY(-1px) scale(1.02);
            box-shadow: 0 26px 48px -24px var(--primary-shadow);
        }}

        .stButton > button:focus-visible,
        .stDownloadButton > button:focus-visible,
        .stFormSubmitButton > button:focus-visible {{
            outline: 2px solid rgba(255, 255, 255, 0.35);
            outline-offset: 3px;
        }}

        div[data-testid="stFileUploader"] {{
            margin-bottom: 1.5rem;
        }}

        div[data-testid="stFileUploader"] > label {{
            font-weight: 600;
            font-size: 0.95rem;
            color: var(--text-secondary);
            margin-bottom: 0.6rem;
        }}

        div[data-testid="stFileUploader"] section[data-testid="stFileUploaderDropzone"] {{
            border: 1px dashed var(--upload-border);
            background: var(--upload-background);
            color: var(--upload-text);
            border-radius: 18px;
            padding: 1.1rem;
        }}

        div[data-testid="stFileUploader"] section[data-testid="stFileUploaderDropzone"]:hover {{
            border-color: var(--primary);
            transform: translateY(-2px) scale(1.01);
            box-shadow: var(--hover-glow);
        }}

        div[data-testid="stFileUploader"] section[data-testid="stFileUploaderDropzone"] span {{
            color: var(--upload-text);
        }}

        div[data-testid="stFileUploader"] button {{
            background: linear-gradient(135deg, var(--secondary-start), var(--secondary-end));
            color: #ffffff;
            border: none;
            border-radius: 12px;
            padding: 0.5rem 1.1rem;
            font-weight: 600;
            box-shadow: var(--hover-glow);
        }}

        div[data-testid="stFileUploader"] button:hover {{
            transform: translateY(-1px);
            box-shadow: 0 24px 44px -26px rgba(27, 172, 156, 0.5);
        }}

        div[data-testid="stAppViewContainer"] .main {{
            padding: 0;
        }}

        div[data-testid="stAppViewContainer"] .main .block-container {{
            background: var(--app-surface);
            border-radius: 28px;
            border: 1px solid var(--app-surface-border);
            box-shadow: var(--app-surface-shadow);
            padding: 2.6rem 3rem 3rem;
            display: flex;
            flex-direction: column;
            gap: 1.8rem;
        }}

        @media (max-width: 992px) {{
            div[data-testid="stAppViewContainer"] .main .block-container {{
                padding: 2rem 1.6rem 2.4rem;
                border-radius: 22px;
            }}
        }}

        div[data-testid="stAppViewContainer"] .main .block-container h1 {{
            font-size: 2.35rem;
            font-weight: 700;
            margin: 0;
            color: var(--text-primary);
        }}

        div[data-testid="stAppViewContainer"] .main .block-container h2 {{
            font-size: 1.6rem;
            font-weight: 700;
            margin-bottom: 0.4rem;
            color: var(--text-primary);
        }}

        div[data-testid="stAppViewContainer"] .main .block-container h3 {{
            font-size: 1.35rem;
            font-weight: 600;
            margin-bottom: 0.35rem;
            color: var(--text-primary);
        }}

        div[data-testid="stAppViewContainer"] .main .block-container p,
        div[data-testid="stAppViewContainer"] .main .block-container span,
        div[data-testid="stAppViewContainer"] .main .block-container label,
        div[data-testid="stAppViewContainer"] .main .block-container li {{
            color: var(--text-primary);
        }}

        div[data-testid="stAppViewContainer"] .main .block-container small,
        div[data-testid="stAppViewContainer"] .main .block-container .stCaption,
        div[data-testid="stAppViewContainer"] .main .block-container .stMarkdown small {{
            color: var(--text-secondary) !important;
        }}

        .stTabs [role="tablist"] {{
            gap: 0.75rem;
            border-bottom: none;
            padding-bottom: 0.25rem;
        }}

        .stTabs [role="tab"] {{
            border-radius: 999px;
            padding: 0.45rem 1.1rem;
            font-weight: 600;
            color: var(--text-secondary);
            background: var(--app-surface-muted);
            border: 1px solid var(--muted-border);
        }}

        .stTabs [role="tab"]:hover {{
            color: var(--text-primary);
            transform: translateY(-1px);
            box-shadow: var(--hover-glow);
        }}

        .stTabs [role="tab"][aria-selected="true"] {{
            background: linear-gradient(135deg, var(--primary), var(--primary-hover));
            color: #ffffff;
            box-shadow: var(--hover-glow);
            border-color: transparent;
        }}

        div[data-testid="stExpander"] > details {{
            background: var(--expander-background);
            border-radius: 18px;
            border: 1px solid var(--muted-border);
            overflow: hidden;
        }}

        div[data-testid="stExpander"] > details > summary {{
            background: var(--expander-header);
            color: var(--text-primary);
            padding: 0.95rem 1.1rem;
            font-weight: 600;
        }}

        div[data-testid="stExpander"] > details > summary:hover {{
            filter: brightness(1.05);
        }}

        div[data-testid="stExpander"] > details div[data-testid="stExpanderContent"] {{
            padding: 0.95rem 1.1rem 1.1rem;
            color: var(--text-primary);
        }}

        .brand-hero {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 1.8rem;
            padding: 1.9rem 2.2rem;
            border-radius: 24px;
            position: relative;
            overflow: hidden;
            background: linear-gradient(135deg, var(--accent-start), var(--accent-end));
            box-shadow: 0 32px 58px -32px var(--accent-shadow);
            color: #f8fafc;
        }}

        .brand-hero::after {{
            content: "";
            position: absolute;
            inset: 0;
            background: radial-gradient(circle at top right, rgba(255, 255, 255, 0.28), transparent 60%);
            opacity: 0.75;
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
            margin: 0.45rem 0 0.85rem;
            font-size: 2.4rem;
            font-weight: 700;
            letter-spacing: 0.01em;
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
            padding: 0.6rem 1.5rem;
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
            padding: 1.4rem 1.5rem;
            border-radius: 22px;
            border: 1px solid var(--card-border);
            background: var(--card-background);
            box-shadow: var(--card-shadow);
            transition: transform 0.25s ease, box-shadow 0.25s ease;
        }}

        .feature-card:hover {{
            transform: translateY(-4px) scale(1.02);
            box-shadow: var(--hover-glow);
        }}

        .feature-card__icon {{
            width: 52px;
            height: 52px;
            border-radius: 50%;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            font-size: 1.6rem;
            margin-bottom: 1rem;
            background: linear-gradient(135deg, var(--secondary-start), var(--secondary-end));
            color: #ffffff;
            box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.25);
        }}

        .feature-card[data-variant="primary"] .feature-card__icon {{
            background: linear-gradient(135deg, var(--primary), var(--primary-hover));
        }}

        .feature-card[data-variant="secondary"] .feature-card__icon {{
            background: linear-gradient(135deg, var(--secondary-start), var(--secondary-end));
        }}

        .feature-card[data-variant="alert"] .feature-card__icon {{
            background: var(--alert-icon-bg);
            color: var(--alert-icon-color);
            box-shadow: inset 0 0 0 1px rgba(255, 193, 7, 0.32);
        }}

        .feature-card__title {{
            font-size: 1.12rem;
            font-weight: 700;
            color: var(--text-primary);
            margin-bottom: 0.5rem;
        }}

        .feature-card__desc {{
            color: var(--text-secondary);
            margin: 0;
            font-size: 0.95rem;
            line-height: 1.6;
        }}

        hr {{
            border-color: var(--muted-border);
        }}

        .stAlert {{
            border-radius: 16px;
            border: 1px solid var(--muted-border);
            background: var(--app-surface-muted);
            box-shadow: var(--hover-glow);
        }}

        .stAlert div[role="alert"] p {{
            color: var(--text-primary);
        }}

        .stAlert[data-baseweb="alert"][kind="warning"] {{
            border-left: 4px solid var(--warning);
        }}

        .stAlert[data-baseweb="alert"][kind="error"] {{
            border-left: 4px solid var(--warning-emphasis);
        }}

        code, pre {{
            background: var(--code-background);
            color: var(--text-primary);
            border-radius: 10px;
            padding: 0.2rem 0.45rem;
        }}

        div[data-baseweb="input"] input,
        div[data-baseweb="input"] textarea,
        div[data-baseweb="select"] > div {{
            background: var(--input-background) !important;
            color: var(--text-primary) !important;
            border-radius: 12px;
        }}

        div[data-baseweb="input"] input,
        div[data-baseweb="input"] textarea {{
            border: 1px solid var(--input-border) !important;
        }}

        div[data-baseweb="input"] input:hover,
        div[data-baseweb="input"] textarea:hover,
        div[data-baseweb="select"] > div:hover {{
            border-color: var(--primary) !important;
            box-shadow: var(--hover-glow);
        }}

        div[data-testid="stMetricValue"] {{
            color: var(--primary);
            font-weight: 700;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def _render_sidebar(current_theme: str) -> str:
    options = list(BRAND_RENDERERS.keys())
    with st.sidebar:
        st.markdown(
            f"""
            <div class="sidebar-heading">
                <span class="sidebar-eyebrow">Unified Console</span>
                <div class="sidebar-title">{html.escape(SIDEBAR_TITLE)}</div>
                <p class="sidebar-tagline">跨品牌威脅分析流程，以一致的體驗呈現。</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        is_dark = st.toggle("深色介面", value=current_theme == "dark", key="unified_theme_toggle")
        st.session_state["unified_theme"] = "dark" if is_dark else "light"

        brand = st.selectbox("選擇品牌", options, key="unified_brand")

        st.markdown(
            f"<span class='sidebar-badge'>現在瀏覽：{html.escape(brand)}</span>",
            unsafe_allow_html=True,
        )

        st.markdown(
            "<p class='sidebar-note'>所有模組共用相同的視覺語言與互動效果，確保跨品牌的一致體驗。</p>",
            unsafe_allow_html=True,
        )

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
            variant = FEATURE_VARIANTS.get(title, "secondary")
            column.markdown(
                f"""
                <div class="feature-card" data-variant="{html.escape(variant)}">
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
    initial_theme = st.session_state.get("unified_theme", "dark")
    palette = THEME_PRESETS.get(initial_theme, THEME_PRESETS["dark"])
    _apply_theme_styles(palette)

    brand = _render_sidebar(initial_theme)

    updated_theme = st.session_state.get("unified_theme", initial_theme)
    if updated_theme != initial_theme:
        palette = THEME_PRESETS.get(updated_theme, THEME_PRESETS["dark"])
        _apply_theme_styles(palette)

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
