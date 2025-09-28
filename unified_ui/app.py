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

THEME_PRESETS = theme_controller.get_theme_presets()
FEATURE_VARIANT_STYLES = theme_controller.get_feature_variants()
DEFAULT_THEME_KEY = theme_controller.get_default_theme()
SIDEBAR_CONFIG = theme_controller.get_sidebar_config()

SIDEBAR_TITLE = SIDEBAR_CONFIG.get("title", "D-FLARE Unified")
SIDEBAR_TAGLINE = SIDEBAR_CONFIG.get(
    "tagline", "跨品牌威脅分析流程，以一致的體驗呈現。"
)
SIDEBAR_DESCRIPTION = SIDEBAR_CONFIG.get("description", "")
SIDEBAR_CUSTOMIZE = SIDEBAR_CONFIG.get("customize_help", "")
SIDEBAR_OPTIONS = SIDEBAR_CONFIG.get("options", {}) or {}
SIDEBAR_ORDER = SIDEBAR_CONFIG.get("order", []) or []


def _resolve_default_brand() -> str:
    for candidate in SIDEBAR_ORDER:
        if candidate in BRAND_RENDERERS:
            return candidate
    for candidate in SIDEBAR_OPTIONS:
        if candidate in BRAND_RENDERERS:
            return candidate
    return next(iter(BRAND_RENDERERS.keys()))


DEFAULT_BRAND = _resolve_default_brand()
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
    st.session_state.setdefault("unified_brand", DEFAULT_BRAND)
    st.session_state.setdefault("fortinet_menu_collapse", False)
    st.session_state.setdefault("cisco_menu_collapse", False)


def _get_active_palette() -> dict[str, str]:
    base = (st.get_option("theme.base") or DEFAULT_THEME_KEY or "dark").lower()
    palette = THEME_PRESETS.get(base)
    if not palette and THEME_PRESETS:
        palette = next(iter(THEME_PRESETS.values()))
    return dict(palette or {})


