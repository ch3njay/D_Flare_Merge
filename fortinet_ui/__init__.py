"""Router for Fortinet branded pages with the new navigation pattern."""
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
        label="資料夾監控",
        icon="📂",
        description="自動監控資料夾、執行 ETL 與推播告警。",
        render=log_monitor.render,
        actions=[
            {"label": "開啟頁面", "type": "navigate"},
            {"label": "使用目前目錄", "type": "command", "command": "log_monitor:use_cwd"},
            {"label": "清除暫存", "type": "command", "command": "log_monitor:clear_generated"},
        ],
    ),
    PageDefinition(
        key="data_cleaning",
        label="GPU ETL",
        icon="🚀",
        description="批次清理、映射與特徵工程的 GPU 加速流程。",
        render=data_cleaning.render,
        actions=[
            {"label": "開啟頁面", "type": "navigate"},
            {"label": "全選步驟", "type": "command", "command": "data_cleaning:select_all"},
            {"label": "全部停用", "type": "command", "command": "data_cleaning:clear_all"},
            {"label": "預設輸出名", "type": "command", "command": "data_cleaning:reset_output"},
        ],
    ),
    PageDefinition(
        key="model_inference",
        label="模型推論",
        icon="🧠",
        description="上傳資料與模型，執行二元/多元推論流程。",
        render=model_inference.render,
        actions=[
            {"label": "開啟頁面", "type": "navigate"},
            {"label": "清除上傳", "type": "command", "command": "model_inference:reset_inputs"},
            {"label": "清除結果", "type": "command", "command": "model_inference:clear_results"},
            {"label": "準備重新上傳", "type": "command", "command": "model_inference:prefill"},
        ],
    ),
    PageDefinition(
        key="notifications",
        label="通知模組",
        icon="🔔",
        description="設定 Discord / LINE / Gemini 告警並快速測試。",
        render=notifications.render,
        actions=[
            {"label": "開啟頁面", "type": "navigate"},
            {"label": "清空欄位", "type": "command", "command": "notifications:reset_fields"},
            {"label": "測試 Discord", "type": "command", "command": "notifications:test_discord"},
            {"label": "測試 LINE", "type": "command", "command": "notifications:test_line"},
            {"label": "預覽報表", "type": "command", "command": "notifications:preview"},
        ],
    ),
    PageDefinition(
        key="visualization",
        label="視覺化分析",
        icon="📈",
        description="檢視分析圖表並重置暫存資料。",
        render=visualization.render,
        actions=[
            {"label": "開啟頁面", "type": "navigate"},
            {"label": "清除暫存", "type": "command", "command": "visualization:clear_cache"},
            {"label": "提示最新報表", "type": "command", "command": "visualization:load_latest"},
        ],
    ),
]


def _ensure_state() -> None:
    st.session_state.setdefault("fortinet_current_page", PAGES[0].key)
    st.session_state.setdefault("fortinet_pending_commands", [])


def _handle_action(page: PageDefinition, action: Dict[str, str]) -> None:
    st.session_state["fortinet_current_page"] = page.key
    if action.get("type") == "command":
        queue = st.session_state.setdefault("fortinet_pending_commands", [])
        queue.append({"page": page.key, "command": action["command"]})


def _next_command(page_key: str) -> str | None:
    queue = st.session_state.get("fortinet_pending_commands", [])
    command = None
    remaining = []
    for item in queue:
        if command is None and item["page"] == page_key:
            command = item["command"]
        else:
            remaining.append(item)
    st.session_state["fortinet_pending_commands"] = remaining
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
            cols_per_row = 2
            for start in range(0, len(page.actions), cols_per_row):
                row = page.actions[start : start + cols_per_row]
                cols = st.columns(len(row))
                for col, action in zip(cols, row):
                    if col.button(
                        action["label"],
                        key=f"fortinet_sidebar_{page.key}_{action['label']}_{start}",
                        use_container_width=True,
                    ):
                        _handle_action(page, action)
        _render_flash_messages()


def _render_flash_messages() -> None:
    messages = st.session_state.pop("fortinet_flash_messages", [])
    if not messages:
        return
    st.markdown("---")
    for msg in messages:
        st.caption(msg)


def _render_active_page() -> None:
    key = st.session_state.get("fortinet_current_page", PAGES[0].key)
    page_lookup = {page.key: page for page in PAGES}
    page = page_lookup.get(key, PAGES[0])
    command = _next_command(page.key)
    if command:
        st.session_state[f"fortinet_command_{page.key}"] = command
    page.render()


def render() -> None:
    """Entry point invoked by ``ui_app`` to render Fortinet brand UI."""

    _ensure_state()
    _render_sidebar()
    _render_active_page()
