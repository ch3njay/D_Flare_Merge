"""跨品牌統一介面的現代化版本。"""
from __future__ import annotations

import csv
import html
import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterable, Iterator, Mapping, Optional, Sequence, Tuple, TypeVar

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

try:  # noqa: E402 - 在 UI 層重用 Fortinet 的 log 解析工具
    from Forti_ui_app_bundle.etl_pipeline.log_cleaning import (
        parse_log_line as fortinet_parse_log_line,
    )
except Exception:  # pragma: no cover - 執行環境缺少相依時提供安全退化
    fortinet_parse_log_line = None

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
    "Fortinet": "完整的威脅防護與 AI 推論解決方案，提供訓練、ETL、推論與多平台通知流程。",
    "Cisco": "專業的 ASA 防火牆日誌分析平台，專注於日誌擷取、智能推論與即時通知。",
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

LOG_SETTINGS_PATH = _PROJECT_ROOT / "logfetcher_settings.json"
_LOG_FILE_EXTENSIONS = (".csv", ".log", ".txt", ".json", ".jsonl")
_THREAT_ACTIONS = {"deny", "blocked", "drop", "reset", "timeout", "reject"}
_ALLOWED_ACTIONS = {"allow", "accept", "pass", "permit", "success"}
_THREAT_LEVELS = {"critical", "high", "alert", "warning", "severe"}
_LOG_SAMPLE_LIMIT = 5000
_KV_FALLBACK_PATTERN = re.compile(r"(\w+)=([\w./:@-]+|\".*?\"|'.*?')")
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
    st.session_state.setdefault("fortinet_menu_collapse", False)
    st.session_state.setdefault("cisco_menu_collapse", False)
    st.session_state.setdefault("show_dashboard", False)
    st.session_state.setdefault("show_settings", False)
    st.session_state.setdefault("discord_notify", True)
    st.session_state.setdefault("slack_notify", False)
    st.session_state.setdefault("log_retention", 30)
    st.session_state.setdefault("log_sidebar_metrics_prev", None)

    current_theme = theme_controller.get_current_theme()
    st.session_state.setdefault("ui_theme_choice", current_theme)
    theme_controller.switch_theme(st.session_state["ui_theme_choice"])

    # 增強主題樣式（改用 Theme Controller 提供的 CSS 變數）
    st.markdown("""
        <style>
        /* === 基礎變數定義：尊重主題控制器提供的參數 === */
        :root {
            --primary-color: var(--theme-customTheme-primary-gradient-start, #6366f1);
            --primary-hover: color-mix(in srgb, var(--theme-customTheme-primary-gradient-end, #8b5cf6) 85%, #ffffff 15%);
            --background-color: var(--theme-customTheme-card-background, #0F1419);
            --secondary-bg-color: color-mix(in srgb, var(--background-color) 82%, #111827 18%);
            --text-color: var(--theme-customTheme-sidebar-text, #E6E8EB);
            --muted-text: var(--theme-customTheme-sidebar-muted, #94a3b8);
            --border-color: var(--theme-customTheme-card-border, #2D3748);
            --success-color: #4CAF50;
            --warning-color: #FFA726;
            --error-color: #FF4757;
            --info-color: #42A5F5;
        }

        /* === 主體背景 === */
        .stApp {
            background-color: var(--background-color);
            color: var(--text-color);
        }

        /* === 增強側邊欄樣式 === */
        section[data-testid="stSidebar"] {
            background: var(--theme-customTheme-sidebar-background, linear-gradient(180deg, #0f172a 0%, #1e293b 100%));
            border-right: 1px solid var(--border-color);
            box-shadow: 4px 0 20px rgba(0, 0, 0, 0.3);
        }

        section[data-testid="stSidebar"] .stButton > button {
            background: linear-gradient(135deg, color-mix(in srgb, var(--primary-color) 75%, #1f2937 25%), color-mix(in srgb, var(--primary-hover) 70%, #111827 30%)) !important;
            border: 1px solid color-mix(in srgb, var(--primary-color) 60%, transparent) !important;
            color: #e2e8f0 !important;
            border-radius: 10px !important;
            padding: 0.8rem !important;
            font-weight: 600 !important;
            transition: all 0.3s ease !important;
            width: 100% !important;
            text-align: left !important;
        }

        section[data-testid="stSidebar"] .stButton > button:hover {
            background: linear-gradient(135deg, var(--primary-color), var(--primary-hover)) !important;
            border-color: color-mix(in srgb, var(--primary-hover) 70%, transparent) !important;
            transform: translateX(5px) !important;
            box-shadow: 0 8px 25px color-mix(in srgb, var(--primary-hover) 40%, transparent) !important;
        }

        section[data-testid="stSidebar"] .stMarkdown {
            color: var(--text-color) !important;
        }
        
        /* === 主內容區域（模擬 Wide mode 效果）=== */
        .main .block-container {
            background-color: var(--secondary-bg-color);
            border-radius: 12px;
            border: 1px solid var(--border-color);
            padding: 2rem 3rem;
            margin-top: 1rem;
            max-width: none;
        }
        
        /* === 品牌英雄卡片 === */
        .brand-hero {
            background: linear-gradient(135deg, #1e293b, #334155, #475569);
            border-radius: 20px;
            padding: 2.5rem;
            margin: 2rem 0;
            color: white;
            box-shadow: 0 15px 40px rgba(71, 85, 105, 0.4);
            display: flex;
            align-items: center;
            gap: 2rem;
            position: relative;
            overflow: hidden;
        }
        
        .brand-hero::before {
            content: "";
            position: absolute;
            top: -50%;
            right: -20%;
            width: 200px;
            height: 200px;
            background: radial-gradient(circle, rgba(255,255,255,0.1) 0%, transparent 70%);
            border-radius: 50%;
        }
        
        /* === 功能卡片 === */
        .feature-card {
            background: var(--secondary-bg-color);
            border: 1px solid var(--border-color);
            border-radius: 16px;
            padding: 2rem;
            margin: 0.5rem 0;
            transition: all 0.3s ease;
            box-shadow: 0 8px 25px rgba(0, 0, 0, 0.1);
            position: relative;
            overflow: hidden;
        }
        
        .feature-card::before {
            content: "";
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 4px;
            background: linear-gradient(90deg, var(--primary-color), var(--info-color));
        }
        
        .feature-card:hover {
            transform: translateY(-8px);
            box-shadow: 0 20px 50px rgba(99, 102, 241, 0.35);
            border-color: #6366f1;
        }
        
        /* === 按鈕樣式 === */
        .stButton > button {
            background: linear-gradient(135deg, #6366f1, #8b5cf6) !important;
            color: white !important;
            border: none !important;
            border-radius: 10px !important;
            font-weight: 600 !important;
            padding: 0.75rem 2rem !important;
            transition: all 0.3s ease !important;
            box-shadow: 0 6px 20px rgba(99, 102, 241, 0.4) !important;
        }
        
        .stButton > button:hover {
            transform: translateY(-3px) !important;
            box-shadow: 0 12px 35px rgba(139, 92, 246, 0.5) !important;
        }
        
        /* === 選擇框和輸入框 === */
        .stSelectbox > div > div {
            background-color: var(--secondary-bg-color) !important;
            border: 1px solid var(--border-color) !important;
            border-radius: 8px !important;
            color: var(--text-color) !important;
        }
        
        .stTextInput > div > div > input {
            background-color: var(--secondary-bg-color) !important;
            border: 1px solid var(--border-color) !important;
            color: var(--text-color) !important;
            border-radius: 8px !important;
        }
        
        /* === 標題樣式 === */
        .stMarkdown h1, .stMarkdown h2, .stMarkdown h3 {
            color: var(--text-color) !important;
        }
        
        .stMarkdown h1 {
            border-bottom: 3px solid var(--primary-color);
            padding-bottom: 0.5rem;
        }
        
        /* === 功能卡片容器 === */
        .feature-cards-container {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 2rem;
            margin: 2rem 0;
        }
        
        /* === 狀態標籤 === */
        .status-badge {
            padding: 0.25rem 0.75rem;
            border-radius: 20px;
            font-size: 0.8rem;
            font-weight: 600;
            display: inline-block;
            margin-top: 1rem;
        }
        
        .status-success { background-color: var(--success-color); color: white; }
        .status-warning { background-color: var(--warning-color); color: white; }
        .status-error { background-color: var(--error-color); color: white; }
        .status-info { background-color: var(--info-color); color: white; }
        
        /* === 響應式設計 === */
        @media (max-width: 768px) {
            .main .block-container {
                padding: 1.5rem;
                margin-top: 0.5rem;
            }
            
            .brand-hero {
                flex-direction: column;
                text-align: center;
                padding: 2rem;
                gap: 1.5rem;
            }
            
            .feature-cards-container {
                grid-template-columns: 1fr;
                gap: 1rem;
            }
        }
        
        /* === 隱藏預設元素 === */
        #MainMenu, header, footer {
            visibility: hidden;
        }
        
        .stDeployButton {
            visibility: hidden;
        }
        
        /* === 自訂滾動條 === */
        ::-webkit-scrollbar {
            width: 10px;
        }
        
        ::-webkit-scrollbar-track {
            background: var(--secondary-bg-color);
            border-radius: 5px;
        }
        
        ::-webkit-scrollbar-thumb {
            background: var(--primary-color);
            border-radius: 5px;
        }
        
        ::-webkit-scrollbar-thumb:hover {
            background: #FF8A50;
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
            background: linear-gradient(135deg, var(--primary), var(--primary-hover));
            color: var(--text-on-primary);
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
        }

        .stButton > button:hover,
        .stDownloadButton > button:hover,
        .stFormSubmitButton > button:hover {
            transform: translateY(-1px) scale(1.02);
            box-shadow: 0 26px 48px -24px var(--primary-shadow);
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


def _resolve_path(raw: str | None) -> Optional[Path]:
    if not raw:
        return None

    candidate = Path(str(raw)).expanduser()
    if not candidate.is_absolute():
        candidate = (LOG_SETTINGS_PATH.parent / candidate).resolve()
    return candidate


def _load_log_settings() -> Mapping[str, object]:
    if not LOG_SETTINGS_PATH.exists():
        return {}

    try:
        data = json.loads(LOG_SETTINGS_PATH.read_text(encoding="utf-8"))
        if isinstance(data, Mapping):
            return data
    except json.JSONDecodeError:
        pass
    return {}


def _iter_recent_log_files(
    settings: Mapping[str, object], metadata: Dict[str, list[str]], limit: int = 5
) -> list[Path]:
    files: list[tuple[float, Path]] = []
    seen: set[Path] = set()

    for key in ("clean_csv_dir", "save_dir"):
        raw_value = settings.get(key)
        resolved = _resolve_path(str(raw_value)) if raw_value else None
        if resolved is None:
            continue

        if not resolved.exists():
            metadata.setdefault("missing_paths", []).append(str(resolved))
            continue

        metadata.setdefault("available_paths", []).append(str(resolved))

        candidates: Iterable[Path]
        if resolved.is_file():
            candidates = (resolved,)
        else:
            candidates = (
                child
                for child in resolved.iterdir()
                if child.is_file() and child.suffix.lower() in _LOG_FILE_EXTENSIONS
            )

        for path in candidates:
            try:
                suffix = path.suffix.lower()
                if suffix not in _LOG_FILE_EXTENSIONS or path in seen:
                    continue
                seen.add(path)
                files.append((path.stat().st_mtime, path))
            except OSError:
                metadata.setdefault("errors", []).append(f"無法讀取檔案資訊：{path}")

    files.sort(key=lambda item: item[0], reverse=True)
    return [path for _, path in files[:limit]]


def _parse_datetime_value(value: str) -> Optional[datetime]:
    value = value.strip()
    if not value:
        return None

    formats = (
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M:%S.%f",
        "%Y/%m/%d %H:%M:%S",
        "%d/%m/%Y %H:%M:%S",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%dT%H:%M:%S.%f",
        "%Y-%m-%d",
        "%Y/%m/%d",
    )

    for fmt in formats:
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue

    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


def _normalise_value(entry: Mapping[str, object], *keys: str) -> str:
    for key in keys:
        if key not in entry:
            continue
        value = entry.get(key)
        if value is None:
            continue
        if isinstance(value, (int, float)):
            return str(value)
        text = str(value).strip()
        if text:
            return text
    return ""


def _parse_timestamp(entry: Mapping[str, object]) -> Optional[datetime]:
    direct_value = _normalise_value(entry, "datetime", "timestamp", "eventtime")
    if direct_value:
        direct_dt = _parse_datetime_value(direct_value)
        if direct_dt:
            return direct_dt

    date_value = _normalise_value(entry, "date", "logdate")
    time_value = _normalise_value(entry, "time", "logtime")
    if date_value or time_value:
        combined = " ".join(part for part in (date_value, time_value) if part)
        combined_dt = _parse_datetime_value(combined)
        if combined_dt:
            return combined_dt

    epoch_value = _normalise_value(entry, "itime", "epoch", "eventtime_epoch")
    if epoch_value:
        try:
            return datetime.fromtimestamp(float(epoch_value))
        except (ValueError, OSError):
            return None
    return None


def _is_threat_entry(entry: Mapping[str, object]) -> bool:
    action = _normalise_value(entry, "action", "event", "event_action", "status").lower()
    if action and (action in _THREAT_ACTIONS or action.startswith("deny")):
        return True

    score_text = _normalise_value(entry, "crscore", "threatscore", "score")
    if score_text:
        try:
            if float(score_text) > 0:
                return True
        except ValueError:
            pass

    is_attack = _normalise_value(entry, "is_attack", "attack").lower()
    if is_attack in {"1", "true", "yes"}:
        return True

    level = _normalise_value(entry, "level", "severity", "threat_level").lower()
    if level in _THREAT_LEVELS:
        return True

    return False


def _update_stats_with_entry(entry: Mapping[str, object], stats: Dict[str, object]) -> None:
    stats["processed"] = int(stats.get("processed", 0)) + 1

    source = _normalise_value(entry, "srcip", "source_ip", "src", "client_ip")
    if source:
        stats.setdefault("sources", set()).add(source)

    destination = _normalise_value(entry, "dstip", "destination_ip", "dst", "server_ip")
    if destination:
        stats.setdefault("destinations", set()).add(destination)

    if _is_threat_entry(entry):
        stats["threats"] = int(stats.get("threats", 0)) + 1

    timestamp = _parse_timestamp(entry)
    if timestamp:
        last_timestamp = stats.get("last_timestamp")
        if last_timestamp is None or timestamp > last_timestamp:
            stats["last_timestamp"] = timestamp


def _parse_text_line(line: str) -> Mapping[str, object]:
    line = line.strip()
    if not line:
        return {}

    if line.startswith("{") and line.endswith("}"):
        try:
            payload = json.loads(line)
            if isinstance(payload, dict):
                return payload
        except json.JSONDecodeError:
            pass

    if fortinet_parse_log_line is not None:
        parsed = fortinet_parse_log_line(line)
        if parsed:
            return {k: v for k, v in parsed.items() if k != "raw_line"}

    matches = _KV_FALLBACK_PATTERN.findall(line)
    if matches:
        return {key.lower(): value.strip('"\'') for key, value in matches}

    return {}


def _consume_csv_file(path: Path, stats: Dict[str, object]) -> None:
    with path.open("r", encoding="utf-8", errors="ignore") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            if not row:
                continue
            _update_stats_with_entry(row, stats)
            if int(stats.get("processed", 0)) >= _LOG_SAMPLE_LIMIT:
                return


def _consume_text_file(path: Path, stats: Dict[str, object]) -> None:
    with path.open("r", encoding="utf-8", errors="ignore") as handle:
        for line in handle:
            if int(stats.get("processed", 0)) >= _LOG_SAMPLE_LIMIT:
                break
            entry = _parse_text_line(line)
            if entry:
                _update_stats_with_entry(entry, stats)


def _collect_log_statistics() -> tuple[Optional[Dict[str, object]], Dict[str, list[str]]]:
    metadata: Dict[str, list[str]] = {
        "available_paths": [],
        "missing_paths": [],
        "files_used": [],
        "errors": [],
    }

    settings = _load_log_settings()
    files = _iter_recent_log_files(settings, metadata)

    stats: Dict[str, object] = {
        "processed": 0,
        "threats": 0,
        "sources": set(),
        "destinations": set(),
        "last_timestamp": None,
    }

    for path in files:
        try:
            if path.suffix.lower() == ".csv":
                _consume_csv_file(path, stats)
            else:
                _consume_text_file(path, stats)
            metadata["files_used"].append(str(path))
        except Exception as exc:  # pragma: no cover
            metadata["errors"].append(f"{path.name}: {exc}")
        if int(stats.get("processed", 0)) >= _LOG_SAMPLE_LIMIT:
            break

    processed = int(stats.get("processed", 0))
    if processed == 0:
        return None, metadata

    summary = {
        "active_connections": len(stats.get("sources", set())),
        "processed_logs": processed,
        "threat_detections": int(stats.get("threats", 0)),
        "last_activity": stats.get("last_timestamp"),
    }
    return summary, metadata


def _format_number(value: int) -> str:
    return f"{value:,}"


def _format_delta(current: int, previous: Optional[int]) -> Optional[str]:
    if previous is None:
        return None
    diff = current - previous
    if diff == 0:
        return "0"
    sign = "+" if diff > 0 else ""
    return f"{sign}{diff:,}"


def _render_sidebar() -> str:
    """渲染增強版側邊欄，提供品牌選擇、快速控制與即時統計。"""
    options = list(BRAND_RENDERERS.keys())
    st.session_state.setdefault("selected_brand", options[0])

    with st.sidebar:
        st.markdown(
            """
            <div class="sidebar-heading">
                <div class="sidebar-eyebrow">UNIFIED THREAT ANALYTICS</div>
                <div class="sidebar-title">🛡️ D-FLARE</div>
                <p class="sidebar-tagline">跨品牌安全控制中心</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        brand_configs = {
            "Fortinet": {
                "icon": "🛡️",
                "desc": "完整的威脅防護與 AI 推論解決方案",
            },
            "Cisco": {
                "icon": "📡",
                "desc": "專注 ASA 日誌擷取與跨平台通知",
            },
        }

        selected_brand = st.radio(
            "選擇安全平台",
            options,
            format_func=lambda key: f"{brand_configs.get(key, {}).get('icon', '🔧')} {key}",
            key="selected_brand",
            label_visibility="collapsed",
        )

        brand_summary = BRAND_DESCRIPTIONS.get(selected_brand) or brand_configs.get(selected_brand, {}).get("desc", "")
        if brand_summary:
            st.markdown(
                f"<div class='sidebar-note'>{html.escape(brand_summary)}</div>",
                unsafe_allow_html=True,
            )

        st.divider()

        st.markdown(
            "<div class='sidebar-eyebrow'>⚡ 快速控制</div>",
            unsafe_allow_html=True,
        )

        show_dashboard = st.checkbox("顯示系統儀表板", key="show_dashboard")
        show_settings = st.checkbox("顯示系統設定面板", key="show_settings")

        theme_key = st.session_state.get("ui_theme_choice", theme_controller.get_current_theme())
        theme_label = theme_controller.THEME_DISPLAY_NAMES.get(theme_key, theme_key.title())
        status_note = (
            f"📊 儀表板：{'🟢 啟用' if show_dashboard else '⚪ 關閉'} · "
            f"⚙️ 設定：{'🟢 顯示' if show_settings else '⚪ 隱藏'} · "
            f"🎨 主題：{theme_label}"
        )
        st.markdown(f"<div class='sidebar-note'>{status_note}</div>", unsafe_allow_html=True)

        metrics, metadata = _collect_log_statistics()
        previous_metrics = st.session_state.get("log_sidebar_metrics_prev")
        prev_metrics = previous_metrics if isinstance(previous_metrics, dict) else None

        if metrics:
            st.session_state["log_sidebar_metrics_prev"] = metrics.copy()

        if show_settings:
            with st.expander("🛠️ 系統設定", expanded=True):
                st.write("**🔔 通知設定**")
                st.checkbox("啟用 Discord 通知", key="discord_notify")
                st.checkbox("啟用 Slack 通知", key="slack_notify")

                st.write("**🎨 介面設定**")
                theme_options = list(theme_controller.THEME_DISPLAY_NAMES.keys())
                theme_index = theme_options.index(theme_key) if theme_key in theme_options else 0
                selected_theme = st.selectbox(
                    "主題選擇",
                    theme_options,
                    index=theme_index,
                    format_func=lambda key: f"{theme_controller.THEME_CONFIGS[key]['icon']} {theme_controller.THEME_DISPLAY_NAMES[key]}",
                    key="ui_theme_choice",
                )
                if selected_theme != theme_controller.get_current_theme():
                    theme_controller.switch_theme(selected_theme)

                st.write("**🔍 日誌設定**")
                st.number_input(
                    "日誌保存天數",
                    min_value=1,
                    max_value=365,
                    value=st.session_state.get("log_retention", 30),
                    key="log_retention",
                )
                if st.button("💾 儲存所有設定", key="save_sidebar_settings"):
                    st.success("✅ 設定已儲存並套用")

        if show_dashboard:
            with st.expander("📊 系統儀表板", expanded=True):
                if metrics:
                    active_delta = _format_delta(
                        metrics["active_connections"],
                        prev_metrics.get("active_connections") if prev_metrics else None,
                    )
                    processed_delta = _format_delta(
                        metrics["processed_logs"],
                        prev_metrics.get("processed_logs") if prev_metrics else None,
                    )
                    threat_delta = _format_delta(
                        metrics["threat_detections"],
                        prev_metrics.get("threat_detections") if prev_metrics else None,
                    )

                    col_d1, col_d2, col_d3 = st.columns(3)
                    with col_d1:
                        st.metric(
                            "活躍連線",
                            _format_number(metrics["active_connections"]),
                            delta=active_delta,
                        )
                    with col_d2:
                        st.metric(
                            "處理日誌",
                            _format_number(metrics["processed_logs"]),
                            delta=processed_delta,
                        )
                    with col_d3:
                        st.metric(
                            "威脅檢測",
                            _format_number(metrics["threat_detections"]),
                            delta=threat_delta,
                        )

                    last_activity = metrics.get("last_activity")
                    if isinstance(last_activity, datetime):
                        st.caption(f"最近資料時間：{last_activity.strftime('%Y-%m-%d %H:%M:%S')}")

                    files_used = metadata.get("files_used", [])
                    if files_used:
                        filenames = ", ".join(Path(path).name for path in files_used)
                        st.caption(f"統計來源：{filenames}")

                    if metadata.get("errors"):
                        st.warning("資料分析時發生異常：" + "、".join(metadata["errors"]))
                    elif metadata.get("missing_paths"):
                        st.caption("尚未偵測到路徑：" + "、".join(metadata["missing_paths"]))
                else:
                    st.info("尚未偵測到符合設定的日誌資料，請確認 logfetcher 設定或等待新資料。")
                    if metadata.get("missing_paths"):
                        st.caption("缺少路徑：" + "、".join(metadata["missing_paths"]))

        st.markdown(
            """
            <div style="
                background: var(--app-surface-muted);
                border: 1px solid var(--muted-border);
                border-radius: 12px;
                padding: 0.9rem 1rem;
                margin-top: 2rem;
                font-size: calc(var(--font-caption) + 1px);
            ">
                <div style="color: var(--sidebar-muted); margin-bottom: 0.35rem;">📡 系統狀態</div>
                <div style="color: var(--sidebar-text); font-weight: 600;">🟢 服務運行中</div>
                <div style="color: var(--sidebar-muted); margin-top: 0.35rem;">版本: v2.1.0</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    return st.session_state.selected_brand


def _chunked(seq: Sequence[_T], size: int) -> Iterator[Sequence[_T]]:
    for idx in range(0, len(seq), size):
        yield seq[idx : idx + size]


def _render_brand_highlights(brand: str) -> bool:
    highlights = BRAND_HIGHLIGHTS.get(brand)
    if not highlights:
        return False

    st.markdown('<div class="feature-cards-container">', unsafe_allow_html=True)

    brand_card_class = "feature-card"
    if brand == "Fortinet":
        brand_card_class = "feature-card fortinet-card"
    elif brand == "Cisco":
        brand_card_class = "feature-card cisco-card"

    for row in _chunked(highlights, 3):
        columns = st.columns(len(row))
        for column, (icon, title, desc) in zip(columns, row):
            variant = FEATURE_VARIANTS.get(title, "secondary")
            column.markdown(
                f"""
                <div class="{brand_card_class}" data-variant="{html.escape(variant)}">
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
