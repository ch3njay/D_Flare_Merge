# -*- coding: utf-8 -*-
"""
log_cleaning.py（GPU 版, 改良：輸出 manifest 與 active_clean_file）
- 分塊流式清洗（TB 等級、防 OOM）
- 進度條（tqdm）、色彩輸出（colorama）
- QUIET 靜默模式：供 pipeline/UI 呼叫；非 QUIET 時支援 tkinter/CLI 互動
- 主資料：移除 raw_log；保留 idseq 並置第一欄
- 即時雙檔輸出（未抽樣 + 抽樣）
- 唯一值清單（json/txt）
- ✅ 新增：產出/更新 manifest.json，並寫入 active_clean_file
"""
import os, re, gzip, json, time, logging
from collections import defaultdict
from tqdm import tqdm
from colorama import init as colorama_init, Fore, Style

# ---- 匯入相容層 ----
try:
    from .utils import check_and_flush, _HAS_CUDF, _HAS_CUPY
except Exception:
    # 允許單檔執行
    from utils import check_and_flush, _HAS_CUDF, _HAS_CUPY

# ---- 資料框相容層（優先 cudf，否則 pandas） ----
if _HAS_CUDF:
    import cudf as xdf
else:
    import pandas as xdf  # type: ignore

# 工具庫：cupy/numpy 二選一
try:
    import cupy as xp  # type: ignore
    _XP = "cupy"
except Exception:
    import numpy as xp  # type: ignore
    _XP = "numpy"

# 可選：GUI
try:
    import tkinter as tk
    from tkinter import filedialog
    TK_OK = True
except Exception:
    TK_OK = False

# 可選：chardet
try:
    import chardet
    HAS_CHARDET = True
except Exception:
    HAS_CHARDET = False

colorama_init(autoreset=True)
logging.basicConfig(filename="gpu_log_cleaning_error.log", level=logging.ERROR,
                    format="%(asctime)s - %(levelname)s - %(message)s")

# =====================[ CONFIG ]=====================
CHUNK_LINES = 50_000
DEFAULT_SAMPLING_SEED = 42
DEFAULT_RANDOM_RATIO = 1.0
DEFAULT_WRITE_RAWDICT = False
RAWDICT_GZ_PATH = "rawlog_dict.jsonl.gz"

# 欄位順序（核心輸出；第一欄 idseq；無 raw_log）
COLUMN_ORDER = [
    'idseq', 'datetime', 'subtype',
    'srcip','srcport','srcintf',
    'dstip','dstport','dstintf',
    'action','sentpkt','rcvdpkt',
    'duration','service','devtype','level',
    'crscore','crlevel','is_attack'
]

UNIQUE_COLS = ["subtype", "level", "srcintf", "dstintf", "action", "service", "devtype", "crlevel"]
# ====================================================

KV_PATTERN = re.compile(r'(\w+)=(".*?"|\'.*?\'|[^"\',\s]+)')
QUIET = False


# --- helper for tests ---
def _split_sampling_targets(df):
    """Return rows that are attacks with known crlevel and the remaining rows."""
    targets_idx = [
        i for i, (c, a) in enumerate(zip(df["crlevel"], df["is_attack"]))
        if a == 1 and c not in {"unknown", "none"}
    ]
    others_idx = [i for i in range(len(df["crlevel"])) if i not in targets_idx]
    return df.select(targets_idx), df.select(others_idx)

# -------------------- 工具 --------------------
def _get_tk_root():
    root = tk.Tk(); root.withdraw(); return root

def _select_files_interactive():
    if (not QUIET) and TK_OK:
        print(f"{Fore.WHITE}【提示】📂 顯示檔案選擇（可多選）")
        _get_tk_root()
        paths = filedialog.askopenfilenames(
            title="選擇日誌檔案",
            filetypes=[("Log/CSV files", "*.txt *.csv *.gz"), ("All files","*.*")]
        )
        if paths: return list(paths)
    while not QUIET:
        s = input("請輸入日誌檔路徑（可多個，分號;分隔）：").strip()
        if s:
            paths = [p.strip() for p in s.split(";") if p.strip()]
            if all(os.path.exists(p) for p in paths):
                return paths
        print("❌ 路徑錯誤，請重試。")
    raise ValueError("QUIET 模式需由呼叫端提供 paths 參數。")

