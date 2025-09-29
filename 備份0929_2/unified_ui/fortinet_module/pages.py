"""Fortinet 介面在統一平台的渲染邏輯。"""
from __future__ import annotations

import html

import streamlit as st

try:
    from streamlit_option_menu import option_menu
except ModuleNotFoundError:  # pragma: no cover
    option_menu = None

from Forti_ui_app_bundle.ui_pages import (
    folder_monitor_ui,
    gpu_etl_ui,
    inference_ui,
    notifier_app,
    training_ui,
    visualization_ui,
)

PAGES = {
    "Training Pipeline": training_ui.app,
    "GPU ETL Pipeline": gpu_etl_ui.app,
    "Model Inference": inference_ui.app,
    "Folder Monitor": folder_monitor_ui.app,
    "Visualization": visualization_ui.app,
    "Notifications": notifier_app.app,
}
PAGE_ICON_EMOJI = {
    "Training Pipeline": "⚙️",
    "GPU ETL Pipeline": "🚀",
    "Model Inference": "🧠",
    "Folder Monitor": "📂",
    "Visualization": "📊",
    "Notifications": "🔔",
}

PAGE_ICONS = {
    "Training Pipeline": "gear",
    "GPU ETL Pipeline": "speedometer2",
    "Model Inference": "cpu",
    "Folder Monitor": "folder",
    "Visualization": "bar-chart",
    "Notifications": "bell",
}
PAGE_DESCRIPTIONS = {
    "Training Pipeline": "設定訓練流程與參數。",
    "GPU ETL Pipeline": "啟動 GPU 加速的 ETL 任務。",
    "Model Inference": "使用已訓練模型進行推論。",
    "Folder Monitor": "監控資料夾並自動清洗檔案。",
    "Visualization": "瀏覽數據可視化結果。",
    "Notifications": "管理通知與 Gemini 建議。",
}

_SIDEBAR_STYLE_FLAG = "_fortinet_sidebar_styles"


def _ensure_sidebar_styles() -> None:
    if st.session_state.get(_SIDEBAR_STYLE_FLAG):
        return

    st.markdown(
        """
        <style>
        .sidebar-section-heading {
            display: flex;
            align-items: center;
            gap: 0.6rem;
            font-weight: 700;
            font-size: calc(var(--font-label) + 0.2px);
            margin: 1.4rem 0 0.8rem;
            color: var(--sidebar-text);
        }
        .sidebar-section-heading .bi {
            font-size: 1rem;
            color: var(--sidebar-icon);
        }
        .sidebar-segmented {
            padding: 0.3rem;
            border-radius: 1.05rem;
            background: color-mix(in srgb, var(--sidebar-bg) 92%, var(--app-surface) 8%);
            border: 1px solid var(--muted-border);
            box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.04);
        }
        .sidebar-segmented div[data-baseweb="segmented-control"] {
            background: transparent;
            border-radius: inherit;
        }
        .sidebar-segmented div[data-baseweb="segmented-control"] > div {
            display: flex;
            flex-direction: column;
            gap: 0.45rem;
        }
        .sidebar-segmented div[data-baseweb="segmented-control"] [role="radio"] {
            border-radius: 0.9rem;
            padding: 0.65rem 0.95rem;
            border: 1px solid transparent;
            background: transparent;
            font-weight: 600;
            color: var(--sidebar-text);
            display: flex;
            align-items: center;
            gap: 0.55rem;
            transition: all 0.2s ease;
        }
        .sidebar-segmented div[data-baseweb="segmented-control"] [role="radio"]:hover {
            border-color: color-mix(in srgb, var(--primary) 32%, transparent);
            background: color-mix(in srgb, var(--primary) 12%, transparent);
        }
        .sidebar-segmented div[data-baseweb="segmented-control"] [role="radio"][aria-checked="true"] {
            background: linear-gradient(135deg, var(--primary), var(--primary-hover));
            color: var(--text-on-primary);
            border-color: transparent;
            box-shadow: var(--hover-glow);
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
    st.session_state[_SIDEBAR_STYLE_FLAG] = True


def _render_navigation(page_keys: list[str]) -> str:
    _ensure_sidebar_styles()

    st.markdown(
        """
        <div class="sidebar-section-heading">
            <i class="bi bi-grid-1x2-fill"></i>
            <span>功能目錄</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    default_page = st.session_state.get("fortinet_active_page", page_keys[0])
    default_index = page_keys.index(default_page) if default_page in page_keys else 0

    if option_menu:
        st.markdown("<div class='sidebar-nav sidebar-nav--fortinet'>", unsafe_allow_html=True)
        selection = option_menu(
            None,
            page_keys,
            icons=[PAGE_ICONS[name] for name in page_keys],
            menu_icon="grid-1x2",
            default_index=default_index,
            key="fortinet_sidebar_menu",
            styles={
                "container": {"padding": "0", "background-color": "transparent"},
                "icon": {"color": "var(--sidebar-icon)", "font-size": "18px"},
                "nav-link": {
                    "color": "var(--sidebar-text)",
                    "font-size": "13px",
                    "text-align": "left",
                    "margin": "0px",
                    "--hover-color": "var(--sidebar-button-hover)",
                    "border-radius": "12px",
                    "padding": "0.7rem 0.95rem",
                },
                "nav-link-selected": {
                    "background-color": "var(--primary)",
                    "color": "var(--text-on-primary)",
                    "border-radius": "12px",
                    "box-shadow": "var(--hover-glow)",
                },
            },
        )
        st.markdown("</div>", unsafe_allow_html=True)
    else:
        glyphs = {name: PAGE_ICON_EMOJI.get(name, "•") for name in page_keys}
        st.markdown("<div class='sidebar-segmented'>", unsafe_allow_html=True)
        if hasattr(st, "segmented_control"):
            selection = st.segmented_control(
                "功能選單",
                options=page_keys,
                default=page_keys[default_index],
                format_func=lambda key: f"{glyphs[key]} {key}",
                key="fortinet_sidebar_menu",
                label_visibility="collapsed",
            )
        else:  # pragma: no cover - compatibility fallback
            selection = st.selectbox(
                "功能選單",
                page_keys,
                index=default_index,
                key="fortinet_sidebar_menu",
                label_visibility="collapsed",
            )
        st.markdown("</div>", unsafe_allow_html=True)

    st.session_state["fortinet_active_page"] = selection
    return selection


def render() -> None:
    # 維持舊狀態鍵以免其他模組存取時發生 KeyError。
    st.session_state.setdefault("fortinet_menu_collapse", False)

    page_keys = list(PAGES.keys())

    with st.sidebar:
        selection = _render_navigation(page_keys)

        description = PAGE_DESCRIPTIONS.get(selection, "")
        if description:
            st.markdown(
                f"<p class='sidebar-menu-description'>{html.escape(description)}</p>",
                unsafe_allow_html=True,
            )

    PAGES[selection]()
