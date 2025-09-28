"""Cisco UI 通知模組。

此檔案整合 LINE、Discord 與 Gemini 推播相關的實作，
供 Streamlit 頁面與自動化流程呼叫，確保在獨立執行時
仍保留完整通知能力。
"""
from __future__ import annotations

import json
import os
from typing import Callable, Dict, List, Optional, Sequence, Tuple

import pandas as pd
import requests

from .utils_labels import NotificationMessage, SEVERITY_LABELS

USER_FILE = "line_users.txt"
LAST_USER_FILE = "last_user.txt"

_FIELD_ALIASES: Dict[str, Sequence[str]] = {
    "timestamp": [
        "Timestamp",
        "EventTime",
        "event_time",
        "LogTime",
        "time",
        "Time",
    ],
    "severity": ["Severity", "severity"],
    "source": ["SourceIP", "SrcIP", "Source", "source_ip"],
    "destination": ["DestinationIP", "DstIP", "Destination", "destination_ip"],
    "protocol": ["Protocol", "Proto", "protocol"],
    "port": ["DestinationPort", "DstPort", "Dst_Port", "port"],
    "description": ["Description", "Message", "LogMessage", "description"],
}

DEFAULT_CONVERGENCE = {"window_minutes": 10, "group_fields": ["source", "destination"]}

_GROUP_LABELS = {
    "source": "來源 IP",
    "destination": "目的 IP",
    "protocol": "通訊協定",
    "port": "目的 Port",
}


def _find_column(columns: Sequence[str], aliases: Sequence[str]) -> Optional[str]:
    """Find the first column that matches any alias (case-insensitive)."""

    lowered = {col.lower(): col for col in columns}
    for alias in aliases:
        key = alias.lower()
        if key in lowered:
            return lowered[key]
    return None


def _coerce_severity(value: object) -> Optional[int]:
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return None


def _normalize_convergence(config: Optional[Dict[str, object]]) -> Dict[str, object]:
    """Merge user-provided convergence options with defaults."""

    merged: Dict[str, object] = dict(DEFAULT_CONVERGENCE)
    if not config:
        return merged

    window = config.get("window_minutes")
    try:
        window_int = int(window) if window is not None else None
    except (TypeError, ValueError):
        window_int = None
    if window_int and window_int > 0:
        merged["window_minutes"] = window_int

    fields = config.get("group_fields")
    if isinstance(fields, (list, tuple)):
        valid = [
            str(field)
            for field in fields
            if str(field) in _GROUP_LABELS
        ]
        if valid:
            merged["group_fields"] = valid
    return merged


def _aggregate_high_risk_events(
    dataframe: pd.DataFrame,
    convergence: Optional[Dict[str, object]] = None,
) -> List[NotificationMessage]:
    """Group similar high-risk events to reduce duplicate notifications."""

    config = _normalize_convergence(convergence)
    severity_col = _find_column(dataframe.columns, _FIELD_ALIASES["severity"])
    desc_col = _find_column(dataframe.columns, _FIELD_ALIASES["description"])
    if not severity_col or not desc_col:
        return []

    work = dataframe.copy()
    work["_severity"] = work[severity_col].apply(_coerce_severity)
    work = work[work["_severity"].isin([1, 2, 3])]
    if work.empty:
        return []

    timestamp_col = _find_column(work.columns, _FIELD_ALIASES["timestamp"])
    if timestamp_col:
        work["_event_time"] = pd.to_datetime(work[timestamp_col], errors="coerce")
    else:
        work["_event_time"] = pd.NaT

    window = max(1, int(config.get("window_minutes", 10) or 10))
    if timestamp_col:
        work["_bucket"] = work["_event_time"].dt.floor(f"{window}min")
    else:
        work["_bucket"] = None

    group_columns: List[str] = []
    if timestamp_col:
        group_columns.append("_bucket")

    resolved_groups: List[Tuple[str, str]] = []
    for alias in config.get("group_fields", []):
        column = _find_column(work.columns, _FIELD_ALIASES.get(alias, []))
        if column:
            group_columns.append(column)
            resolved_groups.append((alias, column))

    if not group_columns:
        work["_row_id"] = range(len(work))
        group_columns.append("_row_id")

    source_col = _find_column(work.columns, _FIELD_ALIASES["source"])

    messages: List[NotificationMessage] = []
    for _, group in work.groupby(group_columns, dropna=False):
        severity_series = group["_severity"].dropna().astype(int)
        if severity_series.empty:
            continue
        severity = int(severity_series.iloc[0])
        source_value = ""
        if source_col and source_col in group:
            source_value = str(group[source_col].iloc[0])
            if source_value.lower() == "nan":
                source_value = ""

        desc_value = str(group[desc_col].iloc[0]) if desc_col in group else ""
        message = NotificationMessage(
            severity=severity,
            source_ip=source_value,
            description=desc_value,
            aggregated_count=len(group),
        )

        if desc_col in group:
            desc_series = group[desc_col].dropna()
            unique_descs = desc_series.astype(str).drop_duplicates().tolist()
            message.aggregated_descriptions = unique_descs

        if timestamp_col and "_event_time" in group:
            valid_times = group["_event_time"].dropna()
            if not valid_times.empty:
                start = valid_times.min()
                end = valid_times.max()
                message.time_window = (
                    start.strftime("%Y-%m-%d %H:%M"),
                    end.strftime("%Y-%m-%d %H:%M"),
                )

        match_parts = []
        for alias, column in resolved_groups:
            value = group[column].iloc[0] if column in group else ""
            if pd.isna(value):
                value = ""
            match_parts.append(f"{_GROUP_LABELS.get(alias, column)}：{value or '未提供'}")
            if alias == "source" and not message.source_ip:
                message.source_ip = str(value)

        message.match_signature = "、".join(match_parts)
        messages.append(message)

    return messages


