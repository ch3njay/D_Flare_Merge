"""Cisco UI 通知模組。

此檔案整合 LINE、Discord 與 Gemini 推播相關的實作，
供 Streamlit 頁面與自動化流程呼叫，確保在獨立執行時
仍保留完整通知能力。
"""
from __future__ import annotations

import json
import os
from typing import Callable, Iterable, List

import pandas as pd
import requests

from .utils_labels import NotificationMessage, SEVERITY_LABELS

USER_FILE = "line_users.txt"
LAST_USER_FILE = "last_user.txt"


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


def send_discord(webhook_url: str, message: str, callback: Callable[[str], None] | None = None, max_retries: int = 3) -> bool:
    """透過 Discord Webhook 推播文字訊息，支援重試機制。"""
    import time
    
    if not webhook_url or not webhook_url.strip():
        if callback:
            callback("❌ Discord webhook URL 未設定")
        return False
    
    # 準備 session
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'D-FLARE-Cisco/1.0',
        'Content-Type': 'application/json'
    })
    
    for attempt in range(max_retries):
        try:
            response = session.post(
                webhook_url, 
                json={"content": message[:2000]},  # Discord 限制
                timeout=(10, 30),
                allow_redirects=True
            )
            
            if response.status_code == 429:  # Rate limit
                retry_after = int(response.headers.get('Retry-After', 1))
                if callback:
                    callback(f"⏳ Discord 限流，等待 {retry_after} 秒後重試...")
                if attempt < max_retries - 1:
                    time.sleep(min(retry_after, 5))
                    continue
                if callback:
                    callback("❌ Discord 限流超時")
                return False
                
            if response.status_code in (200, 204):
                if callback:
                    callback("✅ Discord 已發送")
                return True
                
            if callback:
                callback(f"❌ Discord 發送失敗，狀態碼：{response.status_code}")
            return False
            
        except requests.exceptions.ConnectionError as exc:
            error_msg = f"連線錯誤 (嘗試 {attempt + 1}/{max_retries}): {str(exc)[:100]}"
            if callback:
                callback(f"⚠️ {error_msg}")
            if attempt < max_retries - 1:
                wait_time = min(2 ** attempt, 5)
                time.sleep(wait_time)
                continue
            return False
            
        except requests.exceptions.Timeout as exc:
            if callback:
                callback(f"⏳ 連線超時 (嘗試 {attempt + 1}/{max_retries})")
            if attempt < max_retries - 1:
                time.sleep(1)
                continue
            return False
            
        except Exception as exc:
            if callback:
                callback(f"❌ Discord 發送例外 (嘗試 {attempt + 1}/{max_retries})：{str(exc)[:100]}")
            if attempt < max_retries - 1 and "Connection" in str(exc):
                time.sleep(1)
                continue
            return False
    
    if callback:
        callback(f"❌ Discord 重試 {max_retries} 次後仍然失敗")
    return False


def ask_gemini(log_description: str, gemini_api_key: str) -> str:
    """呼叫 Gemini 產生對應的安全建議。"""
    if not gemini_api_key:
        return ""
    try:
        from google.generativeai import GenerativeModel, configure

        configure(api_key=gemini_api_key)
        model = GenerativeModel("models/gemini-1.5-flash")
        prompt = (
            "你是一位資安分析師。請用繁體中文簡短回覆以下兩段建議，每段不限制兩句，取消任何格式標記：\n"
            "1. 威脅說明：這筆日誌描述了什麼潛在風險？\n"
            "2. 防禦建議：該如何立即應對與預防？\n"
            f"事件日誌：{log_description}"
        )
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as exc:  # pragma: no cover - 離線環境
        return f"（無法取得 AI 建議：{exc}）"


# ---- Pipeline 整合 ----
def _iterate_high_risk_events(dataframe: pd.DataFrame) -> Iterable[NotificationMessage]:
    """從模型結果 DataFrame 中挑選高風險事件。"""
    candidates = dataframe[dataframe["Severity"].astype(str).isin(["1", "2", "3"])]
    for _, row in candidates.iterrows():
        yield NotificationMessage(
            severity=int(row.get("Severity", 0) or 0),
            source_ip=str(row.get("SourceIP", "")),
            description=str(row.get("Description", "")),
        )


def notification_pipeline(
    result_csv: str,
    gemini_api_key: str,
    line_channel_access_token: str,
    line_webhook_url: str,
    discord_webhook_url: str,
    ui_callback: Callable[[str], None] | None,
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

    any_sent = False
    for message in _iterate_high_risk_events(dataframe):
        suggestion = ask_gemini(message.description, gemini_api_key)
        full_message = message.to_text().replace(message.suggestion, suggestion)
        if send_line_to_all(line_channel_access_token, full_message, callback=ui_callback):
            any_sent = True
        if send_discord(discord_webhook_url, full_message, callback=ui_callback):
            any_sent = True

    if not any_sent and ui_callback:
        ui_callback("（本批次無高風險事件，不推播）")
    if any_sent and ui_callback:
        ui_callback("🎉 本批次高風險事件已全數推播")


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
