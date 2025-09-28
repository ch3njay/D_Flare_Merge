"""Fortinet 介面在統一平台的渲染邏輯。"""
from __future__ import annotations

import html
from urllib.parse import urlencode

import streamlit as st

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

PAGE_EMOJIS = {
    "Training Pipeline": "🧪",
    "GPU ETL Pipeline": "⚙️",
    "Model Inference": "🤖",
    "Folder Monitor": "📁",
    "Visualization": "📊",
    "Notifications": "🔔",
}

QUERY_KEY = "fortinet_page"


def _format_label(label: str) -> str:
    icon_name = PAGE_ICONS.get(label)
    if icon_name and st.session_state.get("_unified_bootstrap_icons"):
        icon_markup = f"<i class='bi bi-{html.escape(icon_name)}'></i>"
    else:
        icon_markup = html.escape(PAGE_EMOJIS.get(label, "📄"))
    text = html.escape(label)
    return f"<span class='sidebar-nav__icon'>{icon_markup}</span><span class='sidebar-nav__label'>{text}</span>"


def _build_href(params: dict[str, list[str]]) -> str:
    return "?" + urlencode(params, doseq=True)


def _render_navigation(page_keys: list[str]) -> str:
    query_params = st.experimental_get_query_params()
    state_key = "fortinet_active_page"
    default_page = st.session_state.get(state_key, page_keys[0])
    current = query_params.get(QUERY_KEY, [default_page])[0]
    if current not in page_keys:
        current = page_keys[0]

    st.session_state[state_key] = current

    params_serializable = {
        key: value[0] if isinstance(value, list) and len(value) == 1 else value
        for key, value in query_params.items()
    }
    if params_serializable.get(QUERY_KEY) != current:
        params_serializable[QUERY_KEY] = current
        st.experimental_set_query_params(**params_serializable)

    nav_items: list[str] = []
    for label in page_keys:
        merged_params = {**query_params, QUERY_KEY: [label]}
        href = html.escape(_build_href(merged_params), quote=True)
        nav_items.append(
            f"<a class='sidebar-nav__item' data-active={'true' if label == current else 'false'} href='{href}'>{_format_label(label)}</a>"
        )

    st.markdown("<div class='sidebar-nav sidebar-nav--fortinet'>" + "".join(nav_items) + "</div>", unsafe_allow_html=True)
    return current


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