def _select_save_path_interactive(prompt, default_name):
    if (not QUIET) and TK_OK:
        _get_tk_root()
        p = filedialog.asksaveasfilename(title=prompt, defaultextension=".csv",
                                         initialfile=default_name, filetypes=[("CSV files","*.csv")])
        if p: return p
    if not QUIET:
        s = input(f"{prompt}（預設 {default_name}）：").strip()
        return s if s else default_name
    return default_name

def _detect_encoding(path):
    if not HAS_CHARDET: return "utf-8"
    try:
        with open(path, "rb") as f:
            return chardet.detect(f.read(10000)).get("encoding") or "utf-8"
    except Exception:
        return "utf-8"

def _clean_text(v):
    import re
    return re.sub(r'[^a-z0-9_]', '', str(v).lower()) if v else "unknown"

def _clean_service(v):
    import re
    s = str(v)
    s = re.sub(r'(?:[\s\-_])?port\d+$', "", s, flags=re.IGNORECASE)
    s = re.sub(r'[-_/](\d+)(?:[-_]\d+)?$', "", s)
    s = re.sub(r'[-_]?(to|udp|tcp)[-_]?\d*$', "", s, flags=re.IGNORECASE)
    s = re.sub(r'\s+\d+$', "", s)
    return _clean_text(s)

def parse_log_line(line):
    """K=V 解析：保留 idseq，不輸出 raw_log（主表）；若啟用外掛字典再另存 raw。"""
    try:
        pairs = KV_PATTERN.findall(line)
        if not pairs: return None
        kv = {k.lower(): v.strip('"\'') for k, v in pairs}
        return {
            "idseq": kv.get("idseq", ""),
            "date": kv.get("date", ""), "time": kv.get("time", ""), "itime": kv.get("itime", ""),
            "subtype": _clean_text(kv.get("subtype", "unknown")),
            "srcip": kv.get("srcip",""), "srcport": kv.get("srcport","0"),
            "srcintf": _clean_text(kv.get("srcintf","unknown")),
            "dstip": kv.get("dstip",""), "dstport": kv.get("dstport","0"),
            "dstintf": _clean_text(kv.get("dstintf","unknown")),
            "action": _clean_text(kv.get("action","unknown")),
            "sentpkt": kv.get("sentpkt","0"), "rcvdpkt": kv.get("rcvdpkt","0"),
            "duration": kv.get("duration","0"),
            "service": _clean_service(kv.get("service","unknown")),
            "devtype": _clean_text(kv.get("devtype","unknown")),
            "level": _clean_text(kv.get("level","unknown")),
            "crscore": kv.get("crscore","0"),
            "crlevel": _clean_text(kv.get("crlevel","unknown")),
            "raw_line": line.strip()
        }
    except Exception as e:
        logging.error(f"解析失敗：{e}")
        return None

def _finalize_datetime(df):
    # 優先 date+time；否則 itime(epoch 秒)
    try:
        has_datetime = ("date" in df.columns) and ("time" in df.columns)
    except Exception:
        has_datetime = False

    if has_datetime:
        dt = (df["date"].astype("str") + " " + df["time"].astype("str"))
        try:
            df["datetime"] = xdf.to_datetime(dt, errors="coerce")
        except Exception:
            df["datetime"] = xdf.to_datetime(dt)
        for c in ("date","time"):
            try:
                df.drop(columns=[c], inplace=True)
            except Exception:
                pass

    if "datetime" not in df.columns:
        if "itime" in df.columns:
            try:
                df["datetime"] = xdf.to_datetime(df["itime"].astype("int64"), unit="s")
            except Exception:
                df["datetime"] = xdf.to_datetime(df["itime"], unit="s")
    try:
        df.drop(columns=["itime"], inplace=True)
    except Exception:
        pass
    return df

def _set_is_attack(df):
    if "crscore" in df.columns:
        try:
            cs = df["crscore"].astype("int32")
        except Exception:
            cs = df["crscore"].astype("str").astype("int32")
        df["is_attack"] = (cs > 0).astype("int8")
    elif "crlevel" in df.columns:
        safe = {"0","unknown","none",""}
        try:
            mask = ~df["crlevel"].astype("str").str.lower().isin(list(safe))
        except Exception:
            mask = ~df["crlevel"].astype("str").isin(list(safe))
        df["is_attack"] = mask.astype("int8")
    else:
        df["is_attack"] = 0
    return df

