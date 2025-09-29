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
        ("🧭", "模型推論指引", "依步驟完成資料上傳、模型載入與結果檢視，降低操作門檻。"),
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
    st.session_state.setdefault("fortinet_menu_collapse", False)
    st.session_state.setdefault("cisco_menu_collapse", False)


    # 全域樣式
    st.markdown("""
        <style>
        /* Card Styles */
        .feature-card {
            padding: 2.35rem 2.05rem 1.85rem;
            border-radius: 22px;
            border: 1px solid var(--card-border);
            background: var(--card-background);
            box-shadow: var(--card-shadow);
            transition: transform 0.25s ease, box-shadow 0.25s ease;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            text-align: center;
            gap: 1rem;
            margin-top: 1.5rem;
            margin-inline: auto;
            position: relative;
            overflow: hidden;
        }

        .feature-card:hover {
            transform: translateY(-4px) scale(1.02);
            box-shadow: var(--hover-glow);
        }

        .feature-card__icon {
            width: 52px;
            height: 52px;
            border-radius: 50%;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            font-size: 1.6rem;
            margin: 0 auto 1.15rem;
            background: linear-gradient(
                135deg,
                var(--feature-accent-start, var(--primary)),
                var(--feature-accent-end, var(--primary-hover))
            );
            color: #ffffff;
            box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.25),
                0 12px 28px -14px var(--feature-accent-shadow, rgba(15, 23, 42, 0.28));
        }

        .feature-card__title {
            font-size: var(--font-h3);
            font-weight: 700;
            color: var(--text-h3) !important;
            margin-bottom: 0.25rem;
            text-align: center;
        }

        .feature-card__desc {
            color: var(--text-body) !important;
            margin: 0;
            font-size: calc(var(--font-body) - 0.3px);
            line-height: 1.65;
            text-align: center;
        }

        /* Button Styles */
        .stButton button {
            background: linear-gradient(135deg, var(--primary-color), var(--secondary-color)) !important;
            border: none !important;
            border-radius: 0.5rem !important;
            color: #fff !important;
            font-weight: 600 !important;
            padding: 0.4rem 1rem !important;
            transition: all 0.3s ease-in-out !important;
            box-shadow: 0 16px 32px -20px color-mix(in srgb, var(--primary-color) 55%, transparent);
        }

        .stButton button:hover {
            box-shadow: 0 0 10px color-mix(in srgb, var(--primary-color) 60%, transparent);
            transform: translateY(-1px);
        }
        
        /* Hero Card Alignment */
        .brand-hero {
            margin: 2rem auto;
            max-width: 1200px;
            text-align: center;
        }
        
        </style>
    """, unsafe_allow_html=True)

    _inject_theme_styles()