# ---- LINE 與 Discord 推播工具 ----
def load_line_users(user_file: str = USER_FILE) -> List[str]:
    """讀取已註冊的 LINE 使用者 ID 清單。"""
    if not os.path.exists(user_file):
        return []
    with open(user_file, "r", encoding="utf-8") as handle:
        return [line.strip() for line in handle if line.strip()]


def push_line_message(access_token: str, user_id: str, message: str) -> bool:
    """直接呼叫 LINE API 傳送訊息給單一使用者。"""
    url = "https://api.line.me/v2/bot/message/push"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }
    payload = {"to": user_id, "messages": [{"type": "text", "text": message}]}
    response = requests.post(url, headers=headers, json=payload, timeout=20)
    return response.status_code == 200


def send_line_to_all(access_token: str, message: str, callback: Callable[[str], None] | None = None) -> bool:
    """對所有已註冊的 LINE 使用者送出通知。"""
    user_ids = load_line_users()
    if not access_token or len(access_token) < 10:
        if callback:
            callback("❌ 請正確設定 LINE Channel Access Token")
        return False
    if not user_ids:
        if callback:
            callback("❌ 尚無任何 LINE 使用者，請先掃碼加 Bot 並傳訊息！")
        return False

    success = False
    for user_id in user_ids:
        if push_line_message(access_token, user_id, message):
            success = True
            if callback:
                callback(f"✅ 已發送給 {user_id}")
        else:
            if callback:
                callback(f"❌ 傳送失敗 {user_id}")
    return success


def send_discord(webhook_url: str, message: str, callback: Callable[[str], None] | None = None) -> bool:
    """透過 Discord Webhook 推播文字訊息。"""
    if not webhook_url:
        return False
    try:
        response = requests.post(webhook_url, json={"content": message}, timeout=20)
    except Exception as exc:  # pragma: no cover - 連線錯誤不易測試
        if callback:
            callback(f"❌ Discord 發送例外：{exc}")
        return False
    if response.status_code in (200, 204):
        if callback:
            callback("✅ Discord 已發送")
        return True
    if callback:
        callback(f"❌ Discord 發送失敗，狀態碼：{response.status_code}")
    return False


def ask_gemini(message: NotificationMessage, gemini_api_key: str) -> str:
    """呼叫 Gemini 產生對應的安全建議。"""

    if not gemini_api_key:
        return ""

    time_range = "未提供"
    if message.time_window:
        time_range = f"{message.time_window[0]} ～ {message.time_window[1]}"

    related = "\n".join(
        f"  • {desc}" for desc in message.aggregated_descriptions[:5]
    )
    if not related:
        related = "  • 無額外描述"

    try:
        from google.generativeai import GenerativeModel, configure

        configure(api_key=gemini_api_key)
        model = GenerativeModel("models/gemini-1.5-flash")
        prompt = f"""
你是 D-FLARE 平台的資安分析師助手。請用繁體中文輸出 Markdown，維持專業語氣並套用以下格式：

🛡️ D-FLARE 分析摘要
🔎 威脅重點
- 內容 A
- 內容 B
🛠️ 防護建議
- 建議 A
- 建議 B
📊 收斂統計
- 收斂筆數：<number>
- 時間範圍：<range>
- 匹配條件：<conditions>

撰寫守則：
- 每個段落使用條列符號，必要時可延伸至三個重點。
- 若資訊缺失，請以「未提供」填補。
- 不得重新翻譯或遺漏上述標題與順序。

事件摘要：
- 嚴重度：{SEVERITY_LABELS.get(message.severity, message.severity)}
- 來源 IP：{message.source_ip or '未提供'}
- 代表描述：{message.description or '未提供'}
- 收斂筆數：{message.aggregated_count}
- 時間範圍：{time_range}
- 匹配條件：{message.match_signature or '未提供'}
- 相似描述：
{related}
"""
        response = model.generate_content(prompt)
        return (response.text or "").strip()
    except Exception as exc:  # pragma: no cover - 離線環境
        return f"（無法取得 AI 建議：{exc}）"