def _apply_theme_styles(palette: dict[str, str]) -> None:
    if not st.session_state.get("_unified_icons_loaded"):
        st.markdown(
            "<link rel=\"stylesheet\" href=\"https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.min.css\">",
            unsafe_allow_html=True,
        )
        st.session_state["_unified_icons_loaded"] = True
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
            --text-body: {palette.get('text_body', palette['text_secondary'])};
            --text-caption: {palette.get('text_caption', palette['text_secondary'])};
            --text-label: {palette.get('text_label', palette['text_secondary'])};
            --text-h1: {palette.get('text_h1', palette['text_primary'])};
            --text-h2: {palette.get('text_h2', palette['text_primary'])};
            --text-h3: {palette.get('text_h3', palette['text_primary'])};
            --font-h1: 20.8px;
            --font-h2: 17.6px;
            --font-h3: 14.4px;
            --font-label: 12.8px;
            --font-body: 12.4px;
            --font-caption: 10.8px;
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
            color: var(--text-body) !important;
            font-family: "Noto Sans TC", "Inter", "Segoe UI", system-ui, -apple-system,
                BlinkMacSystemFont, sans-serif;
            font-size: var(--font-body);
            line-height: 1.65;
        }}

        div[data-testid="stAppViewContainer"] .main .block-container {{
            color: var(--text-body) !important;
            font-size: var(--font-body);
            line-height: 1.65;
        }}

        div[data-testid="stAppViewContainer"] .main .block-container p,
        div[data-testid="stAppViewContainer"] .main .block-container span,
        div[data-testid="stAppViewContainer"] .main .block-container li,
        div[data-testid="stAppViewContainer"] .main .block-container label,
        div[data-testid="stAppViewContainer"] .main .block-container .stMarkdown p,
        div[data-testid="stAppViewContainer"] .main .block-container .stMarkdown li {{
            color: var(--text-body) !important;
            font-size: var(--font-body);
        }}

        div[data-testid="stAppViewContainer"] ::placeholder {{
            color: var(--text-caption) !important;
            opacity: 0.85;
        }}

        div[data-testid="stAppViewContainer"] .main .block-container h1,
        div[data-testid="stAppViewContainer"] .main .block-container .stMarkdown h1 {{
            color: var(--text-h1) !important;
            font-size: var(--font-h1);
            font-weight: 700;
            letter-spacing: 0.01em;
            margin-top: 0;
            margin-bottom: 0.75rem;
        }}

        div[data-testid="stAppViewContainer"] .main .block-container h2,
        div[data-testid="stAppViewContainer"] .main .block-container .stMarkdown h2 {{
            color: var(--text-h2) !important;
            font-size: var(--font-h2);
            font-weight: 600;
            margin-top: 2.2rem;
            margin-bottom: 0.75rem;
        }}

        div[data-testid="stAppViewContainer"] .main .block-container h3,
        div[data-testid="stAppViewContainer"] .main .block-container h4,
        div[data-testid="stAppViewContainer"] .main .block-container .stMarkdown h3,
        div[data-testid="stAppViewContainer"] .main .block-container .stMarkdown h4 {{
            color: var(--text-h3) !important;
            font-size: var(--font-h3);
            font-weight: 600;
            margin-top: 1.8rem;
            margin-bottom: 0.6rem;
        }}

        div[data-testid="stAppViewContainer"] .main .block-container h5,
        div[data-testid="stAppViewContainer"] .main .block-container h6,
        div[data-testid="stAppViewContainer"] .main .block-container .stMarkdown h5,
        div[data-testid="stAppViewContainer"] .main .block-container .stMarkdown h6 {{
            color: var(--text-label) !important;
            font-size: calc(var(--font-label) - 1px);
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            margin-top: 1.6rem;
            margin-bottom: 0.5rem;
        }}

        div[data-testid="stAppViewContainer"] .main .block-container label,
        div[data-testid="stAppViewContainer"] .main .block-container .stMarkdown label,
        div[data-testid="stAppViewContainer"] .main .block-container [data-testid="stForm"] label,
        div[data-testid="stAppViewContainer"] .main .block-container [data-testid="stExpander"] label {{
            color: var(--text-label) !important;
            font-size: var(--font-label);
            font-weight: 500;
        }}

        body small,
        body .stCaption,
        body .caption,
        div[data-testid="stAppViewContainer"] .main .block-container small,
        div[data-testid="stAppViewContainer"] .main .block-container .stCaption,
        div[data-testid="stAppViewContainer"] .main .block-container .caption {{
            color: var(--text-caption) !important;
            font-size: var(--font-caption);
            line-height: 1.55;
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

        div[data-testid="stSidebar"] .sidebar-toggle-wrapper {{
            display: inline-flex;
            width: 100%;
            align-items: center;
            justify-content: flex-end;
            margin-bottom: 0.35rem;
            padding-top: 0.15rem;
        }}

        div[data-testid="stSidebar"] .sidebar-toggle-wrapper div[data-testid="stToggle"] {{
            margin: 0;
        }}

        div[data-testid="stSidebar"] .sidebar-toggle-wrapper label {{
            display: inline-flex;
            align-items: center;
            gap: 0.4rem;
            font-weight: 600;
            color: var(--sidebar-text);
            font-size: 0.95rem;
        }}

        div[data-testid="stSidebar"] .sidebar-toggle-wrapper [data-baseweb="toggle"] {{
            background-color: rgba(139, 233, 221, 0.2);
            border-radius: 999px;
            transition: background-color 0.25s ease;
        }}

        div[data-testid="stSidebar"] .sidebar-toggle-wrapper [data-baseweb="toggle"][aria-checked="true"] {{
            background-color: rgba(26, 188, 156, 0.75);
        }}

        div[data-testid="stSidebar"] .sidebar-eyebrow {{
            display: inline-flex;
            align-items: center;
            font-size: 0.85rem;
            letter-spacing: 0.18em;
            text-transform: uppercase;
            color: var(--sidebar-muted);
            font-weight: 700;
        }}

        div[data-testid="stSidebar"] .sidebar-title {{
            font-size: 1.45rem;
            font-weight: 700;
            margin: 0.3rem 0 0.4rem;
            color: var(--sidebar-text);
        }}

        div[data-testid="stSidebar"] .sidebar-tagline {{
            font-size: 0.95rem;
            line-height: 1.65;
            color: var(--sidebar-muted);
            margin: 0;
        }}

        div[data-testid="stSidebar"] div[data-testid="stRadio"] > label {{
            display: none;
        }}

        div[data-testid="stSidebar"] div[data-testid="stRadio"] > div[role="radiogroup"] {{
            display: flex;
            flex-direction: column;
            gap: 0.65rem;
            margin-top: 1.4rem;
        }}

        div[data-testid="stSidebar"] div[data-testid="stRadio"] > div[role="radiogroup"] > div {{
            margin: 0 !important;
        }}

        div[data-testid="stSidebar"] div[data-testid="stRadio"] label {{
            border-radius: 16px;
            border: 1px solid var(--muted-border);
            padding: 0.85rem 1.05rem;
            background: var(--app-surface);
            display: flex;
            align-items: center;
            gap: 0.7rem;
            font-weight: 600;
            font-size: var(--font-label);
            color: var(--sidebar-text);
            cursor: pointer;
            transition: border-color 0.2s ease, box-shadow 0.2s ease, transform 0.2s ease,
                background 0.2s ease, color 0.2s ease;
        }}

        div[data-testid="stSidebar"] div[data-testid="stRadio"] label:hover {{
            border-color: var(--primary);
            box-shadow: var(--hover-glow);
            transform: translateX(4px);
        }}

        div[data-testid="stSidebar"] div[data-testid="stRadio"] label > div:first-child {{
            display: none;
        }}

        div[data-testid="stSidebar"] div[data-testid="stRadio"] input[type="radio"] {{
            display: none;
        }}

        div[data-testid="stSidebar"] div[data-testid="stRadio"] label:has(div[role="radio"][aria-checked="true"]) {{
            background: linear-gradient(135deg, var(--primary), var(--primary-hover));
            color: #ffffff;
            border-color: transparent;
            box-shadow: var(--hover-glow);
        }}

        div[data-testid="stSidebar"] .sidebar-note {{
            margin: 1.25rem 0 0;
            font-size: calc(var(--font-body) - 1px);
            line-height: 1.6;
            color: var(--sidebar-muted);
        }}

        div[data-testid="stSidebar"] div[data-testid="stToggle"] {{
            border: 1px solid var(--muted-border);
            border-radius: 16px;
            padding: 0.8rem 0.9rem;
            background: var(--app-surface);
            box-shadow: 0 28px 42px -34px var(--primary-shadow);
            margin: 1.1rem 0 1.7rem;
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
            padding: 2px;
            border: 1px solid transparent;
            box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.04);
        }}

        div[data-testid="stSidebar"] div[data-testid="stToggle"] [role="switch"][aria-checked="true"] {{
            background: linear-gradient(135deg, var(--primary), var(--primary-hover));
            box-shadow: 0 20px 42px -28px var(--primary-shadow);
        }}

        div[data-testid="stSidebar"] div[data-testid="stToggle"] [role="switch"] > div {{
            background: var(--app-surface);
            border-radius: 50%;
            box-shadow: 0 6px 14px rgba(15, 23, 42, 0.28);
        }}

        div[data-testid="stSidebar"] .stSelectbox > label {{
            font-size: 0.9rem;
            font-weight: 600;
            color: var(--sidebar-text) !important;
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
            margin-top: 1.5rem;
            display: flex;
            flex-direction: column;
            gap: 0.5rem;
        }}

        div[data-testid="stSidebar"] .sidebar-nav .nav-link {{
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
            transition: transform 0.25s ease, box-shadow 0.25s ease, background 0.25s ease;
        }}

        div[data-testid="stSidebar"] .sidebar-nav .nav-link:hover {{
            background: var(--sidebar-button-hover) !important;
            color: var(--sidebar-text) !important;
            transform: translateX(4px) scale(1.01);
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
            transform: translateX(4px) scale(1.01);
        }}

        div[data-testid="stSidebar"] .sidebar-nav .nav-link-selected i {{
            color: #ffffff !important;
        }}

        div[data-testid="stSidebar"] .sidebar-menu-description {{
            color: var(--sidebar-muted) !important;
            font-size: calc(var(--font-body) - 1px);
            margin: 0.45rem 0 1.3rem;
            line-height: 1.65;
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
            font-size: 0.88rem;
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
            font-size: var(--font-label);
            display: inline-flex;
            align-items: center;
            justify-content: center;
            gap: 0.45rem;
            letter-spacing: 0.01em;
            box-shadow: var(--hover-glow);
            margin: 0.2rem 0.35rem 0.2rem 0;
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
            outline: 2px solid rgba(26, 188, 156, 0.45);
            outline-offset: 3px;
        }}

        .stButton > button:disabled,
        .stDownloadButton > button:disabled,
        .stFormSubmitButton > button:disabled {{
            box-shadow: none;
            opacity: 0.65;
        }}

        div[data-testid="stFileUploader"] {{
            margin-bottom: 1.75rem;
        }}

        div[data-testid="stFileUploader"] > label {{
            font-weight: 600;
            font-size: var(--font-label);
            color: var(--text-label);
            margin-bottom: 0.65rem;
        }}

        div[data-testid="stFileUploader"] section[data-testid="stFileUploaderDropzone"] {{
            border: 1px dashed var(--upload-border);
            background: var(--upload-background);
            color: var(--upload-text) !important;
            border-radius: 18px;
            padding: 1.25rem 1.35rem;
            box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.05);
        }}

        div[data-testid="stFileUploader"] section[data-testid="stFileUploaderDropzone"]:hover {{
            border-color: var(--primary);
            transform: translateY(-2px) scale(1.01);
            box-shadow: var(--hover-glow);
        }}

        div[data-testid="stFileUploader"] section[data-testid="stFileUploaderDropzone"] span {{
            color: var(--upload-text) !important;
        }}

        div[data-testid="stFileUploader"] section[data-testid="stFileUploaderDropzone"] p,
        div[data-testid="stFileUploader"] section[data-testid="stFileUploaderDropzone"] small {{
            color: var(--upload-text) !important;
        }}

        div[data-testid="stFileUploader"] button {{
            background: linear-gradient(135deg, var(--primary), var(--primary-hover));
            color: #ffffff;
            border: none;
            border-radius: 12px;
            padding: 0.55rem 1.25rem;
            font-weight: 600;
            font-size: var(--font-label);
            box-shadow: var(--hover-glow);
        }}

        div[data-testid="stFileUploader"] button:hover {{
            transform: translateY(-1px) scale(1.01);
            box-shadow: 0 24px 44px -26px var(--primary-shadow);
        }}

        div[data-testid="stToggle"] {{
            margin-bottom: 1.1rem;
        }}

        div[data-testid="stToggle"] label {{
            color: var(--text-label);
            font-weight: 600;
            font-size: var(--font-label);
        }}

        div[data-testid="stToggle"] [role="switch"] {{
            border-radius: 999px;
            background: var(--muted-border);
            padding: 2px;
            border: 1px solid transparent;
            transition: background 0.3s ease, box-shadow 0.3s ease, transform 0.3s ease;
        }}

        div[data-testid="stToggle"] [role="switch"][aria-checked="true"] {{
            background: linear-gradient(135deg, var(--primary), var(--primary-hover));
            box-shadow: var(--hover-glow);
        }}

        div[data-testid="stToggle"] [role="switch"] > div {{
            background: var(--app-surface);
            border-radius: 50%;
            box-shadow: 0 4px 10px rgba(15, 23, 42, 0.28);
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

        .stTabs [role="tablist"] {{
            gap: 0.6rem;
            border-bottom: none;
            padding-bottom: 0.35rem;
        }}

        .stTabs [role="tab"] {{
            border-radius: 14px;
            padding: 0.6rem 1.35rem;
            font-weight: 600;
            font-size: var(--font-label);
            color: var(--text-label);
            background: var(--app-surface-muted);
            border: 1px solid var(--muted-border);
            transition: transform 0.25s ease, box-shadow 0.25s ease, color 0.25s ease;
        }}

        .stTabs [role="tab"]:hover {{
            color: var(--text-h2);
            transform: translateY(-1px);
            box-shadow: var(--hover-glow);
        }}

        .stTabs [role="tab"][aria-selected="true"] {{
            background: linear-gradient(135deg, var(--primary), var(--primary-hover));
            color: #ffffff;
            box-shadow: var(--hover-glow);
            border-color: transparent;
        }}

        .stTabs [role="tabpanel"] {{
            background: var(--card-background);
            border: 1px solid var(--muted-border);
            border-radius: 20px;
            padding: 1.4rem 1.5rem 1.6rem;
            box-shadow: var(--card-shadow);
            margin-top: 0.85rem;
        }}

        div[data-testid="stExpander"] > details {{
            background: var(--expander-background);
            border-radius: 18px;
            border: 1px solid var(--muted-border);
            overflow: hidden;
            box-shadow: var(--card-shadow);
        }}

        div[data-testid="stExpander"] > details > summary {{
            background: var(--expander-header);
            color: var(--text-label);
            padding: 1rem 1.25rem;
            font-weight: 600;
            font-size: var(--font-label);
        }}

        div[data-testid="stExpander"] > details > summary:hover {{
            filter: brightness(1.05);
            box-shadow: var(--hover-glow);
        }}

        div[data-testid="stExpander"] > details div[data-testid="stExpanderContent"] {{
            padding: 1.15rem 1.25rem 1.35rem;
            color: var(--text-body);
        }}

        .brand-hero {{
            display: flex;
            align-items: center;
            gap: 2.2rem;
            padding: 2rem 2.4rem;
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

        .brand-hero__visual {{
            position: relative;
            z-index: 1;
            flex: 0 0 auto;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 0.4rem 0;
        }}

        .brand-hero__visual img {{
            width: 100%;
            max-width: 200px;
            height: auto;
            filter: drop-shadow(0 18px 32px rgba(15, 23, 42, 0.45));
        }}

        .brand-hero__content {{
            position: relative;
            z-index: 1;
            max-width: 640px;
        }}

        .brand-hero__eyebrow {{
            font-size: 0.86rem;
            text-transform: uppercase;
            letter-spacing: 0.14em;
            font-weight: 600;
            opacity: 0.95;
            margin-bottom: 0.7rem;
        }}

        .brand-hero h1 {{
            margin: 0.35rem 0 0.9rem;
            font-size: clamp(2.6rem, 2vw + 2.2rem, 3.2rem);
            font-weight: 700;
            letter-spacing: 0.01em;
        }}

        .brand-hero p {{
            margin: 0;
            font-size: 1.12rem;
            line-height: 1.55;
            color: rgba(255, 255, 255, 0.95);
        }}

        .brand-hero__badge {{
            position: relative;
            z-index: 1;
            padding: 0.55rem 1.2rem;
            border-radius: 999px;
            border: 1px solid rgba(255, 255, 255, 0.48);
            background: rgba(15, 23, 42, 0.32);
            font-weight: 600;
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
            font-size: 0.92rem;
            box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.35);
        }}

        @media (max-width: 960px) {{
            .brand-hero {{
                flex-direction: column;
                text-align: center;
                gap: 1.6rem;
                padding: 1.8rem;
            }}

            .brand-hero__badge {{
                align-self: center;
            }}

            .brand-hero__visual img {{
                max-width: 160px;
            }}
        }}

        .feature-card {{
            position: relative;
            padding: 2.35rem 2.05rem 1.85rem;
            border-radius: 22px;
            border: 1px solid var(--card-border);
            background: var(--card-body, var(--card-background));
            box-shadow: var(--card-shadow);
            transition: transform 0.35s ease, box-shadow 0.35s ease;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            text-align: center;
            gap: 1rem;
            margin-top: 1.5rem;
            margin-inline: auto;
            overflow: hidden;
        }}

        .feature-card::before {{
            content: "";
            position: absolute;
            inset: -45% -45% 55% -45%;
            background: linear-gradient(
                135deg,
                var(--card-accent-start, var(--primary)),
                var(--card-accent-end, var(--primary-hover))
            );
            opacity: 0.95;
            z-index: 0;
            transition: opacity 0.35s ease;
        }}

        .feature-card:hover {{
            transform: translateY(-6px) scale(1.02);
            box-shadow: var(--card-hover-glow, var(--hover-glow));
        }}

        .feature-card:hover::before {{
            opacity: 1;
        }}

        .feature-card__icon,
        .feature-card__title,
        .feature-card__desc {{
            position: relative;
            z-index: 1;
        }}

        .feature-card__icon {{
            width: 56px;
            height: 56px;
            border-radius: 50%;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            font-size: 1.65rem;
            margin: 0 auto 1.15rem;
            background: var(--card-icon-background, rgba(255, 255, 255, 0.2));
            color: var(--card-icon-color, #ffffff);
            box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.25);
            backdrop-filter: blur(4px);
        }}

        .feature-card__title {{
            font-size: var(--font-h3);
            font-weight: 700;
            color: var(--text-h3) !important;
            margin-bottom: 0.25rem;
            text-align: center;
        }}

        .feature-card__desc {{
            color: var(--text-body) !important;
            margin: 0;
            font-size: calc(var(--font-body) - 0.3px);
            line-height: 1.65;
            text-align: center;
        }}

        .path-preview {{
            display: flex;
            align-items: center;
            gap: 0.85rem;
            background: var(--app-surface-muted);
            border: 1px solid var(--muted-border);
            border-radius: 16px;
            padding: 0.85rem 1.1rem;
            margin-bottom: 0.85rem;
            box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.04);
        }}

        .path-preview__icon {{
            width: 36px;
            height: 36px;
            border-radius: 12px;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            background: linear-gradient(135deg, var(--secondary-start), var(--secondary-end));
            color: #ffffff;
            font-size: 1.1rem;
            flex-shrink: 0;
        }}

        .path-preview__content {{
            display: flex;
            flex-direction: column;
            gap: 0.2rem;
        }}

        .path-preview__label {{
            font-weight: 600;
            color: var(--text-label) !important;
            font-size: calc(var(--font-label) - 1px);
        }}

        .path-preview__path {{
            color: var(--text-body) !important;
            font-family: "JetBrains Mono", "Roboto Mono", monospace;
            font-size: calc(var(--font-body) - 1px);
            word-break: break-all;
            line-height: 1.5;
        }}

        .path-preview--empty {{
            border-style: dashed;
            opacity: 0.85;
        }}

        .path-preview--empty .path-preview__icon {{
            background: rgba(148, 163, 184, 0.2);
            color: var(--text-secondary) !important;
        }}

        .path-preview--empty .path-preview__path {{
            color: var(--text-body) !important;
        }}

        div[data-testid="stCheckbox"] label p,
        div[data-testid="stCheckbox"] label span,
        div[data-testid="stRadio"] label p,
        div[data-testid="stRadio"] label span {{
            color: inherit !important;
        }}

        div[data-testid="stSidebar"] div[data-testid="stRadio"] label:has(div[role="radio"][aria-checked="true"]) * {{
            color: #ffffff !important;
        }}

        div[data-testid="stFileUploader"] > label {{
            color: var(--text-label) !important;
            font-weight: 600;
            font-size: var(--font-label);
            margin-bottom: 0.6rem;
        }}

        div[data-testid="stFileUploader"] section[data-testid="stFileUploaderDropzone"] {{
            background: var(--upload-background);
            border: 1.5px dashed var(--upload-border);
            border-radius: 18px;
            color: var(--upload-text) !important;
            padding: 1.35rem 1.1rem;
            transition: border-color 0.25s ease, box-shadow 0.25s ease,
                background 0.25s ease;
        }}

        div[data-testid="stFileUploader"] section[data-testid="stFileUploaderDropzone"]:hover {{
            border-color: var(--primary);
            box-shadow: var(--hover-glow);
        }}

        div[data-testid="stFileUploader"] section[data-testid="stFileUploaderDropzone"] span,
        div[data-testid="stFileUploader"] section[data-testid="stFileUploaderDropzone"] p,
        div[data-testid="stFileUploader"] section[data-testid="stFileUploaderDropzone"] small {{
            color: var(--upload-text) !important;
        }}

        div[data-testid="stFileUploader"] section[data-testid="stFileUploaderDropzone"] button {{
            background: linear-gradient(135deg, var(--secondary-start), var(--secondary-end));
            color: #ffffff;
            border: none;
            border-radius: 12px;
            font-weight: 600;
            padding: 0.55rem 1.2rem;
            box-shadow: var(--hover-glow);
        }}

        div[data-testid="stFileUploader"] section[data-testid="stFileUploaderDropzone"] button:hover {{
            filter: brightness(1.05);
        }}

        div[data-testid="stFileUploader"] .uploadedFile {{
            background: var(--app-surface-muted);
            border: 1px solid var(--muted-border);
            border-radius: 12px;
            color: var(--text-body) !important;
        }}

        div[data-testid="stFileUploader"] .uploadedFile span,
        div[data-testid="stFileUploader"] .uploadedFile small {{
            color: var(--text-body) !important;
        }}

        hr {{
            border-color: var(--muted-border);
            margin: 2.4rem 0 1.8rem;
        }}

        .stAlert {{
            border-radius: 16px;
            border: 1px solid var(--muted-border);
            background: var(--app-surface-muted);
            box-shadow: var(--hover-glow);
        }}

        .stAlert div[role="alert"] p {{
            color: var(--text-body) !important;
        }}

        .stAlert[data-baseweb="alert"][kind="warning"] {{
            border-left: 4px solid var(--warning);
        }}

        .stAlert[data-baseweb="alert"][kind="error"] {{
            border-left: 4px solid var(--warning-emphasis);
        }}

        code, pre {{
            background: var(--code-background);
            color: var(--text-body) !important;
            border-radius: 10px;
            padding: 0.2rem 0.45rem;
        }}

        div[data-baseweb="input"] input,
        div[data-baseweb="input"] textarea,
        div[data-baseweb="select"] > div {{
            background: var(--input-background) !important;
            color: var(--text-primary) !important;
            border-radius: 12px;
            font-size: var(--font-body) !important;
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

        div[data-testid="stTextArea"] {{
            margin-top: 1.05rem;
        }}

        div[data-testid="stTextArea"] label {{
            color: var(--text-label) !important;
            font-weight: 600;
            font-size: var(--font-label);
        }}

        div[data-testid="stTextArea"] textarea {{
            background: var(--code-background) !important;
            color: var(--text-body) !important;
            border-radius: 14px !important;
            border: 1px solid var(--input-border) !important;
            min-height: 220px;
            padding: 0.9rem 1rem !important;
            line-height: 1.6 !important;
            font-size: var(--font-body) !important;
        }}

        div[data-testid="stTextArea"] textarea:hover,
        div[data-testid="stTextArea"] textarea:focus {{
            border-color: var(--primary) !important;
            box-shadow: var(--hover-glow);
        }}

        div[data-testid="stMetricValue"] {{
            color: var(--primary);
            font-weight: 700;
        }}

        div[data-testid="stJson"] pre {{
            background: var(--code-background);
            color: var(--text-body) !important;
            border-radius: 16px;
            padding: 1.1rem 1.25rem;
            font-size: calc(var(--font-body) - 0.2px);
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def _render_sidebar() -> str:
    """渲染側邊欄並返回選擇的品牌。"""
    configured_options = [
        (key, meta)
        for key, meta in theme_controller.iter_sidebar_options()
        if key in BRAND_RENDERERS
    ]
    if not configured_options:
        configured_options = [
            (key, SIDEBAR_OPTIONS.get(key, {})) for key in BRAND_RENDERERS.keys()
        ]
    option_keys = [key for key, _ in configured_options]
    icons = {key: meta.get("icon", "") for key, meta in configured_options}
    badges = {key: meta.get("badge", key) for key, meta in configured_options}
    descriptions = {
        key: meta.get("description", BRAND_DESCRIPTIONS.get(key, ""))
        for key, meta in configured_options
    }

    with st.sidebar:
        st.markdown(
            f"""
            <div class="sidebar-heading">
                <span class="sidebar-eyebrow">Unified Console</span>
                <div class="sidebar-title">{html.escape(SIDEBAR_TITLE)}</div>
                <p class="sidebar-tagline">{html.escape(SIDEBAR_TAGLINE)}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        brand = st.radio(
            "選擇品牌",
            option_keys,
            key="unified_brand",
            label_visibility="collapsed",
            format_func=lambda key: f"{icons.get(key, '')} {badges.get(key, key)}".strip(),
        )

        # 品牌標籤
        st.markdown(
            f"""<span class='sidebar-badge'>現在瀏覽：{html.escape(brand)}</span>""",
            unsafe_allow_html=True,
        )

        # 說明文字
        note = descriptions.get(brand) or SIDEBAR_DESCRIPTION
        if note:
            st.markdown(
                f"<p class='sidebar-note'>{html.escape(note)}</p>",
                unsafe_allow_html=True,
            )

        if SIDEBAR_CUSTOMIZE:
            with st.expander("⚙️ 介面設定", expanded=False):
                st.markdown(SIDEBAR_CUSTOMIZE, unsafe_allow_html=False)
                st.markdown(
                    "<small>更多主題範例可參考官方 theming overview（Spotify 與 Anthropic 案例）。</small>",
                    unsafe_allow_html=True,
                )

        # 分隔線
        st.divider()

        return brand


def _chunked(seq: Sequence[_T], size: int) -> Iterator[Sequence[_T]]:
    for idx in range(0, len(seq), size):
        yield seq[idx : idx + size]


def _render_brand_highlights(brand: str) -> bool:
    highlights = BRAND_HIGHLIGHTS.get(brand)
    if not highlights:
        return False

    st.markdown('<div class="feature-cards-container">', unsafe_allow_html=True)

    for row in _chunked(highlights, 3):
        columns = st.columns(len(row))
        for column, (icon, title, desc) in zip(columns, row):
            variant = FEATURE_VARIANTS.get(title, "secondary")
            style_config = FEATURE_VARIANT_STYLES.get(variant, {})
            style_parts = []
            gradient = style_config.get("accent_gradient")
            if isinstance(gradient, (list, tuple)) and len(gradient) >= 2:
                style_parts.append(f"--card-accent-start: {gradient[0]};")
                style_parts.append(f"--card-accent-end: {gradient[1]};")
            if style_config.get("body_background"):
                style_parts.append(f"--card-body: {style_config['body_background']};")
            if style_config.get("border"):
                style_parts.append(f"--card-border: {style_config['border']};")
            if style_config.get("hover_glow"):
                style_parts.append(f"--card-hover-glow: {style_config['hover_glow']};")
            if style_config.get("icon_background"):
                style_parts.append(f"--card-icon-background: {style_config['icon_background']};")
            if style_config.get("icon_color"):
                style_parts.append(f"--card-icon-color: {style_config['icon_color']};")
            style_attr = " ".join(style_parts)
            column.markdown(
                f"""
                <div class="feature-card" data-variant="{html.escape(variant)}" style="{style_attr}">
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
    theme = theme_controller.get_brand_hero(brand)
    start = theme.get("start", "#6366f1")
    end = theme.get("end", "#8b5cf6")
    shadow = theme.get("shadow", "rgba(99, 102, 241, 0.45)")
    eyebrow = theme.get("eyebrow", "Unified Threat Analytics")
    icon = theme.get("icon", "🧭")
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
        <div class="brand-hero" style="--accent-start: {start}; --accent-end: {end}; --accent-shadow: {shadow}">
            {visual_html}
            <div class="brand-hero__content">
                <div class="brand-hero__eyebrow">{html.escape(eyebrow)}</div>
                <h1>{html.escape(title)}</h1>
                {description_html}
            </div>
            <span class="brand-hero__badge">{html.escape(icon)} {html.escape(brand)}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )


def main() -> None:
    """主應用程式入口點。"""
    _ensure_session_defaults()
    palette = _get_active_palette()
    if palette:
        _apply_theme_styles(palette)
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
