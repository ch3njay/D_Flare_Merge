"""Reusable notification utilities for D-FLARE."""

from __future__ import annotations

import hashlib
import os
from typing import Callable, Dict, Iterable, List, Optional, Set, Tuple

try:  # pragma: no cover - best effort import
    import pandas as pd
    if not hasattr(pd, "read_csv"):  # stub detected
        pd = None  # type: ignore[assignment]
except Exception:  # pragma: no cover - fallback when pandas unavailable
    pd = None
try:  # pragma: no cover - best effort import
    import requests
except Exception:  # pragma: no cover - network disabled
    requests = None  # type: ignore

# 添加 ui_shared 模組路徑
import sys
from pathlib import Path
_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT / "ui_shared") not in sys.path:
    sys.path.insert(0, str(_ROOT / "ui_shared"))

from notification_models import NotificationMessage, SEVERITY_LABELS

USER_FILE = "line_users.txt"

# Mapping from various severity representations to numeric levels
_CRLEVEL_MAP = {
    "1": 1,
    "low": 1,
    "2": 2,
    "medium": 2,
    "3": 3,
    "high": 3,
    "4": 4,
    "critical": 4,
}

_COLUMN_ALIASES: Dict[str, Iterable[str]] = {
    "crlevel": ["crlevel", "cr_level", "level", "severity"],
    "srcip": ["srcip", "sourceip", "src_ip", "source_ip"],
    "dstip": ["dstip", "destinationip", "dst_ip", "destination_ip"],
    "protocol": ["protocol", "proto", "l4proto"],
    "dstport": ["dstport", "destination_port", "dest_port", "service_port"],
    "description": ["description", "msg", "event_message", "Description"],
    "timestamp": [
        "timestamp",
        "eventtime",
        "log_time",
        "date",
        "time",
        "EventTime",
    ],
}

_CONVERGENCE_DEFAULT = {"window_minutes": 10, "group_fields": ["source", "destination"]}
_CONVERGENCE_LABELS = {
    "source": "來源 IP",
    "destination": "目的 IP",
    "protocol": "通訊協定",
    "port": "目的 Port",
}


def normalize_crlevel(value) -> Optional[int]:
    """Normalize *crlevel* to an integer 1-4.

    Returns ``None`` if *value* cannot be interpreted.
    """

    if isinstance(value, (int, float)):
        val = int(value)
        return val if val in {1, 2, 3, 4} else None
    key = str(value).strip().lower()
    return _CRLEVEL_MAP.get(key)


def send_discord(webhook_url: str, content: str) -> Tuple[bool, str]:
    """Send *content* to a Discord *webhook_url*.

    Returns ``(True, "OK")`` on success or ``(False, error)`` on failure.
    """

    if requests is None:  # pragma: no cover - fallback
        return False, "requests library unavailable"
    try:
        resp = requests.post(webhook_url, json={"content": content}, timeout=10)
        if 200 <= resp.status_code < 300:
            return True, "OK"
        return False, f"{resp.status_code}: {resp.text}"
    except Exception as exc:  # pragma: no cover - network errors
        return False, str(exc)


def load_line_users(user_file: str = USER_FILE) -> Iterable[str]:
    """Load LINE user IDs from *user_file* if present."""

    if not os.path.exists(user_file):
        return []
    with open(user_file, "r", encoding="utf-8") as fh:
        return [line.strip() for line in fh if line.strip()]


def _push_line(access_token: str, user_id: str, msg: str) -> bool:
    """Push *msg* to a single LINE *user_id*."""

    if requests is None:  # pragma: no cover - fallback when requests missing
        return False
    url = "https://api.line.me/v2/bot/message/push"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }
    payload = {"to": user_id, "messages": [{"type": "text", "text": msg}]}
    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=10)
        return resp.status_code == 200
    except Exception:  # pragma: no cover - network error
        return False


def send_line_to_all(access_token: str, msg: str, callback=None) -> bool:
    """Send *msg* to all registered LINE users."""

    user_ids = list(load_line_users())
    if not access_token or len(access_token) < 10:
        if callback:
            callback("LINE Channel Access Token not set")
        return False
    if not user_ids:
        if callback:
            callback("No LINE users registered")
        return False
    success = False
    for uid in user_ids:
        if _push_line(access_token, uid, msg):
            success = True
            if callback:
                callback(f"Sent LINE notification to {uid}")
        elif callback:
            callback(f"Failed to send LINE notification to {uid}")
    return success