def notification_pipeline(
    result_csv: str,
    gemini_api_key: str,
    line_channel_access_token: str,
    line_webhook_url: str,
    discord_webhook_url: str,
    ui_callback: Callable[[str], None] | None,
    *,
    convergence_config: Optional[Dict[str, object]] = None,
) -> None:
    """統一處理 Gemini、LINE 與 Discord 的自動推播流程。"""
    if not os.path.exists(result_csv):
        if ui_callback:
            ui_callback(f"❌ 結果檔不存在：{result_csv}")
        return

    try:
        dataframe = pd.read_csv(result_csv)
    except Exception as exc:  # pragma: no cover
        if ui_callback:
            ui_callback(f"❌ 讀取結果 CSV 失敗：{exc}")
        return

    messages = _aggregate_high_risk_events(dataframe, convergence=convergence_config)
    if not messages:
        if ui_callback:
            ui_callback("（本批次無高風險事件或缺少必要欄位）")
        return

    any_sent = False
    for message in messages:
        if gemini_api_key:
            message.suggestion = ask_gemini(message, gemini_api_key)
        text = message.to_text()
        if ui_callback:
            ui_callback(text)
        if send_line_to_all(line_channel_access_token, text, callback=ui_callback):
            any_sent = True
        if send_discord(discord_webhook_url, text, callback=ui_callback):
            any_sent = True

    if ui_callback:
        if any_sent:
            ui_callback("🎉 本批次收斂後的高風險事件已完成推播")
        else:
            ui_callback("（已顯示通知內容，但未設定外部推播管道）")


# ---- LINE Webhook 測試伺服器 ----
def run_line_webhook_server(
    channel_secret: str,
    access_token: str,
    host: str = "0.0.0.0",
    port: int = 8000,
) -> None:
    """提供簡易的 LINE Webhook 測試伺服器。"""
    from flask import Flask, abort, request
    from linebot.v3.messaging import ApiClient, Configuration, MessagingApi
    from linebot.v3.messaging.models import TextMessage
    from linebot.v3.webhook import WebhookHandler
    from linebot.v3.webhooks import MessageEvent, TextMessageContent

    app = Flask(__name__)
    handler = WebhookHandler(channel_secret)

    @app.route("/callback", methods=["POST"])
    def callback() -> str:
        signature = request.headers.get("X-Line-Signature", "")
        body = request.get_data(as_text=True)
        try:
            handler.handle(body, signature)
        except Exception as exc:  # pragma: no cover - 測試伺服器
            print("Webhook 處理失敗", exc)
            abort(400)
        return "OK"

    @handler.add(MessageEvent, message=TextMessageContent)
    def handle_message(event: MessageEvent) -> None:  # pragma: no cover - 外部觸發
        user_id = event.source.user_id
        if user_id:
            ids = set(load_line_users())
            ids.add(user_id)
            with open(USER_FILE, "w", encoding="utf-8") as handle:
                for uid in ids:
                    handle.write(uid + "\n")
            with open(LAST_USER_FILE, "w", encoding="utf-8") as handle:
                handle.write(user_id)
        try:
            configuration = Configuration(access_token=access_token)
            with ApiClient(configuration) as api_client:
                messaging_api = MessagingApi(api_client)
                messaging_api.push_message(
                    to=user_id,
                    messages=[TextMessage(text="✅ 已註冊，成功加入 D-FLARE 威脅通知")],
                )
        except Exception as exc:  # pragma: no cover
            print("回覆歡迎訊息失敗：", exc)

    print(f"LINE Webhook 伺服器啟動於 http://{host}:{port}/callback")
    app.run(host=host, port=port)