def _enforce_crlevel_rule(df):
    """若 crscore==0，crlevel 一律改為 'none'"""
    if "crscore" in df.columns and "crlevel" in df.columns:
        try:
            cs = df["crscore"].astype("int32")
        except Exception:
            cs = df["crscore"].astype("str").astype("int32")
        mask = (cs == 0)
        if mask.any():
            df.loc[mask, "crlevel"] = "none"
    return df

def _reorder_keep_only(df):
    # 確保欄位存在
    for col in COLUMN_ORDER:
        if col not in df.columns:
            df[col] = xdf.NaT if col == "datetime" else ""
    # 僅保留核心欄位
    return df[COLUMN_ORDER]

def _choose_mode_interactive():
    print(f"{Fore.CYAN}請選擇操作模式：")
    print("  1. 預先設定抽樣（處理時同步輸出未抽樣 + 抽樣）")
    print("  2. 後置抽樣（先清洗，再對清洗檔二次抽樣）")
    print("  3. 僅清洗（不抽樣）")
    ans = input("輸入 1/2/3（預設 1）：").strip() or "1"
    return "1" if ans not in ("1","2","3") else ans

def _choose_sampling_interactive():
    print(f"{Fore.CYAN}抽樣方法：")
    print("  1. 隨機 random")
    print("  2. 平衡 balanced（依標籤下採樣）")
    print("  3. 系統 systematic（固定間隔）")
    print("  4. 自訂 custom（label:數量, ...）")
    m = input("輸入 1/2/3/4（預設 1）：").strip() or "1"
    if m not in ("1","2","3","4"): m = "1"
    basis = input("抽樣依據（1=is_attack, 2=crlevel；預設 1）：").strip() or "1"
    label_col = "crlevel" if basis == "2" else "is_attack"
    seed = input(f"隨機種子（預設 {DEFAULT_SAMPLING_SEED}）：").strip()
    try: seed = int(seed) if seed else DEFAULT_SAMPLING_SEED
    except: seed = DEFAULT_SAMPLING_SEED
    cfg = {"method": m, "label_col": label_col, "seed": seed}
    if m == "1":
        r = input(f"隨機比例 0~1（預設 {DEFAULT_RANDOM_RATIO}）：").strip()
        try: cfg["ratio"] = float(r) if r else DEFAULT_RANDOM_RATIO
        except: cfg["ratio"] = DEFAULT_RANDOM_RATIO
    elif m == "4":
        print("格式示例：0:1000,1:1000,2:200")
        cc = input("custom_counts：").strip()
        d = {}
        if cc:
            for part in cc.split(","):
                try:
                    k,v = part.split(":")
                    d[k.strip()] = int(v.strip())
                except: pass
        cfg["custom_counts"] = d
    return cfg

def _write_rawdict_open():
    if not DEFAULT_WRITE_RAWDICT: return None
    return gzip.open(RAWDICT_GZ_PATH, "at", encoding="utf-8")

def _write_rawdict_line(gzfp, rec):
    if gzfp is None: return
    rid = rec.get("idseq","")
    raw = rec.get("raw_line","")
    if rid and raw:
        gzfp.write(json.dumps({"idseq": rid, "raw": raw}, ensure_ascii=False) + "\n")

def _df_sample(df, frac=None, n=None, random_state=None, replace=False):
    return df.sample(frac=frac, n=n, random_state=random_state, replace=replace)

def _ensure_dir(p: str):
    os.makedirs(p, exist_ok=True)

def _atomic_write_json(path: str, payload: dict):
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    os.replace(tmp, path)

