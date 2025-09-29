# -*- coding: utf-8 -*-
"""
log_mapping.py
職責：
- 讀取清洗後的 CSV（含 idseq），只做【字典映射】與【欄位排序】
- idseq 置第一欄；raw_log 若存在則移除
- 檢查唯一值清單是否覆蓋（可選）；未覆蓋者記錄報告
- 流式分塊（TB 等級）、tqdm 進度條、colorama 色彩、CLI 防笨
- QUIET 旗標可關閉所有提示列印（供 pipeline/UI 靜默呼叫）
"""

import os, json
import pandas as pd
from tqdm import tqdm
from colorama import Fore, Style, init as colorama_init
from .utils import check_and_flush

# ---- 初始化 ----
colorama_init(autoreset=True)

# 可靜默的全域旗標
QUIET = False

# ---- CONFIG ----
CSV_CHUNK_SIZE = 100_000
DEFAULT_INPUT  = "processed_logs.csv"
DEFAULT_OUTPUT = "preprocessed_data.csv"
DEFAULT_UNIQUE = "log_unique_values.json"  # 由 cleaning 產出的唯一值清單（可無）

# —— 核心欄位順序（idseq 置頂；不含 raw_log）——
CORE_ORDER = [
    "idseq", "datetime", "subtype",
    "srcip", "srcport", "srcintf",
    "dstip", "dstport", "dstintf",
    "action", "sentpkt", "rcvdpkt",
    "duration", "service", "devtype", "level",
    "crscore", "crlevel", "is_attack"
]

# —— 類別映射字典（依需要擴充；未知值 → -1）——
CATEGORICAL_MAPPINGS = {
    "subtype": {
        "unknown": 0, "forward": 1, "local": 2, "app-ctrl": 3, "appctrl": 3,
        "webfilter": 4, "ssl": 5, "anomaly": 6, "ips": 7, "dos": 8, "voip": 9,
        "virus": 10, "multicast": 11, "email": 12, "application": 19, "traffic": 24,
        "system": 22, "user": 23, "vpn": 25, "ddos": 26, "portscan": 27
    },
    "srcintf": {"unknown": 0, "root": 1, "port4": 2, "port7": 3, "port9": 4, "vlan19": 6, "vlan250": 7},
    "dstintf": {"unknown": 0, "root": 1, "port1": 2, "port2": 3, "port3": 4, "port4": 5, "vlan1": 12, "vlan19": 13},
    "action":  {"unknown": 0, "accept": 1, "deny": 2, "block": 3, "close": 7, "detect": 8, "timeout": 9, "drop": 15},
    "devtype": {"unknown": -1, "router": 1},
    "crlevel": {"unknown": 0,  "low": 1, "medium": 2, "high": 3, "critical": 4},
    "level":   {"unknown": 0, "notice": 1, "warning": 2, "error": 3, "information": 4, "critical": 5}
}

UNIQUE_CHECK_COLS = ["subtype","level","srcintf","dstintf","action","service","devtype","crlevel"]

# ---- 工具 ----
# ---- 工具 ----
def _ask_path(prompt, default_path):
    if QUIET:
        return default_path
    p = input(Fore.CYAN + f"{prompt}（預設 {default_path}）：").strip()
    return p if p else default_path

def _reorder_preserve(df: pd.DataFrame) -> pd.DataFrame:
    for c in CORE_ORDER:
        if c not in df.columns:
            df[c] = "" if c != "datetime" else pd.NaT
    rest = [c for c in df.columns if c not in CORE_ORDER and c != "raw_log"]
    return df[CORE_ORDER + rest]

def _normalize_str(s: pd.Series) -> pd.Series:
    return s.astype(str).str.strip().str.lower().fillna("unknown")

def _build_dynamic_mapping(col_values, base: dict = None):
    """
    依唯一值清單建立穩定映射表（unknown→0；其餘依字母序／自然序）。
    若提供 base，會優先套用 base 中已定義的值（保留你的手動表）。
    """
    base = base.copy() if base else {}
    mapping = {}
    # 先放 unknown
    mapping["unknown"] = base.get("unknown", 0)
    used = set(mapping.values())

    # 其餘依序編碼（跳過已存在於 base 的）
    pool = sorted({str(v).lower() for v in col_values if str(v).strip()})
    next_id = max(used) + 1 if used else 1
    for v in pool:
        if v in mapping: 
            continue
        if v in base:
            mapping[v] = base[v]
            used.add(base[v])
        else:
            while next_id in used:
                next_id += 1
            mapping[v] = next_id
            used.add(next_id)
            next_id += 1
    return mapping

def _load_unique_values(path: str):
    if not os.path.exists(path):
        if not QUIET:
            print(Fore.YELLOW + f"⚠️ 找不到唯一值清單：{path}，跳過覆蓋檢查")
        return {}, False
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f), True
    except Exception:
        if not QUIET:
            print(Fore.YELLOW + f"⚠️ 無法讀取唯一值清單：{path}，跳過覆蓋檢查")
        return {}, False

