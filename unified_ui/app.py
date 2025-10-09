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

    # 條件載入模組，避免單一模組錯誤影響整個系統
    cisco_pages = None
    fortinet_pages = None
    
    try:
        from cisco_module import pages as cisco_pages  # type: ignore[import]
    except ImportError:
        # 靜默處理，避免顯示錯誤訊息
        cisco_pages = None
    except Exception:
        # 其他異常也靜默處理
        cisco_pages = None
    
    try:
        from fortinet_module import pages as fortinet_pages  # type: ignore[import]
    except ImportError as e:
        # 靜默處理，避免顯示錯誤訊息
        fortinet_pages = None
    except Exception as e:
        # 其他異常也靜默處理
        fortinet_pages = None
else:
    # 相對路徑版本，同樣使用條件載入
    cisco_pages = None
    fortinet_pages = None
    
    try:
        from .cisco_module import pages as cisco_pages
    except ImportError as e:
        st.error(f"無法載入 Cisco 模組: {e}")
        cisco_pages = None
    
    try:
        from .fortinet_module import pages as fortinet_pages
    except ImportError as e:
        st.warning(f"無法載入 Fortinet 模組: {e}")
        fortinet_pages = None

try:
    st.set_page_config(
        page_title="D-FLARE Unified Dashboard", 
        page_icon="🛡️", 
        layout="wide",
        initial_sidebar_state="expanded"
    )
except StreamlitAPIException:
    pass

# 品牌渲染器映射字典 - 條件設定，只加入成功載入的模組
BRAND_RENDERERS = {}
if fortinet_pages:
    BRAND_RENDERERS["Fortinet"] = fortinet_pages.render
if cisco_pages:
    BRAND_RENDERERS["Cisco"] = cisco_pages.render