# -------------------- 主程序（可靜默） --------------------
def clean_logs(
    quiet: bool = None,
    mode: str = None,
    paths: list = None,
    clean_csv: str = "processed_logs.csv",
    sampled_csv: str = None,
    sampling_cfg: dict = None,
    enable_sampling: bool = True,
    # 這次新增：artifacts/run 目錄（若提供就落地到該處）
    run_dir: str = None
):
    """
    清洗主函式（供 pipeline/UI 呼叫）：
      - quiet=True：完全靜默，不互動；需提供 paths；其它參數可省略
      - quiet=False 或 None：如未提供參數，進入互動式問答（GUI/CLI）
    ✅ 會產出/更新 manifest.json，包含 active_clean_file
    回傳：clean_csv 的實際輸出路徑
    """
    global QUIET
    if quiet is not None:
        QUIET = bool(quiet)

    if not QUIET:
        print(f"{Fore.WHITE}{Style.BRIGHT}==== 清洗 / 標準化（GPU 流式） ====")

    if mode is None:
        mode = _choose_mode_interactive() if not QUIET else ("1" if enable_sampling else "3")
    if paths is None:
        paths = _select_files_interactive() if not QUIET else None
    if QUIET and not paths:
        raise ValueError("QUIET 模式需提供 paths（list[str]）。")

    # 輸出佈局
    run_dir = run_dir or os.path.abspath("./artifacts/" + time.strftime("%Y%m%d_%H%M%S"))
    dir_clean = os.path.join(run_dir, "00_clean")
    _ensure_dir(dir_clean)

    clean_csv = clean_csv if os.path.isabs(clean_csv) else os.path.join(dir_clean, os.path.basename(clean_csv))
    if sampled_csv is None and mode in ("1","2") and enable_sampling:
        sampled_csv = "sampled_logs.csv"
    if sampled_csv:
        sampled_csv = sampled_csv if os.path.isabs(sampled_csv) else os.path.join(dir_clean, os.path.basename(sampled_csv))

    if not QUIET:
        clean_csv = _select_save_path_interactive("選擇清洗後（未抽樣）CSV 儲存位置", clean_csv)
        if mode in ("1","2") and enable_sampling:
            sampled_csv = _select_save_path_interactive("選擇抽樣後 CSV 儲存位置", sampled_csv or os.path.join(dir_clean,"sampled_logs.csv"))

    if sampling_cfg is None:
        if mode in ("1","2") and enable_sampling:
            sampling_cfg = _choose_sampling_interactive() if not QUIET else {
                "method": "1", "ratio": DEFAULT_RANDOM_RATIO,
                "label_col": "is_attack", "seed": DEFAULT_SAMPLING_SEED
            }
        else:
            sampling_cfg = {"method":"1","ratio":1.0,"label_col":"is_attack","seed":DEFAULT_SAMPLING_SEED}

    method_map = {"1":"random","2":"balanced","3":"systematic","4":"custom"}
    method = method_map.get(sampling_cfg.get("method","1"), "random")
    try:
        ratio = float(sampling_cfg.get("ratio", DEFAULT_RANDOM_RATIO))
    except Exception:
        ratio = DEFAULT_RANDOM_RATIO
    label_col = sampling_cfg.get("label_col","is_attack")
    seed = int(sampling_cfg.get("seed", DEFAULT_SAMPLING_SEED))
    custom_counts = sampling_cfg.get("custom_counts", None)

    # 唯一值收集
    uniques = {c: set() for c in UNIQUE_COLS}
    first_clean, first_sample = True, True
    tot_clean, tot_sample = 0, 0
    rawdict_fp = _write_rawdict_open()

    # 解析輸入（可多檔）
    def _iter_lines(paths_list):
        for p in paths_list:
            enc = _detect_encoding(p)
            if p.endswith(".gz"):
                import gzip as _gz
                with _gz.open(p, "rt", encoding=enc, errors="ignore") as f:
                    for line in f:
                        yield line
            else:
                with open(p, "r", encoding=enc, errors="ignore") as f:
                    for line in f:
                        yield line

    def _process_df(buf_records):
        nonlocal first_clean, first_sample, tot_clean, tot_sample
        df = xdf.DataFrame(buf_records)
        df = _finalize_datetime(df)
        df = _set_is_attack(df)
        df = _enforce_crlevel_rule(df)
        try:
            df = df.drop_duplicates()
        except Exception:
            pass
        df = _reorder_keep_only(df)

        # [1] 寫清洗檔
        df.to_csv(clean_csv, mode="w" if first_clean else "a",
                  header=first_clean, index=False, encoding="utf-8")
        first_clean = False
        tot_clean += len(df)

        # [2] 記憶體保護
        check_and_flush("gpu_log_cleaning", df)

        # [3] 寫抽樣（視模式/設定）
        if sampled_csv and enable_sampling:
            if method == "random":
                if ratio >= 1.0:
                    sdf = df
                elif ratio <= 0.0:
                    sdf = df.head(0)
                else:
                    sdf = _df_sample(df, frac=ratio, random_state=seed, replace=False)
            elif method == "balanced":
                # 依 label 下採樣（簡化版本）
                sdf_parts = []
                try:
                    for k, g in df.groupby(label_col):
                        frac = min(ratio, 1.0)
                        if len(g) > 0:
                            sdf_parts.append(_df_sample(g, frac=frac, random_state=seed))
                    sdf = xdf.concat(sdf_parts) if len(sdf_parts) else df.head(0)
                except Exception:
                    sdf = df.head(0)
            elif method == "systematic":
                try:
                    sdf = df.iloc[::max(1, int(1/ratio))] if ratio > 0 and ratio < 1 else df
                except Exception:
                    sdf = df.head(0)
            elif method == "custom" and isinstance(custom_counts, dict):
                sdf_parts = []
                try:
                    for k, g in df.groupby(label_col):
                        n = int(custom_counts.get(str(k), 0))
                        if n <= 0:
                            continue
                        if len(g) > n:
                            sdf_parts.append(g.sample(n=n, random_state=seed))
                        else:
                            sdf_parts.append(g)
                    sdf = xdf.concat(sdf_parts) if len(sdf_parts) else df.head(0)
                except Exception:
                    sdf = df.head(0)
            else:
                sdf = df.head(0)

            if len(sdf):
                sdf.to_csv(sampled_csv, mode="w" if first_sample else "a",
                           header=first_sample, index=False, encoding="utf-8")
                first_sample = False
                tot_sample += len(sdf)

        # uniques（可擴充寫出 json/txt）
        for c in uniques.keys():
            try:
                uniques[c].update(set(map(str, df[c].to_pandas().unique())) if hasattr(df[c], "to_pandas") else set(map(str, df[c].unique())))
            except Exception:
                pass

    # ===== 主讀取回圈 =====
    buf, n = [], 0
    for line in tqdm(_iter_lines(paths), desc=("讀取中" if not QUIET else None), unit="line", disable=QUIET):
        rec = parse_log_line(line)
        if rec:
            buf.append(rec); n += 1
            if n >= CHUNK_LINES:
                _process_df(buf)
                buf, n = [], 0
    if buf:
        _process_df(buf)

    if rawdict_fp:
        rawdict_fp.close()

    if not QUIET:
        print(Fore.GREEN + f"✅ 清洗完成：{clean_csv}（{tot_clean} 筆）")
        if sampled_csv and enable_sampling:
            print(Fore.GREEN + f"✅ 抽樣完成：{sampled_csv}（{tot_sample} 筆）")

    # ===== 產出/更新 manifest.json =====
    manifest_path = os.path.join(run_dir, "manifest.json")
    try:
        os.makedirs(run_dir, exist_ok=True)
        payload = {}
        if os.path.exists(manifest_path):
            with open(manifest_path, "r", encoding="utf-8") as f:
                payload = json.load(f)

        payload.setdefault("run_id", os.path.basename(run_dir))
        payload["root_dir"] = run_dir
        payload["clean"] = payload.get("clean", {})
        payload["clean"]["processed_csv"] = clean_csv
        if sampled_csv and enable_sampling and os.path.exists(sampled_csv):
            payload["clean"]["sampled_csv"] = sampled_csv
            payload["clean"]["mode"] = "preconfigured"
            payload["clean"]["active_clean_file"] = sampled_csv  # ✅ 啟用抽樣 → active 指向抽樣檔
        else:
            payload["clean"]["sampled_csv"] = payload["clean"].get("sampled_csv", "")
            payload["clean"]["mode"] = payload["clean"].get("mode", "none")
            payload["clean"]["active_clean_file"] = clean_csv     # ✅ 未抽樣 → active 指向清洗檔

        _atomic_write_json(manifest_path, payload)
        if not QUIET:
            print(Style.BRIGHT + Fore.GREEN + f"🧭 manifest 已更新：{manifest_path}")
    except Exception as e:
        print(Fore.YELLOW + f"⚠️ manifest 寫入失敗：{e}")

    return clean_csv