def _check_coverage(chunk: pd.DataFrame, uniq_map: dict, missing: dict):
    for col in UNIQUE_CHECK_COLS:
        if col in chunk.columns and col in uniq_map:
            seen = set(map(str, chunk[col].astype(str).unique()))
            valid = set(map(str, uniq_map[col]))
            diff = seen - valid
            if diff:
                missing.setdefault(col, set()).update(diff)

def _apply_mappings(df: pd.DataFrame, uniq_map: dict = None) -> pd.DataFrame:
    """
    強化版：
    - 既有手動映射：subtype/srcintf/dstintf/action/devtype/crlevel/level（維持）
    - 新增：service 亦做映射（使用唯一值清單動態建表，unknown→0）
    """
    # 1) 固定欄位：使用預先定義的 CATEGORICAL_MAPPINGS
    for col, mapping in CATEGORICAL_MAPPINGS.items():
        if col not in df.columns:
            continue
        if pd.api.types.is_numeric_dtype(df[col]):
            continue
        s = _normalize_str(df[col])
        df[col] = s.map(lambda x: mapping.get(x, -1)).astype("int32", errors="ignore")

    # 2) 動態 service 映射（若存在）
    if "service" in df.columns:
        if pd.api.types.is_numeric_dtype(df["service"]):
            # 已是數值就不處理
            pass
        else:
            s = _normalize_str(df["service"])
            # 優先使用唯一值清單；否則以當前 chunk 估計（穩定性較差，但能保工作流程不中斷）
            if uniq_map and "service" in uniq_map and uniq_map["service"]:
                dyn_map = _build_dynamic_mapping(uniq_map["service"])
            else:
                dyn_map = _build_dynamic_mapping(s.unique())
            df["service"] = s.map(lambda x: dyn_map.get(x, 0)).astype("int32", errors="ignore")

    return df

# ---- 主程序（保留 CLI；可靜默） ----
def main():
    if not QUIET:
        print(Style.BRIGHT + "==== 映射 / 排序（log_mapping）====")
    in_csv  = _ask_path("輸入檔（processed_logs.csv）", DEFAULT_INPUT)
    out_csv = _ask_path("輸出檔（preprocessed_data.csv）", DEFAULT_OUTPUT)
    uniq_p  = _ask_path("唯一值清單（可按 Enter 略過）", DEFAULT_UNIQUE)

    if not os.path.exists(in_csv):
        if not QUIET:
            print(Fore.RED + f"❌ 找不到輸入檔：{in_csv}")
        return

    uniq_map, do_check = _load_unique_values(uniq_p)
    first = True
    total = 0
    missing = {}

    for chunk in tqdm(pd.read_csv(in_csv, chunksize=CSV_CHUNK_SIZE, encoding="utf-8"),
                    desc=("分塊處理" if not QUIET else None), unit="chunk", disable=QUIET):
        if "raw_log" in chunk.columns:
            chunk.drop(columns=["raw_log"], inplace=True)
        if "datetime" in chunk.columns and not pd.api.types.is_datetime64_any_dtype(chunk["datetime"]):
            chunk["datetime"] = pd.to_datetime(chunk["datetime"], errors="coerce")

        # 覆蓋檢查在映射前
        if do_check:
            _check_coverage(chunk, uniq_map, missing)

        # 傳入 uniq_map 確保 service 穩定映射
        chunk = _apply_mappings(chunk, uniq_map)
        # 
        check_and_flush("log_mapping", chunk)
        
        if "is_attack" not in chunk.columns:
            if "crscore" in chunk.columns:
                chunk["is_attack"] = (pd.to_numeric(chunk["crscore"], errors="coerce").fillna(0).astype(int) > 0).astype(int)
            else:
                chunk["is_attack"] = 0

        chunk.drop_duplicates(inplace=True)
        chunk = _reorder_preserve(chunk)

        chunk.to_csv(out_csv, mode="w" if first else "a", header=first, index=False, encoding="utf-8")
        first = False
        total += len(chunk)
        if not QUIET:
            print(Fore.GREEN + f"處理 {len(chunk)} 筆，總計 {total} 筆")

    # 報告
    report_path = os.path.splitext(out_csv)[0] + "_mapping_report.json"
    rep = {"total_rows": total}
    rep["uncovered_values"] = {k: sorted(list(v)) for k, v in missing.items()} if missing else "none or not-checked"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(rep, f, ensure_ascii=False, indent=2)

    if not QUIET:
        print(Fore.GREEN + f"✅ 完成：{out_csv}（{total} 筆）")
        print(Fore.GREEN + f"📝 報告：{report_path}")

if __name__ == "__main__":
    main()