def ask_gemini(message: NotificationMessage, api_key: str) -> str:
    """向 Gemini 請求收斂後的安全建議。"""

    if not api_key:
        return ""

    time_range = "未提供"
    if message.time_window:
        time_range = f"{message.time_window[0]} ～ {message.time_window[1]}"

    related = "\n".join(
        f"  • {desc}" for desc in message.aggregated_descriptions[:5]
    )
    if not related:
        related = "  • 無額外描述"

    try:  # pragma: no cover - external service
        import google.generativeai as genai

        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("models/gemini-1.5-flash")
        prompt = f"""
你是 D-FLARE 的 Fortinet 資安分析助手。請使用繁體中文與 Markdown，並依照下列版型產出內容：

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

撰寫指引：
- 條列至少兩項重點，若資訊不足請以「未提供」表示。
- 保留上述標題與順序，不可自行刪改。

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
    except Exception as exc:
        return f"（無法取得 AI 建議：{exc}）"


def _find_column(columns: Iterable[str], aliases: Iterable[str]) -> Optional[str]:
    lowered = {c.lower(): c for c in columns}
    for alias in aliases:
        if alias.lower() in lowered:
            return lowered[alias.lower()]
    return None


def _merge_convergence(config: Optional[Dict[str, object]]) -> Dict[str, object]:
    merged: Dict[str, object] = dict(_CONVERGENCE_DEFAULT)
    if not config:
        return merged

    window = config.get("window_minutes")
    try:
        window_val = int(window) if window is not None else None
    except (TypeError, ValueError):
        window_val = None
    if window_val and window_val > 0:
        merged["window_minutes"] = window_val

    fields = config.get("group_fields")
    if isinstance(fields, (list, tuple)):
        normalized: List[str] = []
        for field in fields:
            key = str(field)
            if key in _CONVERGENCE_LABELS:
                normalized.append(key)
        if normalized:
            merged["group_fields"] = normalized
    return merged


def _resolve_convergence_column(columns: Iterable[str], alias_key: str) -> Optional[str]:
    if alias_key == "source":
        aliases = _COLUMN_ALIASES["srcip"]
    elif alias_key == "destination":
        aliases = _COLUMN_ALIASES.get("dstip", [])
    elif alias_key == "protocol":
        aliases = _COLUMN_ALIASES.get("protocol", [])
    elif alias_key == "port":
        aliases = _COLUMN_ALIASES.get("dstport", [])
    else:
        aliases = []
    return _find_column(columns, aliases)


def _parse_attack_flag(value: object) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        text = str(value).strip().lower()
        return 1 if text in {"1", "true", "yes", "attack"} else 0


def _aggregate_notifications(
    dataframe: "pd.DataFrame",
    src_col: str,
    desc_col: str,
    convergence: Optional[Dict[str, object]] = None,
) -> List[NotificationMessage]:
    config = _merge_convergence(convergence)

    timestamp_col = _find_column(dataframe.columns, _COLUMN_ALIASES.get("timestamp", []))
    if timestamp_col:
        dataframe["_event_time"] = pd.to_datetime(dataframe[timestamp_col], errors="coerce")
    else:
        dataframe["_event_time"] = pd.NaT

    window = max(1, int(config.get("window_minutes", 10) or 10))
    if timestamp_col:
        dataframe["_bucket"] = dataframe["_event_time"].dt.floor(f"{window}min")
    else:
        dataframe["_bucket"] = None

    group_columns: List[str] = []
    if timestamp_col:
        group_columns.append("_bucket")

    alias_columns: Dict[str, str] = {}
    for alias_key in config.get("group_fields", []):
        column = _resolve_convergence_column(dataframe.columns, alias_key)
        if column:
            group_columns.append(column)
            alias_columns[alias_key] = column

    if not group_columns:
        dataframe["_row_id"] = range(len(dataframe))
        group_columns.append("_row_id")

    messages: List[NotificationMessage] = []
    for _, group in dataframe.groupby(group_columns, dropna=False):
        severity_series = group["_severity"].dropna().astype(int)
        if severity_series.empty:
            continue
        severity = int(severity_series.iloc[0])
        source_value = str(group[src_col].iloc[0]) if src_col in group else ""
        if source_value.lower() == "nan":
            source_value = ""
        description_value = str(group[desc_col].iloc[0]) if desc_col in group else ""

        message = NotificationMessage(
            severity=severity,
            source_ip=source_value,
            description=description_value,
            aggregated_count=len(group),
        )

        if desc_col in group:
            desc_series = group[desc_col].dropna()
            message.aggregated_descriptions = (
                desc_series.astype(str).drop_duplicates().tolist()
            )

        if "_event_time" in group:
            valid_times = group["_event_time"].dropna()
            if not valid_times.empty:
                start = valid_times.min()
                end = valid_times.max()
                message.time_window = (
                    start.strftime("%Y-%m-%d %H:%M"),
                    end.strftime("%Y-%m-%d %H:%M"),
                )

        signature_parts: List[str] = []
        for alias_key, column in alias_columns.items():
            value = group[column].iloc[0] if column in group else ""
            if pd.isna(value):
                value = ""
            signature_parts.append(
                f"{_CONVERGENCE_LABELS.get(alias_key, column)}：{value or '未提供'}"
            )
            if alias_key == "source" and not message.source_ip:
                message.source_ip = str(value)
        message.match_signature = "、".join(signature_parts)
        messages.append(message)

    return messages
def notify_from_csv(
    csv_path: str,
    discord_webhook: str,
    gemini_key: str,
    *,
    risk_levels: Iterable = ("3", "4"),
    ui_log=None,
    dedupe_cache: Optional[Dict] = None,
    progress_cb: Optional[Callable[[float], None]] = None,
    line_token: str = "",
    convergence: Optional[Dict[str, object]] = None,
):
    """Read a Fortinet event CSV and push high-risk rows to Discord/LINE."""

    if dedupe_cache is not None:
        strategy = dedupe_cache.get("strategy", "mtime")
        cache: Set[str] = dedupe_cache.setdefault("keys", set())
        if strategy == "hash":
            with open(csv_path, "rb") as fh:
                file_hash = hashlib.sha1(fh.read()).hexdigest()
            dedupe_key = f"{csv_path}:{file_hash}"
        else:
            mtime = os.path.getmtime(csv_path)
            dedupe_key = f"{csv_path}:{mtime}"
        if dedupe_key in cache:
            if ui_log:
                ui_log("File already processed, skipping notification.")
            return []
        cache.add(dedupe_key)

    import csv

    try:
        if pd is not None:
            df = pd.read_csv(csv_path)
            rows = df.to_dict("records")
            columns = df.columns
        else:  # fallback parser
            with open(csv_path, newline="") as fh:
                reader = csv.DictReader(fh)
                rows = list(reader)
                columns = reader.fieldnames or []
    except Exception as exc:
        if ui_log:
            ui_log(f"Failed to read CSV: {exc}")
        return []

    cr_col = _find_column(columns, _COLUMN_ALIASES["crlevel"])
    src_col = _find_column(columns, _COLUMN_ALIASES["srcip"])
    desc_col = _find_column(columns, _COLUMN_ALIASES["description"])
    atk_col = _find_column(columns, ["is_attack"])
    if not (cr_col and src_col and desc_col):
        if ui_log:
            ui_log("CSV missing required columns.")
        return []

    risk_ints = {normalize_crlevel(x) for x in risk_levels}
    risk_ints.discard(None)
    if not risk_ints:
        risk_ints = {3, 4}

    results = []

    if pd is not None:
        df = pd.DataFrame(rows)
        df["_severity"] = df[cr_col].apply(normalize_crlevel)
        df = df[df["_severity"].isin(risk_ints)]
        if atk_col:
            df = df[df[atk_col].apply(_parse_attack_flag) == 1]

        if df.empty:
            if ui_log:
                ui_log("No events matched the criteria.")
            return []

        messages = _aggregate_notifications(df, src_col, desc_col, convergence)
        if not messages:
            if ui_log:
                ui_log("No events matched the criteria.")
            return []

        total = len(messages)
        for idx, message in enumerate(messages, 1):
            if gemini_key:
                message.suggestion = ask_gemini(message, gemini_key)
            text = message.to_text()
            if ui_log:
                ui_log(text)
            ok = True
            info = ""
            if discord_webhook:
                ok, info = send_discord(discord_webhook, text)
            if line_token:
                send_line_to_all(line_token, text, callback=ui_log)
            results.append((text, ok, info))
            if progress_cb:
                progress_cb(idx / total if total else 1.0)
        return results

    total = len(rows)
    for idx, row in enumerate(rows, 1):
        if atk_col and _parse_attack_flag(row.get(atk_col, 0)) != 1:
            continue
        severity = normalize_crlevel(row.get(cr_col))
        if severity is None or severity not in risk_ints:
            continue
        message = NotificationMessage(
            severity=severity,
            source_ip=str(row.get(src_col, "")),
            description=str(row.get(desc_col, "")),
        )
        if gemini_key:
            message.suggestion = ask_gemini(message, gemini_key)
        text = message.to_text()
        if ui_log:
            ui_log(text)
        ok = True
        info = ""
        if discord_webhook:
            ok, info = send_discord(discord_webhook, text)
        if line_token:
            send_line_to_all(line_token, text, callback=ui_log)
        results.append((text, ok, info))
        if progress_cb:
            progress_cb(idx / total if total else 1.0)

    if not results and ui_log:
        ui_log("No events matched the criteria.")
    return results


__all__ = [
    "normalize_crlevel",
    "send_discord",
    "send_line_to_all",
    "ask_gemini",
    "notify_from_csv",
]