def _inject_theme_styles() -> None:
    if not st.session_state.get("_unified_icons_loaded"):
        st.markdown(
            "<link rel=\"stylesheet\" href=\"https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.min.css\">",
            unsafe_allow_html=True,
        )
        st.session_state["_unified_icons_loaded"] = True

    if st.session_state.get("_unified_theme_css_applied"):
        return

    st.session_state["_unified_theme_css_applied"] = True
    st.markdown(
        """
        <style>
        :root {
            --app-bg: var(--backgroundColor);
            --app-surface: var(--secondaryBackgroundColor);
            --app-surface-muted: color-mix(in srgb, var(--secondaryBackgroundColor) 85%, var(--backgroundColor) 15%);
            --app-surface-border: color-mix(in srgb, var(--textColor) 12%, var(--backgroundColor) 88%);
            --app-surface-shadow: 0 36px 72px -42px color-mix(in srgb, var(--backgroundColor) 80%, transparent);
            --text-primary: var(--textColor);
            --text-secondary: color-mix(in srgb, var(--textColor) 70%, var(--backgroundColor) 30%);
            --text-body: color-mix(in srgb, var(--textColor) 88%, var(--backgroundColor) 12%);
            --text-caption: color-mix(in srgb, var(--textColor) 58%, var(--backgroundColor) 42%);
            --text-label: color-mix(in srgb, var(--textColor) 78%, var(--backgroundColor) 22%);
            --text-h1: color-mix(in srgb, var(--textColor) 96%, var(--backgroundColor) 4%);
            --text-h2: color-mix(in srgb, var(--textColor) 92%, var(--backgroundColor) 8%);
            --text-h3: color-mix(in srgb, var(--textColor) 88%, var(--backgroundColor) 12%);
            --font-h1: 20.8px;
            --font-h2: 17.6px;
            --font-h3: 14.4px;
            --font-label: 12.8px;
            --font-body: 12.4px;
            --font-caption: 10.8px;
            --sidebar-bg: color-mix(in srgb, var(--backgroundColor) 90%, var(--secondaryBackgroundColor) 10%);
            --sidebar-text: var(--textColor);
            --sidebar-muted: color-mix(in srgb, var(--textColor) 52%, var(--backgroundColor) 48%);
            --sidebar-button-hover: color-mix(in srgb, var(--primaryColor) 18%, transparent);
            --sidebar-icon: var(--textColor);
            --sidebar-icon-hover: color-mix(in srgb, var(--textColor) 86%, var(--backgroundColor) 14%);
            --card-background: color-mix(in srgb, var(--secondaryBackgroundColor) 92%, var(--backgroundColor) 8%);
            --card-border: color-mix(in srgb, var(--textColor) 12%, var(--backgroundColor) 88%);
            --card-shadow: 0 28px 56px -32px color-mix(in srgb, var(--backgroundColor) 84%, transparent);
            --primary: var(--primaryColor);
            --primary-hover: color-mix(in srgb, var(--primaryColor) 76%, var(--textColor) 24%);
            --primary-shadow: color-mix(in srgb, var(--primaryColor) 44%, transparent);
            --secondary-start: color-mix(in srgb, var(--primaryColor) 68%, var(--textColor) 32%);
            --secondary-end: color-mix(in srgb, var(--primaryColor) 48%, var(--backgroundColor) 52%);
            --secondary-hover: color-mix(in srgb, var(--primaryColor) 62%, var(--textColor) 38%);
            /*
             * Color variable mapping standardization:
             * --primary-color is a semantic alias for the active brand hue (--primary).
             * --secondary-color mirrors --secondary-start to anchor gradient blends.
             * Centralizing these aliases keeps the gradient button styles consistent
             * across brand themes and matches the names used in theme_controller.py.
             */
            --primary-color: var(--primary);
            --secondary-color: var(--secondary-start);
            --warning: color-mix(in srgb, var(--primaryColor) 40%, var(--textColor) 60%);
            --warning-emphasis: color-mix(in srgb, var(--primaryColor) 55%, var(--textColor) 45%);
            --alert-icon-bg: color-mix(in srgb, var(--primaryColor) 20%, transparent);
            --alert-icon-color: color-mix(in srgb, var(--textColor) 85%, var(--backgroundColor) 15%);
            --expander-header: color-mix(in srgb, var(--secondaryBackgroundColor) 72%, var(--backgroundColor) 28%);
            --expander-background: color-mix(in srgb, var(--secondaryBackgroundColor) 86%, var(--backgroundColor) 14%);
            --code-background: color-mix(in srgb, var(--secondaryBackgroundColor) 78%, var(--backgroundColor) 22%);
            --input-background: color-mix(in srgb, var(--secondaryBackgroundColor) 82%, var(--backgroundColor) 18%);
            --input-border: color-mix(in srgb, var(--textColor) 16%, var(--backgroundColor) 84%);
            --muted-border: color-mix(in srgb, var(--textColor) 10%, var(--backgroundColor) 90%);
            --upload-background: color-mix(in srgb, var(--secondaryBackgroundColor) 84%, var(--backgroundColor) 16%);
            --upload-border: color-mix(in srgb, var(--primaryColor) 32%, transparent);
            --upload-text: color-mix(in srgb, var(--textColor) 86%, var(--backgroundColor) 14%);
            --hover-glow: 0 32px 64px -34px color-mix(in srgb, var(--primaryColor) 52%, transparent);
            --sidebar-badge-bg: color-mix(in srgb, var(--primaryColor) 24%, transparent);
            --accent: var(--primaryColor);
            --accent-hover: color-mix(in srgb, var(--primaryColor) 74%, var(--textColor) 26%);
            --text-on-primary: color-mix(in srgb, var(--textColor) 95%, var(--backgroundColor) 5%);
        }

        * {
            transition: background-color 0.25s ease, color 0.25s ease, border-color 0.25s ease,
                box-shadow 0.25s ease, transform 0.25s ease;
        }

        html, body, div[data-testid="stAppViewContainer"] {
            background-color: var(--app-bg);
        }

        body {
            color: var(--text-body) !important;
            font-family: "Noto Sans TC", "Inter", "Segoe UI", system-ui, -apple-system,
                BlinkMacSystemFont, sans-serif;
            font-size: var(--font-body);
            line-height: 1.65;
        }

        div[data-testid="stAppViewContainer"] .main .block-container {
            color: var(--text-body) !important;
            font-size: var(--font-body);
            line-height: 1.65;
        }

        div[data-testid="stAppViewContainer"] .main .block-container p,
        div[data-testid="stAppViewContainer"] .main .block-container span,
        div[data-testid="stAppViewContainer"] .main .block-container li,
        div[data-testid="stAppViewContainer"] .main .block-container label,
        div[data-testid="stAppViewContainer"] .main .block-container .stMarkdown p,
        div[data-testid="stAppViewContainer"] .main .block-container .stMarkdown li {
            color: var(--text-body) !important;
            font-size: var(--font-body);
        }

        div[data-testid="stAppViewContainer"] ::placeholder {
            color: var(--text-caption) !important;
            opacity: 0.85;
        }

        div[data-testid="stAppViewContainer"] .main .block-container h1,
        div[data-testid="stAppViewContainer"] .main .block-container .stMarkdown h1 {
            color: var(--text-h1) !important;
            font-size: var(--font-h1);
            font-weight: 700;
            letter-spacing: 0.01em;
            margin-top: 0;
            margin-bottom: 0.75rem;
        }

        div[data-testid="stAppViewContainer"] .main .block-container h2,
        div[data-testid="stAppViewContainer"] .main .block-container .stMarkdown h2 {
            color: var(--text-h2) !important;
            font-size: var(--font-h2);
            font-weight: 600;
            margin-top: 2.2rem;
            margin-bottom: 0.75rem;
        }

        div[data-testid="stAppViewContainer"] .main .block-container h3,
        div[data-testid="stAppViewContainer"] .main .block-container h4,
        div[data-testid="stAppViewContainer"] .main .block-container .stMarkdown h3,
        div[data-testid="stAppViewContainer"] .main .block-container .stMarkdown h4 {
            color: var(--text-h3) !important;
            font-size: var(--font-h3);
            font-weight: 600;
            margin-top: 1.8rem;
            margin-bottom: 0.6rem;
        }

        div[data-testid="stAppViewContainer"] .main .block-container h5,
        div[data-testid="stAppViewContainer"] .main .block-container h6,
        div[data-testid="stAppViewContainer"] .main .block-container .stMarkdown h5,
        div[data-testid="stAppViewContainer"] .main .block-container .stMarkdown h6 {
            color: var(--text-label) !important;
            font-size: calc(var(--font-label) - 1px);
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            margin-top: 1.6rem;
            margin-bottom: 0.5rem;
        }

        div[data-testid="stAppViewContainer"] .main .block-container label,
        div[data-testid="stAppViewContainer"] .main .block-container .stMarkdown label,
        div[data-testid="stAppViewContainer"] .main .block-container [data-testid="stForm"] label,
        div[data-testid="stAppViewContainer"] .main .block-container [data-testid="stExpander"] label {
            color: var(--text-label) !important;
            font-size: var(--font-label);
            font-weight: 500;
        }

        body small,
        body .stCaption,
        body .caption,
        div[data-testid="stAppViewContainer"] .main .block-container small,
        div[data-testid="stAppViewContainer"] .main .block-container .stCaption,
        div[data-testid="stAppViewContainer"] .main .block-container .caption {
            color: var(--text-caption) !important;
            font-size: var(--font-caption);
            line-height: 1.55;
        }

        header, #MainMenu {
            display: none;
        }

        footer {
            visibility: hidden;
        }

        div[data-testid="stDecoration"] {
            display: none !important;
        }

        div[data-testid="stSidebar"] {
            width: 296px;
            min-width: 296px;
            background: var(--sidebar-bg);
            border-right: 1px solid var(--app-surface-border);
            padding: 1.6rem 1.25rem 2.8rem;
        }

        @media (max-width: 992px) {
            div[data-testid="stSidebar"] {
                width: 100%;
                min-width: 0;
            }
        }

        div[data-testid="stSidebar"] section[data-testid="stSidebarContent"] {
            padding: 0;
        }

        div[data-testid="stSidebar"] h1,
        div[data-testid="stSidebar"] h2,
        div[data-testid="stSidebar"] h3,
        div[data-testid="stSidebar"] h4,
        div[data-testid="stSidebar"] h5,
        div[data-testid="stSidebar"] h6,
        div[data-testid="stSidebar"] label,
        div[data-testid="stSidebar"] span,
        div[data-testid="stSidebar"] p {
            color: var(--sidebar-text) !important;
        }

        div[data-testid="stSidebar"] .sidebar-heading {
            margin-bottom: 1.4rem;
        }

        div[data-testid="stSidebar"] .sidebar-eyebrow {
            display: inline-flex;
            align-items: center;
            font-size: 0.85rem;
            letter-spacing: 0.18em;
            text-transform: uppercase;
            color: var(--sidebar-muted);
            font-weight: 700;
        }

        div[data-testid="stSidebar"] .sidebar-title {
            font-size: 1.45rem;
            font-weight: 700;
            margin: 0.3rem 0 0.4rem;
            color: var(--sidebar-text);
        }

        div[data-testid="stSidebar"] .sidebar-tagline {
            font-size: 0.95rem;
            line-height: 1.65;
            color: var(--sidebar-muted);
            margin: 0;
        }

        div[data-testid="stSidebar"] .sidebar-note {
            margin: 1.25rem 0 0;
            font-size: calc(var(--font-body) - 1px);
            line-height: 1.6;
            color: var(--sidebar-muted);
        }

        div[data-testid="stSidebar"] .stSelectbox > label {
            font-size: 0.9rem;
            font-weight: 600;
            color: var(--sidebar-text) !important;
            margin-bottom: 0.45rem;
        }

        div[data-testid="stSidebar"] .stSelectbox div[data-baseweb="select"] > div {
            background: transparent;
            border: 1px solid var(--muted-border);
            border-radius: 12px;
            color: var(--sidebar-text);
            padding: 0.25rem 0.5rem;
        }

        div[data-testid="stSidebar"] .stSelectbox div[data-baseweb="select"] > div:hover {
            border-color: var(--primary);
            box-shadow: var(--hover-glow);
        }

        div[data-testid="stSidebar"] .stSelectbox div[data-baseweb="select"] span {
            color: var(--sidebar-text);
        }

        div[data-testid="stSidebar"] .sidebar-nav {
            margin-top: 1.5rem;
            display: flex;
            flex-direction: column;
            gap: 0.5rem;
        }

        div[data-testid="stSidebar"] .sidebar-nav .nav-link {
            color: var(--sidebar-text) !important;
            border-radius: 12px !important;
            padding: 0.7rem 0.95rem !important;
            font-weight: 600;
            font-size: var(--font-label);
            background: transparent !important;
            border: 1px solid transparent !important;
            display: flex !important;
            align-items: center;
            gap: 0.65rem;
        }

        div[data-testid="stSidebar"] .sidebar-nav .nav-link svg {
            color: var(--sidebar-icon);
            width: 1.1rem;
            height: 1.1rem;
        }

        div[data-testid="stSidebar"] .sidebar-nav .nav-link:hover {
            background: var(--sidebar-button-hover) !important;
            border-color: var(--sidebar-button-hover) !important;
            transform: translateX(2px);
            box-shadow: var(--hover-glow);
        }

        div[data-testid="stSidebar"] .sidebar-nav .nav-link:hover svg {
            color: var(--sidebar-icon-hover);
        }

        div[data-testid="stSidebar"] .sidebar-nav .nav-link.active {
            background: linear-gradient(135deg, var(--primary), var(--primary-hover)) !important;
            color: var(--text-on-primary) !important;
            box-shadow: var(--hover-glow);
        }

        div[data-testid="stSidebar"] .sidebar-nav .nav-link.active svg {
            color: var(--text-on-primary);
        }

        .sidebar-badge {
            display: inline-flex;
            align-items: center;
            gap: 0.45rem;
            background: var(--sidebar-badge-bg);
            border-radius: 999px;
            padding: 0.45rem 0.9rem;
            margin-top: 0.85rem;
            color: var(--sidebar-text);
            font-weight: 600;
            font-size: calc(var(--font-label) - 1px);
            letter-spacing: 0.04em;
        }

        .sidebar-badge::before {
            content: "";
            width: 6px;
            height: 6px;
            border-radius: 50%;
            background: var(--primary);
            box-shadow: 0 0 0 4px color-mix(in srgb, var(--primary) 12%, transparent);
        }

        .sidebar-menu-description {
            color: var(--sidebar-muted);
            font-size: calc(var(--font-body) - 1px);
            margin: 0.35rem 0 0;
            line-height: 1.55;
        }

        div[data-testid="stSidebar"] hr {
            border-color: var(--app-surface-border);
            margin: 1.8rem 0 1.4rem;
        }

        .stButton > button,
        .stDownloadButton > button,
        .stFormSubmitButton > button {
            background: linear-gradient(135deg, var(--primary-color), var(--secondary-color));
            color: #fff;
            border: none;
            border-radius: 0.5rem;
            padding: 0.4rem 1rem;
            font-weight: 600;
            font-size: var(--font-label);
            display: inline-flex;
            align-items: center;
            justify-content: center;
            gap: 0.45rem;
            letter-spacing: 0.01em;
            box-shadow: 0 18px 36px -22px color-mix(in srgb, var(--primary-color) 55%, transparent);
            margin: 0.2rem 0.35rem 0.2rem 0;
        }

        .stButton > button:hover,
        .stDownloadButton > button:hover,
        .stFormSubmitButton > button:hover {
            transform: translateY(-1px);
            box-shadow: 0 0 10px color-mix(in srgb, var(--primary-color) 60%, transparent);
        }

        .stButton > button:focus-visible,
        .stDownloadButton > button:focus-visible,
        .stFormSubmitButton > button:focus-visible {
            outline: 2px solid color-mix(in srgb, var(--primaryColor) 45%, transparent);
            outline-offset: 3px;
        }

        .stButton > button:disabled,
        .stDownloadButton > button:disabled,
        .stFormSubmitButton > button:disabled {
            box-shadow: none;
            opacity: 0.65;
        }

        div[data-testid="stFileUploader"] {
            margin-bottom: 1.75rem;
        }

        div[data-testid="stFileUploader"] > label {
            font-weight: 600;
            font-size: var(--font-label);
            color: var(--text-label);
            margin-bottom: 0.65rem;
        }

        div[data-testid="stFileUploader"] section[data-testid="stFileUploaderDropzone"] {
            border: 1px dashed var(--upload-border);
            background: var(--upload-background);
            color: var(--upload-text) !important;
            border-radius: 18px;
            padding: 1.25rem 1.35rem;
            box-shadow: inset 0 1px 0 color-mix(in srgb, var(--textColor) 5%, transparent);
        }

        div[data-testid="stFileUploader"] section[data-testid="stFileUploaderDropzone"]:hover {
            border-color: var(--primary);
            transform: translateY(-2px) scale(1.01);
            box-shadow: var(--hover-glow);
        }

        div[data-testid="stFileUploader"] section[data-testid="stFileUploaderDropzone"] span,
        div[data-testid="stFileUploader"] section[data-testid="stFileUploaderDropzone"] p,
        div[data-testid="stFileUploader"] section[data-testid="stFileUploaderDropzone"] small {
            color: var(--upload-text) !important;
        }

        div[data-testid="stFileUploader"] button {
            background: linear-gradient(135deg, var(--primary), var(--primary-hover));
            color: var(--text-on-primary);
            border: none;
            border-radius: 12px;
            padding: 0.55rem 1.25rem;
            font-weight: 600;
            font-size: var(--font-label);
            box-shadow: var(--hover-glow);
        }

        div[data-testid="stFileUploader"] button:hover {
            transform: translateY(-1px) scale(1.01);
            box-shadow: 0 24px 44px -26px var(--primary-shadow);
        }

        div[data-testid="stToggle"] {
            margin-bottom: 1.1rem;
        }

        div[data-testid="stToggle"] label {
            color: var(--text-label);
            font-weight: 600;
            font-size: var(--font-label);
        }

        div[data-testid="stToggle"] [role="switch"] {
            border-radius: 999px;
            background: var(--muted-border);
            padding: 2px;
            border: 1px solid transparent;
            transition: background 0.3s ease, box-shadow 0.3s ease, transform 0.3s ease;
        }

        div[data-testid="stToggle"] [role="switch"][aria-checked="true"] {
            background: linear-gradient(135deg, var(--primary), var(--primary-hover));
            box-shadow: var(--hover-glow);
        }

        div[data-testid="stToggle"] [role="switch"] > div {
            background: var(--app-surface);
            border-radius: 50%;
            box-shadow: 0 6px 14px color-mix(in srgb, var(--backgroundColor) 55%, transparent);
        }

        div[data-testid="stAppViewContainer"] .main {
            padding: 0;
        }

        div[data-testid="stAppViewContainer"] .main .block-container {
            background: var(--app-surface);
            border-radius: 28px;
            border: 1px solid var(--app-surface-border);
            box-shadow: var(--app-surface-shadow);
            padding: 2.6rem 3rem 3rem;
            display: flex;
            flex-direction: column;
            gap: 1.8rem;
        }

        @media (max-width: 992px) {
            div[data-testid="stAppViewContainer"] .main .block-container {
                padding: 2rem 1.6rem 2.4rem;
                border-radius: 22px;
            }
        }

        .stTabs [role="tablist"] {
            gap: 0.6rem;
            border-bottom: none;
            padding-bottom: 0.35rem;
        }

        .stTabs [role="tab"] {
            border-radius: 14px;
            padding: 0.6rem 1.35rem;
            font-weight: 600;
            font-size: var(--font-label);
            color: var(--text-label);
            background: var(--app-surface-muted);
            border: 1px solid var(--muted-border);
            transition: transform 0.25s ease, box-shadow 0.25s ease, color 0.25s ease;
        }

        .stTabs [role="tab"]:hover {
            color: var(--text-h2);
            transform: translateY(-1px);
            box-shadow: var(--hover-glow);
        }

        .stTabs [role="tab"][aria-selected="true"] {
            background: linear-gradient(135deg, var(--primary), var(--primary-hover));
            color: var(--text-on-primary);
            box-shadow: var(--hover-glow);
            border-color: transparent;
        }

        .stTabs [role="tabpanel"] {
            background: var(--card-background);
            border: 1px solid var(--muted-border);
            border-radius: 20px;
            padding: 1.4rem 1.5rem 1.6rem;
            box-shadow: var(--card-shadow);
            margin-top: 0.85rem;
        }

        div[data-testid="stExpander"] > details {
            background: var(--expander-background);
            border-radius: 18px;
            border: 1px solid var(--muted-border);
            overflow: hidden;
            box-shadow: var(--card-shadow);
        }

        div[data-testid="stExpander"] > details > summary {
            background: var(--expander-header);
            color: var(--text-label);
            padding: 1rem 1.25rem;
            font-weight: 600;
            font-size: var(--font-label);
        }

        div[data-testid="stExpander"] > details > summary:hover {
            filter: brightness(1.05);
            box-shadow: var(--hover-glow);
        }

        div[data-testid="stExpander"] > details div[data-testid="stExpanderContent"] {
            padding: 1.15rem 1.25rem 1.35rem;
            color: var(--text-body);
        }

        .brand-hero {
            display: flex;
            align-items: center;
            gap: 2.2rem;
            padding: 2rem 2.4rem;
            border-radius: 24px;
            position: relative;
            overflow: hidden;
            background: linear-gradient(135deg, var(--accent-start), var(--accent-end));
            box-shadow: 0 32px 58px -32px var(--accent-shadow);
            color: var(--text-on-primary);
        }

        .brand-hero::after {
            content: "";
            position: absolute;
            inset: 0;
            background: radial-gradient(
                circle at top right,
                color-mix(in srgb, var(--text-on-primary) 28%, transparent),
                transparent 60%
            );
            opacity: 0.75;
            pointer-events: none;
        }

        .brand-hero__visual {
            position: relative;
            z-index: 1;
            flex: 0 0 auto;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 0.4rem 0;
        }

        .brand-hero__visual img {
            width: 100%;
            max-width: 200px;
            height: auto;
            filter: drop-shadow(0 18px 32px color-mix(in srgb, var(--backgroundColor) 55%, transparent));
        }

        .brand-hero__content {
            position: relative;
            z-index: 1;
        }

        .brand-hero__content p {
            color: color-mix(in srgb, var(--text-on-primary) 88%, var(--backgroundColor) 12%);
        }

        .brand-hero__badge {
            position: absolute;
            top: 2rem;
            right: 2rem;
            padding: 0.55rem 1.2rem;
            background: color-mix(in srgb, var(--text-on-primary) 12%, transparent);
            backdrop-filter: blur(8px);
            border-radius: 9999px;
            color: var(--text-on-primary);
            font-size: 0.9rem;
            font-weight: 600;
        }

        @media (max-width: 960px) {
            .brand-hero {
                flex-direction: column;
                text-align: center;
                gap: 1.6rem;
                padding: 1.8rem;
            }

            .brand-hero__badge {
                position: static;
                margin-top: 1rem;
                align-self: center;
            }

            .brand-hero__visual img {
                max-width: 160px;
            }
        }

        div[data-testid="stTextArea"] {
            margin-top: 1.05rem;
        }

        div[data-testid="stTextArea"] label {
            color: var(--text-label) !important;
            font-weight: 600;
            font-size: var(--font-label);
        }

        div[data-testid="stTextArea"] textarea {
            background: var(--code-background) !important;
            color: var(--text-body) !important;
            border-radius: 14px !important;
            border: 1px solid var(--input-border) !important;
            min-height: 220px;
            padding: 0.9rem 1rem !important;
            line-height: 1.6 !important;
            font-size: var(--font-body) !important;
        }

        div[data-testid="stTextArea"] textarea:hover,
        div[data-testid="stTextArea"] textarea:focus {
            border-color: var(--primary) !important;
            box-shadow: var(--hover-glow);
        }

        div[data-testid="stMetricValue"] {
            color: var(--primary);
            font-weight: 700;
        }

        div[data-testid="stJson"] pre {
            background: var(--code-background);
            color: var(--text-body) !important;
            border-radius: 16px;
            padding: 1.1rem 1.25rem;
            font-size: calc(var(--font-body) - 0.2px);
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

def _render_sidebar() -> str:
    """渲染側邊欄並返回選擇的品牌。"""
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
        
        # 品牌選擇
        brand = st.selectbox(
            "選擇品牌",
            options,
            key="unified_brand"
        )
        
        # 品牌標籤
        st.markdown(
            f"""<span class='sidebar-badge'>現在瀏覽：{html.escape(brand)}</span>""",
            unsafe_allow_html=True,
        )

        # 說明文字
        st.markdown(
            """<p class='sidebar-note'>"""
            """所有模組共用相同的視覺語言與互動效果，確保跨品牌的一致體驗。"""
            """</p>""",
            unsafe_allow_html=True,
        )

        # 分隔線
        st.divider()
        
        return brand

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

    theme = BRAND_THEMES.get(brand, DEFAULT_THEME)
    accent_start = theme.get("start", DEFAULT_THEME["start"])
    accent_end = theme.get("end", DEFAULT_THEME["end"])
    accent_shadow = theme.get("shadow", DEFAULT_THEME["shadow"])

    for row in _chunked(highlights, 3):
        columns = st.columns(len(row))
        for column, (icon, title, desc) in zip(columns, row):
            variant = FEATURE_VARIANTS.get(title, "secondary")
            column.markdown(
                f"""
                <div class="feature-card" data-variant="{html.escape(variant)}" style="--feature-accent-start: {accent_start}; --feature-accent-end: {accent_end}; --feature-accent-shadow: {accent_shadow};">
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
    logo_src = theme_controller.get_logo_data_uri()
    visual_html = ""
    if logo_src:
        visual_html = (
            f"<div class=\"brand-hero__visual\"><img src=\"{logo_src}\" alt=\"{html.escape(title)} 標誌\" /></div>"
        )

    # Add hero card styles
    st.markdown("""
        <style>
        .brand-hero {
            background: linear-gradient(135deg, var(--accent-start), var(--accent-end));
            border-radius: 24px;
            padding: 2rem 2.4rem;
            margin: 1rem 0;
            position: relative;
            box-shadow: 0 20px 40px -12px var(--accent-shadow);
            display: flex;
            align-items: center;
            gap: 2.4rem;
            overflow: hidden;
        }
        .brand-hero__visual {
            position: relative;
            z-index: 1;
            flex: 0 0 auto;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 0.5rem 0;
        }
        .brand-hero__visual img {
            max-width: 200px;
            width: 100%;
            height: auto;
            filter: drop-shadow(0 18px 32px rgba(15, 23, 42, 0.45));
        }
        .brand-hero__content {
            max-width: 640px;
            position: relative;
            z-index: 1;
        }
        .brand-hero__eyebrow {
            font-size: 0.875rem;
            font-weight: 600;
            letter-spacing: 0.14em;
            color: rgba(255, 255, 255, 0.9);
            margin-bottom: 0.75rem;
        }
        .brand-hero h1 {
            color: white;
            font-size: clamp(2.6rem, 2vw + 2.2rem, 3.2rem);
            margin: 0.35rem 0 0.9rem;
            font-weight: 700;
            letter-spacing: 0.01em;
        }
        .brand-hero p {
            color: rgba(255, 255, 255, 0.9);
            font-size: 1.12rem;
            margin: 0;
            line-height: 1.55;
        }
        .brand-hero__badge {
            position: absolute;
            top: 2rem;
            right: 2rem;
            padding: 0.55rem 1.2rem;
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(8px);
            border-radius: 9999px;
            color: white;
            font-size: 0.9rem;
            font-weight: 600;
        }
        @media (max-width: 960px) {
            .brand-hero {
                flex-direction: column;
                text-align: center;
                gap: 1.6rem;
                padding: 1.8rem;
            }
            .brand-hero__badge {
                position: static;
                margin-top: 1rem;
                align-self: center;
            }
            .brand-hero__visual img {
                max-width: 160px;
            }
        }
        </style>
    """, unsafe_allow_html=True)

    # Render hero card
    st.markdown(
        f"""
        <div class="brand-hero" style="--accent-start: {theme['start']}; --accent-end: {theme['end']}; --accent-shadow: {theme['shadow']}">
            {visual_html}
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
    """主應用程式入口點。"""
    _ensure_session_defaults()
    brand = _render_sidebar()
    
    if brand:
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
