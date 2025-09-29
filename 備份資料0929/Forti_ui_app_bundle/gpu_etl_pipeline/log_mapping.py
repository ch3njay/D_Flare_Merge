# -*- coding: utf-8 -*-
"""
log_mapping.py（GPU 版，改良：預設從 manifest.clean.active_clean_file 讀取）
- 讀取清洗後的 CSV（優先 active_clean_file），進行字典映射與欄位排序
- 分塊讀取/append 輸出；保留互動/靜默
- 相容匯入層：可在 package 或單檔執行
"""
import os
import json
import sys
from tqdm import tqdm
from colorama import Fore, Style, init as colorama_init

# === 匯入相容層 ===
try:
    from .utils import check_and_flush, _HAS_CUDF
except Exception:
    cur_dir = os.path.dirname(os.path.abspath(__file__))
    if cur_dir not in sys.path:
        sys.path.append(cur_dir)
    from utils import check_and_flush, _HAS_CUDF

import pandas as pd
if _HAS_CUDF:
    import cudf as xdf
else:
    import pandas as xdf  # type: ignore

colorama_init(autoreset=True)
QUIET = False

# ---- CONFIG ----
CSV_CHUNK_SIZE = 100_000
DEFAULT_INPUT  = "processed_logs.csv"
DEFAULT_OUTPUT = "preprocessed_data.csv"
DEFAULT_UNIQUE = "log_unique_values.json"

CORE_ORDER = [
    "idseq", "datetime", "subtype",
    "srcip", "srcport", "srcintf",
    "dstip", "dstport", "dstintf",
    "action", "sentpkt", "rcvdpkt",
    "duration", "service", "devtype", "level",
    "crscore", "crlevel", "is_attack"
]

CATEGORICAL_MAPPINGS = {
    "subtype": {
        "unknown": 0, "forward": 1, "local": 2, "app-ctrl": 3, "appctrl": 3,
        "webfilter": 4, "ssl": 5, "anomaly": 6, "ips": 7, "dos": 8, "voip": 9,
        "virus": 10, "multicast": 11, "email": 12, "application": 19, "traffic": 24,
        "system": 22, "user": 23, "vpn": 25, "ddos": 26, "portscan": 27
    },
    "srcintf": {"unknown": 0, "root": 1, "port4": 2, "port7": 3, "port9": 4, "vlan19": 6, "vlan250": 7},
    "dstintf": {"unknown": 0, "port1": 2, "port2": 3, "port3": 4, "port4": 5, "root": 1, "vlan1": 12, "vlan19": 13},
    "action":  {"unknown": 0, "accept": 1, "deny": 2, "block": 3, "close": 7, "detect": 8, "timeout": 9, "drop": 15},
    "devtype": {"unknown": -1, "router": 1},
    "crlevel": {"unknown": 0, "none": 0,  "low": 1, "medium": 2, "high": 3, "critical": 4},
    "level":   {"unknown": 0, "notice": 1, "warning": 2, "error": 3, "information": 4, "critical": 5}
}

UNIQUE_CHECK_COLS = ["subtype","level","srcintf","dstintf","action","service","devtype","crlevel"]

def _ask_path(prompt, default_path):
    if QUIET:
        return default_path
    p = input(Fore.CYAN + f"{prompt}（預設 {default_path}）：").strip()
    return p if p else default_path

def _reorder_preserve(df):
    for c in CORE_ORDER:
        if c not in df.columns:
            df[c] = xdf.NaT if c == "datetime" else ""
    rest = [c for c in df.columns if c not in CORE_ORDER and c != "raw_log"]
    return df[CORE_ORDER + rest]

def _normalize_str(s):
    try:
        return s.astype(str).str.strip().str.lower().fillna("unknown")
    except Exception:
        return s.astype(str).str.lower()

def _build_dynamic_mapping(col_values, base: dict = None):
    base = base.copy() if base else {}
    mapping = {}
    mapping["unknown"] = base.get("unknown", 0)
    used = set(mapping.values())

    pool = sorted({str(v).lower() for v in col_values if str(v).strip()})
    next_id = max(used) + 1 if used else 1
    for v in pool:
        if v in mapping:
            continue
        if v in base:
            mapping[v] = base[v]; used.add(base[v])
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

def _check_coverage(chunk, uniq_map: dict, missing: dict):
    import pandas as _pd
    for col in UNIQUE_CHECK_COLS:
        if col in chunk.columns and col in uniq_map:
            seen = set(map(str, _pd.Series(chunk[col]).astype(str).unique()))
            valid = set(map(str, uniq_map[col]))
            diff = seen - valid
            if diff:
                missing.setdefault(col, set()).update(diff)

def _apply_mappings(df, uniq_map: dict = None):
    # 1) 固定欄位
    for col, mapping in CATEGORICAL_MAPPINGS.items():
        if col not in df.columns:
            continue
        s = _normalize_str(df[col])
        try:
            df[col] = s.map(mapping).fillna(-1).astype("int32")
        except Exception:
            df[col] = s.map(lambda x: mapping.get(x, -1))

    # 2) service 動態映射
    if "service" in df.columns:
        if uniq_map and "service" in uniq_map and uniq_map["service"]:
            dyn_map = _build_dynamic_mapping(uniq_map["service"])
        else:
            try:
                values = df["service"].astype(str).unique().to_pandas().tolist()
            except Exception:
                import pandas as _pd
                values = _pd.Series(df["service"]).astype(str).unique().tolist()
            dyn_map = _build_dynamic_mapping(values)
        s = _normalize_str(df["service"])
        try:
            df["service"] = s.map(dyn_map).fillna(0).astype("int32")
        except Exception:
            df["service"] = s.map(lambda x: dyn_map.get(x, 0))
    return df

