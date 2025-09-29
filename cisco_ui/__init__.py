"""Router for Cisco branded pages with unified navigation."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Dict, List

import streamlit as st

from theme_controller import get_button_style

from . import data_cleaning, log_monitor, model_inference, notifications, visualization


@dataclass(frozen=True)
class PageDefinition:
    key: str
    label: str
    icon: str
    description: str
    render: Callable[[], None]
    actions: List[Dict[str, str]]


PAGES: List[PageDefinition] = [
    PageDefinition(
        key="log_monitor",
        label="Log 擷取",
        icon="📡",
        description="監控 ASA log 並自動觸發清洗、推論與通知。",
        render=log_monitor.render,
        actions=[
            {"label": "開啟儀表板", "type": "navigate"},
            {"label": "開始監控", "type": "command", "command": "log_monitor:start"},
            {"label": "停止監控", "type": "command", "command": "log_monitor:stop"},
            {"label": "手動掃描", "type": "command", "command": "log_monitor:scan"},
        ],
    ),
    PageDefinition(
        key="data_cleaning",
        label="資料清理",
        icon="🧹",
        description="維護清洗資料夾並設定排程清理策略。",
        render=data_cleaning.render,
        actions=[
            {"label": "開啟頁面", "type": "navigate"},
            {"label": "啟動排程", "type": "command", "command": "data_cleaning:start_auto"},
            {"label": "停止排程", "type": "command", "command": "data_cleaning:stop_auto"},
            {"label": "立即清理", "type": "command", "command": "data_cleaning:manual"},
            {"label": "批次清空", "type": "command", "command": "data_cleaning:purge"},
        ],
    ),
    PageDefinition(
        key="model_inference",
        label="模型推論",
        icon="🤖",
        description="手動載入模型與 log 檔案，執行 Pipeline。",
        render=model_inference.render,
        actions=[
            {"label": "開啟頁面", "type": "navigate"},
            {"label": "使用最新檔案", "type": "command", "command": "model_inference:use_recent"},
            {"label": "清空上傳", "type": "command", "command": "model_inference:clear_uploads"},
            {"label": "同步輸出路徑", "type": "command", "command": "model_inference:focus_output"},
        ],
    ),
    PageDefinition(
        key="notifications",
        label="通知模組",
        icon="🔔",
        description="整合 Gemini、LINE 與 Discord 的推播設定。",
        render=notifications.render,
        actions=[
            {"label": "開啟頁面", "type": "navigate"},
            {"label": "儲存設定", "type": "command", "command": "notifications:save"},
            {"label": "測試 LINE", "type": "command", "command": "notifications:test_line"},
            {"label": "測試 Discord", "type": "command", "command": "notifications:test_discord"},
        ],
    ),
    PageDefinition(
        key="visualization",
        label="圖表預覽",
        icon="📊",
        description="檢視最近的分析圖表並同步輸出資料夾。",
        render=visualization.render,
        actions=[
            {"label": "開啟頁面", "type": "navigate"},
            {"label": "同步路徑", "type": "command", "command": "visualization:sync"},
            {"label": "切換圖表", "type": "command", "command": "visualization:cycle"},
        ],
    ),
]


def _ensure_state() -> None:
    st.session_state.setdefault("cisco_current_page", PAGES[0].key)
    st.session_state.setdefault("cisco_pending_commands", [])


def _handle_action(page: PageDefinition, action: Dict[str, str]) -> None:
    st.session_state["cisco_current_page"] = page.key
    if action.get("type") == "command":
        queue = st.session_state.setdefault("cisco_pending_commands", [])
        queue.append({"page": page.key, "command": action["command"]})


def _next_command(page_key: str) -> str | None:
    queue = st.session_state.get("cisco_pending_commands", [])
    command = None
    remaining = []
    for item in queue:
        if command is None and item["page"] == page_key:
            command = item["command"]
        else:
            remaining.append(item)
    st.session_state["cisco_pending_commands"] = remaining
    return command


def _render_sidebar() -> None:
    with st.sidebar:
        st.header("📂 功能目錄")
        st.markdown(get_button_style(), unsafe_allow_html=True)
        for page in PAGES:
            st.markdown(
                f"<div class='sidebar-feature__title'>{page.icon} {page.label}</div>",
                unsafe_allow_html=True,
            )
            if page.description:
                st.markdown(
                    f"<div class='sidebar-feature__note'>{page.description}</div>",
                    unsafe_allow_html=True,
                )
            actions = page.actions
            cols_per_row = 2
            for start in range(0, len(actions), cols_per_row):
                row = actions[start : start + cols_per_row]
                cols = st.columns(len(row))
                for col, action in zip(cols, row):
                    if col.button(
                        action["label"],
                        key=f"cisco_sidebar_{page.key}_{action['label']}_{start}",
                        use_container_width=True,
                    ):
                        _handle_action(page, action)
        _render_flash_messages()


def _render_flash_messages() -> None:
    messages = st.session_state.pop("cisco_flash_messages", [])
    if not messages:
        return
    st.markdown("---")
    for msg in messages:
        st.caption(msg)


def _render_active_page() -> None:
    key = st.session_state.get("cisco_current_page", PAGES[0].key)
    page_lookup = {page.key: page for page in PAGES}
    page = page_lookup.get(key, PAGES[0])
    command = _next_command(page.key)
    if command:
        st.session_state[f"cisco_command_{page.key}"] = command
    page.render()


def render() -> None:
    """Entry point used by :mod:`ui_app` for Cisco brand rendering."""

    _ensure_state()
    _render_sidebar()
    _render_active_page()
