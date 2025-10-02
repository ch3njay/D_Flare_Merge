"""Reusable notification utilities for D-FLARE."""

from __future__ import annotations

import hashlib
import os
from typing import Callable, Dict, Iterable, Optional, Set, Tuple

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
    "description": ["description", "msg", "event_message", "Description"],
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


def send_discord(webhook_url: str, content: str, max_retries: int = 3) -> Tuple[bool, str]:
    """Send *content* to a Discord *webhook_url* with retry mechanism.

    Returns ``(True, "OK")`` on success or ``(False, error)`` on failure.
    """
    import time
    
    if requests is None:  # pragma: no cover - fallback
        return False, "requests library unavailable"
    
    if not webhook_url or not webhook_url.strip():
        return False, "Discord webhook URL is empty"
    
    # 準備 session 和 headers
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'D-FLARE/1.0 (Discord Bot)',
        'Content-Type': 'application/json'
    })
    
    for attempt in range(max_retries):
        try:
            # 使用較長的超時時間和連線設定
            resp = session.post(
                webhook_url, 
                json={"content": content[:2000]},  # Discord 訊息長度限制
                timeout=(10, 30),  # (連線超時, 讀取超時)
                allow_redirects=True
            )
            
            if resp.status_code == 429:  # Rate limit
                retry_after = int(resp.headers.get('Retry-After', 1))
                if attempt < max_retries - 1:
                    time.sleep(min(retry_after, 5))  # 最多等待 5 秒
                    continue
                return False, f"Rate limited, retry after {retry_after}s"
            
            if 200 <= resp.status_code < 300:
                return True, "OK"
            
            return False, f"HTTP {resp.status_code}: {resp.text[:200]}"
            
        except requests.exceptions.ConnectionError as exc:
            error_msg = f"連線錯誤 (嘗試 {attempt + 1}/{max_retries}): {str(exc)[:100]}"
            if attempt < max_retries - 1:
                # 指數退避重試
                wait_time = min(2 ** attempt, 5)
                time.sleep(wait_time)
                continue
            return False, error_msg
            
        except requests.exceptions.Timeout as exc:
            error_msg = f"連線超時 (嘗試 {attempt + 1}/{max_retries}): {str(exc)[:100]}"
            if attempt < max_retries - 1:
                time.sleep(1)
                continue
            return False, error_msg
            
        except Exception as exc:
            error_msg = f"發送失敗: {str(exc)[:100]}"
            if attempt < max_retries - 1 and "Connection" in str(exc):
                time.sleep(1)
                continue
            return False, error_msg
    
    return False, f"重試 {max_retries} 次後仍然失敗"


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


def ask_gemini(desc: str, api_key: str) -> str:
    """Query Gemini for a two-line English recommendation.

    Falls back to a fixed message if the API call fails.
    """

    try:  # pragma: no cover - external service
        import google.generativeai as genai

        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-pro")
        prompt = (
            "The following is a Fortinet event description:\n"
            f"{desc}\n"
            "Please provide two lines in English: the first line describes the threat, "
            "the second line gives an immediate recommendation."
        )
        response = model.generate_content(prompt)
        text = response.text.strip()
        if "\n" not in text:
            text += "\nNo further recommendation."
        return text
    except Exception:
        return (
            "Threat description: AI recommendation unavailable.\n"
            "Immediate recommendation: please refer to internal procedures."
        )


def _find_column(columns: Iterable[str], aliases: Iterable[str]) -> Optional[str]:
    lowered = {c.lower(): c for c in columns}
    for alias in aliases:
        if alias.lower() in lowered:
            return lowered[alias.lower()]
    return None


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
    results = []
    total = len(rows)
    for idx, row in enumerate(rows, 1):
        if atk_col:
            val = row.get(atk_col, 0)
            try:
                atk = int(val)
            except Exception:
                atk = 1 if str(val).strip().lower() in {"1", "true", "yes"} else 0
            if atk != 1:
                continue
        cr_int = normalize_crlevel(row.get(cr_col))
        if cr_int is None or cr_int not in risk_ints:
            continue
        cr_text = {1: "low", 2: "medium", 3: "high", 4: "critical"}[cr_int]
        srcip = row.get(src_col)
        desc = row.get(desc_col)

        if gemini_key:
            ai_text = ask_gemini(str(desc), gemini_key)
            lines = ai_text.splitlines()
            reco1 = lines[0] if lines else ""
            reco2 = lines[1] if len(lines) > 1 else ""
            message = (
                "🚨 High-risk event detected (Fortinet)\n"
                f"Level: {cr_text} ({cr_int})\n"
                f"Source IP: {srcip}\n"
                f"Description: {desc}\n"
                "———— AI Recommendation ————\n"
                f"{reco1}\n{reco2}"
            )
        else:
            message = (
                "🚨 High-risk event detected (Fortinet)\n"
                f"Level: {cr_text} ({cr_int})\n"
                f"Source IP: {srcip}\n"
                f"Description: {desc}"
            )

        if ui_log:
            ui_log(message)
        ok = True
        info = ""
        if discord_webhook:
            ok, info = send_discord(discord_webhook, message)
        if line_token:
            send_line_to_all(line_token, message, callback=ui_log)
        results.append((message, ok, info))
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