def _read_manifest(run_dir: str = None) -> dict:
    """
    嘗試讀取 run_dir/manifest.json；若 run_dir 未提供，嘗試從當前目錄向上尋找。
    找不到時回傳 {}
    """
    candidates = []
    if run_dir:
        candidates.append(os.path.join(run_dir, "manifest.json"))
    # 常見相對位置
    candidates += [
        os.path.abspath("./manifest.json"),
        os.path.abspath(os.path.join(os.getcwd(), "manifest.json"))
    ]
    for p in candidates:
        if os.path.exists(p):
            try:
                with open(p, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
    return {}

def main(in_csv: str = None,
         out_csv: str = None,
         uniq_json: str = None,
         # 允許多餘參數（由 pipeline 傳入），保持相容
         batch_mode: bool = None,
         batch_size: int = None,
         quiet: bool = None,
         run_dir: str = None,
         use_manifest: bool = True,
         **kwargs):
    """
    - 預設 use_manifest=True：優先讀 manifest.clean.active_clean_file 作為輸入
    - 若讀取失敗或不存在，回退到 in_csv 或 DEFAULT_INPUT
    """
    global QUIET, CSV_CHUNK_SIZE
    if quiet is not None:
        QUIET = bool(quiet)
    if batch_size:
        CSV_CHUNK_SIZE = int(batch_size)

    if not QUIET:
        print(Style.BRIGHT + "==== 映射 / 排序（gpu_log_mapping）====")

    src_from_manifest = None
    if use_manifest:
        m = _read_manifest(run_dir)
        try:
            src_from_manifest = m.get("clean", {}).get("active_clean_file", None)
        except Exception:
            src_from_manifest = None

    # 優先順序：manifest → in_csv → DEFAULT_INPUT
    in_csv  = src_from_manifest or in_csv  or _ask_path("輸入檔（processed_logs.csv 或 sampled_logs.csv）", DEFAULT_INPUT)
    out_csv = out_csv or _ask_path("輸出檔（preprocessed_data.csv）", DEFAULT_OUTPUT)
    uniq_p  = uniq_json or _ask_path("唯一值清單（可按 Enter 略過）", DEFAULT_UNIQUE)

    # 若 run_dir 存在，將 out_csv 落地到 01_map
    if run_dir:
        dir_map = os.path.join(run_dir, "01_map")
        os.makedirs(dir_map, exist_ok=True)
        out_csv = out_csv if os.path.isabs(out_csv) else os.path.join(dir_map, os.path.basename(out_csv))

    if not os.path.exists(in_csv):
        if not QUIET:
            print(Fore.RED + f"❌ 找不到輸入檔：{in_csv}")
        return

    uniq_map, do_check = _load_unique_values(uniq_p)
    first = True
    total = 0
    missing = {}

    import pandas as _pandas
    for chunk_pd in tqdm(_pandas.read_csv(in_csv, chunksize=CSV_CHUNK_SIZE, encoding="utf-8"),
                         desc=("分塊處理" if not QUIET else None), unit="chunk", disable=QUIET):
        chunk = xdf.DataFrame.from_pandas(chunk_pd) if _HAS_CUDF else chunk_pd

        if "raw_log" in chunk.columns:
            try:
                chunk.drop(columns=["raw_log"], inplace=True)
            except Exception:
                pass

        if "datetime" in chunk.columns:
            try:
                chunk["datetime"] = xdf.to_datetime(chunk["datetime"], errors="coerce")
            except Exception:
                chunk["datetime"] = xdf.to_datetime(chunk["datetime"])

        if do_check:
            _check_coverage(chunk_pd, uniq_map, missing)

        chunk = _apply_mappings(chunk, uniq_map)
        if "is_attack" not in chunk.columns:
            # 保底：若缺失則補 0
            try:
                chunk["is_attack"] = 0
            except Exception:
                pass

        chunk = _reorder_preserve(chunk)

        # 寫檔
        mode = "w" if first else "a"
        chunk.to_csv(out_csv, mode=mode, header=first, index=False, encoding="utf-8")
        first = False
        total += len(chunk)

        check_and_flush("gpu_log_mapping", chunk)

    if not QUIET:
        print(Fore.GREEN + f"✅ 輸出：{out_csv}（{total} 筆）")

    # 回寫 manifest.map
    if run_dir:
        m = _read_manifest(run_dir)
        m.setdefault("map", {})
        m["map"]["input"] = os.path.abspath(in_csv)
        m["map"]["output"] = os.path.abspath(out_csv)
        try:
            with open(os.path.join(run_dir, "manifest.json"), "w", encoding="utf-8") as f:
                json.dump(m, f, ensure_ascii=False, indent=2)
            if not QUIET:
                print(Style.BRIGHT + Fore.GREEN + "🧭 manifest.map 已更新")
        except Exception as e:
            if not QUIET:
                print(Fore.YELLOW + f"⚠️ manifest.map 寫入失敗：{e}")