# 品牌描述字典 - 為每個品牌提供統一的功能描述，僅防火牆品牌不同
BRAND_DESCRIPTIONS = {
    "Fortinet": "統一威脅分析平台，支援 Fortinet 防火牆日誌處理、AI 模型訓練與推論、ETL 資料處理及多平台智慧通知系統。",
    "Cisco": "統一威脅分析平台，支援 Cisco ASA 防火牆日誌處理、AI 模型訓練與推論、ETL 資料處理及多平台智慧通知系統。",
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
        "contrast_start": "#38bdf8",  # Cisco 藍色
        "contrast_end": "#2563eb",
    },
    "Cisco": {
        "start": "#38bdf8",
        "end": "#2563eb",
        "shadow": "rgba(37, 99, 235, 0.45)",
        "icon": "📡",
        "eyebrow": "Cisco 安全平台",
        "contrast_start": "#f97316",  # Fortinet 橘色
        "contrast_end": "#ef4444",
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
        ("⚙️", "模型推論指引", "依步驟完成資料上傳、模型載入與結果檢視，降低操作門檻。"),
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

    # 增強主題樣式（僅 layout 增強，不覆蓋 Streamlit 主題顏色）
    st.markdown("""
        <style>
        /* === 側邊欄 layout 增強 === */
        section[data-testid="stSidebar"] {
            box-shadow: 4px 0 20px rgba(0, 0, 0, 0.3);
        }
        
        section[data-testid="stSidebar"] .stButton > button {
            border-radius: 10px !important;
            padding: 0.8rem !important;
            font-weight: 600 !important;
            transition: all 0.3s ease !important;
            width: 100% !important;
            text-align: left !important;
        }
        
        section[data-testid="stSidebar"] .stButton > button:hover {
            transform: translateX(5px) !important;
            box-shadow: 0 8px 25px
                color-mix(in srgb, var(--primary-color) 40%, transparent) !important;
        }
        
        /* === 主內容區域 layout === */
        .main .block-container {
            border-radius: 12px;
            padding: 2rem 3rem;
            margin-top: 1rem;
            max-width: none;
        }
        
        /* === 品牌英雄卡片 === */
        .brand-hero {
            border-radius: 20px;
            padding: 2.5rem;
            margin: 2rem 0;
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
            background: radial-gradient(
                circle,
                rgba(255,255,255,0.1) 0%,
                transparent 70%);
            border-radius: 50%;
        }
        
        /* === 功能卡片 === */
        .feature-card {
            border-radius: 16px;
            padding: 2rem;
            margin: 0.5rem 0;
            transition: all 0.3s ease;
            box-shadow: 0 8px 25px rgba(0, 0, 0, 0.1);
            position: relative;
            overflow: hidden;
            border: 1px solid rgba(99, 102, 241, 0.2);
        }
        
        .feature-card::before {
            content: "";
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 4px;
            background: linear-gradient(
                90deg,
                #ec4899,
                #8b5cf6,
                #3b82f6,
                #06b6d4);
        }
        
        .feature-card:hover {
            transform: translateY(-8px);
            box-shadow: 0 20px 50px rgba(99, 102, 241, 0.4),
                        0 0 40px rgba(139, 92, 246, 0.3);
            border-color: rgba(139, 92, 246, 0.5);
        }
        
        /* === Fortinet 品牌卡片樣式 === */
        .fortinet-card {
            border-color: rgba(249, 115, 22, 0.25);
        }
        
        .fortinet-card::before {
            background: linear-gradient(
                90deg,
                #f97316,
                #ef4444,
                #dc2626,
                #fb923c);
        }
        
        .fortinet-card:hover {
            box-shadow: 0 20px 50px rgba(249, 115, 22, 0.4),
                        0 0 40px rgba(239, 68, 68, 0.3);
            border-color: rgba(239, 68, 68, 0.6);
        }
        
        /* === Cisco 品牌卡片樣式 === */
        .cisco-card {
            border-color: rgba(56, 189, 248, 0.25);
        }
        
        .cisco-card::before {
            background: linear-gradient(
                90deg,
                #38bdf8,
                #3b82f6,
                #2563eb,
                #60a5fa);
        }
        
        .cisco-card:hover {
            box-shadow: 0 20px 50px rgba(56, 189, 248, 0.4),
                        0 0 40px rgba(59, 130, 246, 0.3);
            border-color: rgba(37, 99, 235, 0.6);
        }
        
        /* === 功能卡片內容樣式 === */
        .feature-card__icon {
            font-size: 2.5rem;
            margin-bottom: 1rem;
            text-align: center;
        }
        
        .feature-card__title {
            font-size: 1.5rem;
            font-weight: 700;
            margin: 1rem 0;
            text-align: center;
        }
        
        .feature-card__desc {
            font-size: 0.95rem;
            line-height: 1.6;
            opacity: 0.85;
            text-align: center;
        }
        
        /* === 按鈕樣式系統 v2.0 - 參考圖5漸層設計 === */
        
        /* 通用按鈕基礎 - 青藍科技漸層（現代安全監控配色） */
        .stButton > button,
        button[kind="primary"],
        button[kind="secondary"],
        button[data-testid="baseButton-primary"],
        button[data-testid="baseButton-secondary"] {
            /* 青藍漸層 - 科技專業風格 */
            background: linear-gradient(
                135deg,
                #06b6d4 0%,
                #0891b2 100%) !important;
            
            /* 青色邊框 */
            border: 2px solid #06b6d4 !important;
            border-radius: 14px !important;
            font-weight: 600 !important;
            padding: 0.75rem 2rem !important;
            
            /* 柔和青色光暈 */
            box-shadow: 
                0 0 25px rgba(6, 182, 212, 0.4),
                0 4px 12px rgba(0, 0, 0, 0.15),
                inset 0 1px 0 rgba(255, 255, 255, 0.15) !important;
            
            /* 白色文字 */
            color: white !important;
            text-shadow: 0 1px 2px rgba(0, 0, 0, 0.3) !important;
            
            transition: all 0.35s cubic-bezier(0.4, 0, 0.2, 1) !important;
            position: relative !important;
        }
        
        /* 按鈕懸停 - 增強光暈 */
        .stButton > button:hover,
        button[kind="primary"]:hover,
        button[kind="secondary"]:hover,
        button[data-testid="baseButton-primary"]:hover,
        button[data-testid="baseButton-secondary"]:hover {
            transform: translateY(-3px) scale(1.03) !important;
            
            /* 更強青色光暈 */
            box-shadow: 
                0 0 35px rgba(6, 182, 212, 0.6),
                0 8px 20px rgba(0, 0, 0, 0.2),
                inset 0 1px 0 rgba(255, 255, 255, 0.2) !important;
            
            /* 漸層變亮 */
            background: linear-gradient(
                135deg,
                #22d3ee 0%,
                #06b6d4 100%) !important;
            
            filter: brightness(1.15) !important;
        }
        
        /* 按鈕點擊效果 */
        .stButton > button:active,
        button[kind="primary"]:active,
        button[data-testid="baseButton-primary"]:active {
            transform: translateY(-1px) scale(0.99) !important;
            box-shadow: 
                0 0 18px rgba(6, 182, 212, 0.35),
                0 2px 8px rgba(0, 0, 0, 0.2),
                inset 0 2px 4px rgba(0, 0, 0, 0.15) !important;
        }
        
        /* Primary 按鈕 - 品牌色實心（橘色/藍色） */
        .stButton > button[kind="primary"],
        button[data-testid="baseButton-primary"] {
            /* 品牌色漸層實心背景 */
            background: linear-gradient(
                135deg,
                var(--primary-color) 0%,
                color-mix(in srgb, var(--primary-color) 75%, #dc2626) 100%) !important;
            
            border: 2px solid var(--primary-color) !important;
            
            /* 更強的品牌色光暈 */
            box-shadow: 
                0 0 25px color-mix(in srgb, var(--primary-color) 45%, transparent),
                0 6px 16px rgba(0, 0, 0, 0.2),
                inset 0 1px 0 rgba(255, 255, 255, 0.15) !important;
            
            color: white !important;
            text-shadow: 0 2px 4px rgba(0, 0, 0, 0.3) !important;
        }
        
        .stButton > button[kind="primary"]:hover,
        button[data-testid="baseButton-primary"]:hover {
            box-shadow: 
                0 0 40px color-mix(in srgb, var(--primary-color) 60%, transparent),
                0 10px 25px rgba(0, 0, 0, 0.25),
                inset 0 1px 0 rgba(255, 255, 255, 0.2) !important;
        }
        
        /* Secondary 按鈕 - 保持青藍漸層 */
        .stButton > button[kind="secondary"],
        button[data-testid="baseButton-secondary"] {
            /* 保持預設的青藍漸層 */
        }
        
        /* === 確保文字顏色繼承 === */
        .stButton > button span,
        button[kind="primary"] span,
        button[kind="secondary"] span {
            color: inherit !important;
        }
        
        /* === 選擇框和輸入框 layout === */
        .stSelectbox > div > div,
        .stTextInput > div > div > input {
            border-radius: 8px !important;
        }
        
        /* === 標題樣式 === */
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
        
        /* === 隱藏部分預設元素 === */
        footer {
            visibility: hidden;
        }
        
        .stDeployButton {
            visibility: hidden;
        }
        
        /* === 自訂滾動條 === */
        ::-webkit-scrollbar {
            width: 10px;
        }
        
        ::-webkit-scrollbar-thumb {
            background: var(--primary-color);
            border-radius: 5px;
        }
        
        ::-webkit-scrollbar-thumb:hover {
            background: color-mix(in srgb, var(--primary-color) 85%, white);
        }
        }
        
        /* === 修復側邊欄摺疊按鈕 === */
        .stSidebarCollapsedControl {
            position: fixed !important;
            top: 0.5rem !important;
            left: 0.5rem !important;
            z-index: 999999 !important;
            border-radius: 8px !important;
            padding: 0.5rem !important;
            transition: all 0.3s ease !important;
            backdrop-filter: blur(10px) !important;
        }
        
        .stSidebarCollapsedControl:hover {
            transform: scale(1.1) !important;
        }
        
        /* 確保摺疊按鈕在所有狀態下都可見 */
        button[data-testid="collapsedControl"] {
            position: fixed !important;
            top: 0.5rem !important;
            left: 0.5rem !important;
            z-index: 999999 !important;
            border-radius: 8px !important;
            width: 2.5rem !important;
            height: 2.5rem !important;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
            backdrop-filter: blur(10px) !important;
            transition: all 0.3s ease !important;
        }
        
        button[data-testid="collapsedControl"]:hover {
            transform: scale(1.1) !important;
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
            --font-label: 16px;  #這是標籤的字體大小
            --font-body: 12.4px;  #這是主體的字體大小
            --font-caption: 10.8px;  #這是說明文字的字體大小
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

          /* 保留 header 可見性 */
          /* header, #MainMenu {
              display: none;
          } */          /* footer 已在上方設定隱藏 */        div[data-testid="stDecoration"] {
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
            font-size: var(--font-label) !important;   #這是側邊欄選單的字體大小 加上了!important確保被應用與優先於其他樣式設置
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

        /* Sidebar中的expander標題（功能目錄）特別放大 */
        div[data-testid="stSidebar"] div[data-testid="stExpander"] > details > summary {
            font-size: calc(var(--font-label) * 1.2) !important;
            font-weight: 700;
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
    """渲染增強版側邊欄，使用卡片式選單取代 radio button。"""
    options = list(BRAND_RENDERERS.keys())
    
    # 檢查是否有可用的品牌渲染器
    if not options:
        st.error("❌ 無法載入任何品牌模組，請檢查模組安裝是否正確。")
        st.stop()
    
    # 初始化會話狀態
    if "selected_brand" not in st.session_state:
        st.session_state.selected_brand = options[0]
    
    with st.sidebar:
        # 標題區域 - 修正版
        st.markdown(
            """
            <div style="text-align: center; margin-bottom: 2rem;">
                <h1 style="margin: 0; font-size: 1.8rem; font-weight: 800;">
                    🛡️ D-FLARE
                </h1>
                <div style="
                    width: 100%;
                    height: 3px;
                    background: linear-gradient(90deg, 
                        #f97316 0%,
                        #fb923c 50%,
                        #f97316 100%);
                    margin: 0.8rem auto;
                    border-radius: 2px;
                "></div>
                <p style="margin: 0.5rem 0; font-size: 0.85rem; letter-spacing: 1px; opacity: 0.7; text-transform: uppercase;">
                    UNIFIED THREAT ANALYTICS
                </p>
                <div style="
                    width: 40%;
                    height: 2px;
                    background: linear-gradient(90deg, 
                        transparent 0%,
                        #a855f7 50%,
                        transparent 100%);
                    margin: 0.8rem auto 0 auto;
                    border-radius: 2px;
                "></div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        
        # 品牌選擇區域 - 美觀圖標網格
        st.markdown(
            """
            <style>
            /* === 側邊欄品牌選擇按鈕 - 參考圖2舊版設計（更和諧配色） === */
            section[data-testid="stSidebar"] .stButton > button {
                border-radius: 14px !important;
                font-weight: 700 !important;
                padding: 1rem 1.5rem !important;
                font-size: 1.05rem !important;
                transition: all 0.35s cubic-bezier(0.4, 0, 0.2, 1) !important;
                position: relative !important;
            }
            
            /* 側邊欄 Primary 按鈕 - 選中狀態（橘色漸層） */
            section[data-testid="stSidebar"] .stButton > button[kind="primary"] {
                /* 橘色實心漸層 */
                background: linear-gradient(
                    135deg,
                    #f97316,
                    #ea580c) !important;
                border: 2px solid #f97316 !important;
                
                /* 柔和橘色光暈 */
                box-shadow:
                    0 6px 20px rgba(249, 115, 22, 0.4),
                    0 3px 8px rgba(0, 0, 0, 0.15),
                    inset 0 1px 0 rgba(255, 255, 255, 0.15) !important;
                
                color: white !important;
                text-shadow: 0 1px 3px rgba(0, 0, 0, 0.3) !important;
            }
            
            section[data-testid="stSidebar"] .stButton > button[kind="primary"]:hover {
                transform: translateY(-2px) scale(1.02) !important;
                
                /* Hover 光暈適度增強 */
                box-shadow:
                    0 8px 25px rgba(249, 115, 22, 0.5),
                    0 4px 10px rgba(0, 0, 0, 0.2),
                    inset 0 1px 0 rgba(255, 255, 255, 0.2) !important;
                
                filter: brightness(1.1) !important;
            }
            
            /* 側邊欄 Secondary 按鈕 - 未選中狀態（參考圖2 Cisco 未選中） */
            section[data-testid="stSidebar"] .stButton > button[kind="secondary"] {
                /* 深色不透明背景 - 類似圖2 */
                background: linear-gradient(
                    135deg, 
                    rgba(45, 50, 60, 0.9), 
                    rgba(35, 40, 50, 0.85)) !important;
                border: 2px solid rgba(255, 255, 255, 0.12) !important;
                color: rgba(255, 255, 255, 0.8) !important;
                box-shadow: 
                    0 2px 8px rgba(0, 0, 0, 0.2),
                    inset 0 1px 0 rgba(255, 255, 255, 0.05) !important;
            }
            
            section[data-testid="stSidebar"] .stButton > button[kind="secondary"]:hover {
                background: linear-gradient(
                    135deg, 
                    rgba(55, 60, 70, 0.95), 
                    rgba(45, 50, 60, 0.9)) !important;
                border: 2px solid rgba(255, 255, 255, 0.2) !important;
                color: white !important;
                box-shadow: 
                    0 4px 12px rgba(0, 0, 0, 0.25),
                    inset 0 1px 0 rgba(255, 255, 255, 0.08) !important;
                transform: translateY(-2px) scale(1.02) !important;
            }
            
            /* === 目錄按鈕特別設計（expander 內的按鈕）- 半透明漸層設計 === */
            details[open] .stButton > button,
            div[data-testid="stExpander"] .stButton > button {
                /* 更大的圓角 */
                border-radius: 14px !important;
                padding: 1rem 1.5rem !important;
                font-size: 0.95rem !important;
                font-weight: 600 !important;
                
                /* 半透明青藍漸層背景 */
                background: linear-gradient(
                    to right,
                    rgba(6, 182, 212, 0.15) 0%,
                    rgba(8, 145, 178, 0.12) 100%) !important;
                
                /* 品牌色左側邊條 */
                border-left: 4px solid var(--primary-color) !important;
                border-top: 1px solid rgba(255, 255, 255, 0.15) !important;
                border-right: 1px solid rgba(255, 255, 255, 0.15) !important;
                border-bottom: 1px solid rgba(255, 255, 255, 0.15) !important;
                
                /* 柔和光暈 */
                box-shadow: 
                    0 0 20px color-mix(in srgb, var(--primary-color) 15%, transparent),
                    0 4px 12px rgba(0, 0, 0, 0.2) !important;
                
                /* 白色文字 - 高對比度 */
                color: white !important;
                text-align: left !important;
                text-shadow: 0 1px 2px rgba(0, 0, 0, 0.3) !important;
            }
            
            details[open] .stButton > button:hover,
            div[data-testid="stExpander"] .stButton > button:hover {
                /* Hover 背景加強半透明青藍漸層 */
                background: linear-gradient(
                    to right,
                    rgba(6, 182, 212, 0.25) 0%,
                    rgba(8, 145, 178, 0.20) 100%) !important;
                
                border-left: 4px solid color-mix(in srgb, var(--primary-color) 120%, white) !important;
                border-top: 1px solid rgba(255, 255, 255, 0.25) !important;
                border-right: 1px solid rgba(255, 255, 255, 0.25) !important;
                border-bottom: 1px solid rgba(255, 255, 255, 0.25) !important;
                
                /* 更強的光暈 */
                box-shadow: 
                    0 0 30px color-mix(in srgb, var(--primary-color) 30%, transparent),
                    0 6px 18px rgba(0, 0, 0, 0.25) !important;
                
                transform: translateX(4px) !important;
            }
            </style>
            <h3 style="font-size: 1rem; margin-bottom: 1rem; font-weight: 600;">
                ✨ 選擇安全平台
            </h3>
            """,
            unsafe_allow_html=True,
        )

        # 創建品牌配置 - 包含品牌特定的漸層配色
        brand_configs = {
            "Fortinet": {
                "icon": "🛡️",
                "desc": "智慧威脅分析與 Fortinet 防火牆日誌處理平台",
                "gradient": "linear-gradient(135deg, #f97316, #ef4444)",
                "shadow": "rgba(239, 68, 68, 0.3)"
            },
            "Cisco": {
                "icon": "📡",
                "desc": "智慧威脅分析與 Cisco ASA 防火牆日誌處理平台",
                "gradient": "linear-gradient(135deg, #38bdf8, #2563eb)",
                "shadow": "rgba(37, 99, 235, 0.3)"
            }
        }

        selected_brand = st.session_state.selected_brand

        # 簡潔美觀的品牌選擇按鈕
        for brand in options:
            config = brand_configs.get(brand, {
                "icon": "🔧", 
                "desc": "專業安全解決方案",
                "gradient": "linear-gradient(135deg, #6b7280, #4b5563)",
                "shadow": "rgba(75, 85, 99, 0.3)"
            })
            is_selected = brand == selected_brand
            
            # 使用原生 Streamlit 按鈕，根據選中狀態調整樣式
            button_type = "primary" if is_selected else "secondary"
            
            if st.button(
                f"{config['icon']} **{brand}**",
                key=f"brand_{brand}",
                use_container_width=True,
                type=button_type,
                help=config['desc']
            ):
                st.session_state.selected_brand = brand
                st.rerun()        # 狀態顯示
        current_config = brand_configs.get(selected_brand, {
            "icon": "🔧",
            "gradient": "linear-gradient(135deg, #6b7280, #4b5563)",
            "shadow": "rgba(75, 85, 99, 0.3)"
        })
        st.markdown(
            f"""
            <div style="
                background: {current_config['gradient']};
                border-radius: 10px;
                padding: 1rem;
                margin: 1.5rem 0;
                text-align: center;
                box-shadow: 0 6px 20px {current_config['shadow']};
            ">
                <div style="color: white; font-weight: 600; font-size: 0.9rem;">
                    {current_config['icon']} 當前平台: {selected_brand}
                </div>
                <div style="color: rgba(255, 255, 255, 0.9); font-size: 0.8rem; margin-top: 0.5rem;">
                    {brand_configs.get(selected_brand, {"desc": ""})['desc']}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    
    return st.session_state.selected_brand


def _render_system_status() -> None:
    """渲染系統狀態區塊到側邊欄最底部。"""
    with st.sidebar:
        # 系統資訊 (移到最底部)
        st.markdown(
            """
            <div style="
                border: 2px solid #22c55e;
                border-radius: 8px;
                padding: 0.8rem;
                margin-top: 2rem;
                font-size: 0.8rem;
                background: rgba(34, 197, 94, 0.1);
            ">
                <div style="margin-bottom: 0.5rem; opacity: 0.7;">📡 系統狀態</div>
                <div style="color: #22c55e; font-weight: 600;">🟢 所有服務運行中</div>
                <div style="margin-top: 0.3rem; opacity: 0.7;">版本: v2.1.0</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


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

    # Add hero card styles - 參考圖3添加漸層線條
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
            margin: 0.35rem 0 0 0;
            padding-bottom: 1.2rem;
            font-weight: 700;
            letter-spacing: 0.01em;
            position: relative;
        }
        
        /* 品牌色漸層線條 - 在大標與小標之間 */
        /* 使用相反品牌色：Fortinet 用 Cisco 藍，Cisco 用 Fortinet 橘 */
        .brand-hero h1::after {
            content: "";
            position: absolute;
            bottom: 0;
            left: 0;
            right: 0;
            height: 3px;
            background: linear-gradient(90deg, 
                transparent 0%,
                var(--contrast-start) 15%,
                var(--contrast-end) 85%,
                transparent 100%);
            opacity: 0.85;
        }
        
        .brand-hero p {
            color: rgba(255, 255, 255, 0.9);
            font-size: 1.12rem;
            margin: 1rem 0 0 0;
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
        <div class="brand-hero" style="--accent-start: {theme['start']}; --accent-end: {theme['end']}; --accent-shadow: {theme['shadow']}; --contrast-start: {theme['contrast_start']}; --contrast-end: {theme['contrast_end']}">
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
        
        # 最後渲染系統狀態區塊，確保出現在功能目錄之後
        _render_system_status()


if __name__ == "__main__":
    main()
