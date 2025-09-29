# -*- coding: utf-8 -*-
"""
log_cleaning.py
- 分塊流式清洗（TB 等級、防 OOM）
- 進度條（tqdm）、色彩輸出（colorama）
- CLI 互動僅在 __main__；可用 QUIET/參數靜默執行（供 pipeline/UI 呼叫）
- 主資料：移除 raw_log；保留 idseq 並置第一欄
- 即時雙檔輸出（未抽樣 + 抽樣）
- 唯一值清單（json/txt）
"""
import os, re, gzip, json, time, logging
import pandas as pd, numpy as np
from tqdm import tqdm
from colorama import init, Fore, Style
from .utils import check_and_flush

# 可靜默的全域旗標（預設 False；由外部設定 True 可關閉所有輸出與互動）
QUIET = False

# 可選：GUI；不可用時自動退化為 CLI 輸入（在 QUIET 模式下不啟用 GUI）
try:
    import tkinter as tk
    from tkinter import filedialog
    TK_OK = True
except Exception:
    TK_OK = False

# 可選：自動偵測編碼
try:
    import chardet
    HAS_CHARDET = True
except Exception:
    HAS_CHARDET = False

init(autoreset=True)
logging.basicConfig(filename="log_cleaning_error.log", level=logging.ERROR,
                    format="%(asctime)s - %(levelname)s - %(message)s")

# =====================[ CONFIG ]=====================
CHUNK_LINES = 50_000
DEFAULT_SAMPLING_SEED = 42
DEFAULT_RANDOM_RATIO = 1.0
DEFAULT_WRITE_RAWDICT = False   # 如需 idseq→raw_log 外掛字典，設 True（壓縮 JSONL）
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

# -------------------- 工具 --------------------
def _get_tk_root():
    root = tk.Tk(); root.withdraw(); return root

def _select_files_interactive():
    # 僅在非 QUIET 才可能啟動 GUI/CLI 輸入
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
    # QUIET 模式走到這代表外部未提供 paths
    raise ValueError("QUIET 模式需由呼叫端提供 paths 參數。")

def _select_save_path_interactive(prompt, default_name):
    # 僅在非 QUIET 才可能啟動 GUI/CLI 輸入
    if (not QUIET) and TK_OK:
        _get_tk_root()
        p = filedialog.asksaveasfilename(title=prompt, defaultextension=".csv",
                                         initialfile=default_name, filetypes=[("CSV files","*.csv")])
        if p: return p
    if not QUIET:
        s = input(f"{prompt}（預設 {default_name}）：").strip()
        return s if s else default_name
    # QUIET 模式：直接用預設檔名（相對或絕對皆可）
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
            "idseq": kv.get("idseq", ""),  # 字串存放，避免整數溢位
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
            "raw_line": line.strip()  # 僅供外掛字典使用
        }
    except Exception as e:
        logging.error(f"解析失敗：{e}")
        return None

def _finalize_datetime(df):
    # 優先 date+time；否則 itime(epoch 秒)
    if "date" in df.columns and "time" in df.columns:
        df["datetime"] = pd.to_datetime(df["date"].astype(str) + " " + df["time"].astype(str), errors="coerce")
        df.drop(columns=["date","time"], inplace=True, errors="ignore")
    if "datetime" not in df.columns or not pd.api.types.is_datetime64_any_dtype(df["datetime"]):
        if "itime" in df.columns:
            df["datetime"] = pd.to_datetime(pd.to_numeric(df["itime"], errors="coerce"), unit="s", errors="coerce")
    df.drop(columns=["itime"], inplace=True, errors="ignore")
    return df

def _set_is_attack(df):
    if "crscore" in df.columns:
        df["is_attack"] = (pd.to_numeric(df["crscore"], errors="coerce").fillna(0).astype(int) > 0).astype(int)
    elif "crlevel" in df.columns:
        safe = {"0","unknown","none",""}
        df["is_attack"] = (~df["crlevel"].astype(str).str.lower().isin(safe)).astype(int)
    else:
        df["is_attack"] = 0
    return df

def _reorder_keep_only(df):
    for col in COLUMN_ORDER:
        if col not in df.columns:
            df[col] = "" if col != "datetime" else pd.NaT
    return df[COLUMN_ORDER]

def _choose_mode_interactive():
    print(f"{Fore.CYAN}請選擇操作模式：")
    print("  1. 預先設定抽樣（處理時同步輸出未抽樣+抽樣）")
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

def _detect_encoding_safe(path):
    enc = _detect_encoding(path)
    return enc

def _write_rawdict_open():
    if not DEFAULT_WRITE_RAWDICT: return None
    return gzip.open(RAWDICT_GZ_PATH, "at", encoding="utf-8")

def _write_rawdict_line(gzfp, rec):
    if gzfp is None: return
    rid = rec.get("idseq","")
    raw = rec.get("raw_line","")
    if rid and raw:
        gzfp.write(json.dumps({"idseq": rid, "raw": raw}, ensure_ascii=False) + "\n")

# -------------------- 主程序（可靜默） --------------------
def clean_logs(
    quiet: bool = None,
    mode: str = None,
    paths: list = None,
    clean_csv: str = "processed_logs.csv",
    sampled_csv: str = None,
    sampling_cfg: dict = None
):
    """
    清洗主函式（供 pipeline/UI 呼叫）：
      - quiet=True：完全靜默，不進行任何互動印出；需提供 paths；其它參數可省略用預設
      - quiet=False 或 None：如未提供參數，進入互動式問答（GUI/CLI）
    回傳：clean_csv 的實際輸出路徑
    """
    global QUIET
    if quiet is not None:
        QUIET = bool(quiet)

    if not QUIET:
        print(f"{Fore.WHITE}{Style.BRIGHT}==== 清洗 / 標準化（流式） ====")

    # 互動或靜默模式下的參數準備
    if mode is None:
        mode = _choose_mode_interactive() if not QUIET else "3"
    if paths is None:
        paths = _select_files_interactive() if not QUIET else None
    if QUIET and not paths:
        raise ValueError("QUIET 模式需提供 paths（list[str]）。")

    # 輸出檔名（靜默則使用預設）
    if sampled_csv is None and mode in ("1","2"):  # 需要抽樣輸出
        sampled_csv = "sampled_logs.csv"

    if not QUIET:
        clean_csv = _select_save_path_interactive("選擇清洗後（未抽樣）CSV 儲存位置", clean_csv)
        if mode in ("1","2"):
            sampled_csv = _select_save_path_interactive("選擇抽樣後 CSV 儲存位置", sampled_csv or "sampled_logs.csv")

    # 抽樣設定
    if sampling_cfg is None:
        if mode in ("1","2"):
            sampling_cfg = _choose_sampling_interactive() if not QUIET else {
                "method": "1", "ratio": DEFAULT_RANDOM_RATIO,
                "label_col": "is_attack", "seed": DEFAULT_SAMPLING_SEED
            }
        else:
            sampling_cfg = {"method":"1","ratio":1.0,"label_col":"is_attack","seed":DEFAULT_SAMPLING_SEED}

    method_map = {"1":"random","2":"balanced","3":"systematic","4":"custom"}
    method = method_map.get(sampling_cfg.get("method","1"), "random")
    ratio = float(sampling_cfg.get("ratio", DEFAULT_RANDOM_RATIO))
    label_col = sampling_cfg.get("label_col","is_attack")
    seed = int(sampling_cfg.get("seed", DEFAULT_SAMPLING_SEED))
    custom_counts = sampling_cfg.get("custom_counts", None)
    np.random.seed(seed)

    uniques = {c: set() for c in UNIQUE_COLS}
    first_clean, first_sample = True, True
    tot_clean, tot_sample = 0, 0
    rawdict_fp = _write_rawdict_open()

    def _process_df(df):
        nonlocal first_clean, first_sample, tot_clean, tot_sample
        # 完成時間、標籤、去重、重排
        df = _finalize_datetime(df)
        df = _set_is_attack(df)
        df.drop_duplicates(inplace=True)
        df = _reorder_keep_only(df)
        # [1] 寫清洗檔
        df.to_csv(clean_csv, mode="w" if first_clean else "a",
                  header=first_clean, index=False, encoding="utf-8")
        first_clean = False
        tot_clean += len(df)
        # [2] 記憶體檢查與 flush
        check_and_flush("log_cleaning", df)
        # [3] 寫抽樣檔（視模式）
        if sampled_csv:
            if method == "random":
                sdf = df.sample(frac=min(max(ratio,0.0),1.0), random_state=seed) if ratio < 1.0 else df
            elif method == "balanced":
                if label_col not in df.columns:
                    if not QUIET:
                        print(f"{Fore.RED}❌ 找不到平衡欄位 {label_col}，本塊跳過抽樣")
                    sdf = df.head(0)
                else:
                    vc = df[label_col].value_counts()
                    m = vc.min() if len(vc)>0 else 0
                    parts = []
                    for _, g in df.groupby(label_col):
                        n = min(m, len(g))
                        if n>0:
                            parts.append(g.sample(n=n, random_state=seed, replace=(n>len(g))))
                    sdf = pd.concat(parts).sample(frac=1.0, random_state=seed) if parts else df.head(0)
            elif method == "systematic":
                sdf = df.iloc[::max(int(1.0/ratio),1)] if ratio < 1.0 and ratio>0 else df
            else:
                if (custom_counts is None) or (label_col not in df.columns):
                    if not QUIET:
                        print(f"{Fore.RED}❌ custom 未正確設定，跳過抽樣")
                    sdf = df.head(0)
                else:
                    parts = []
                    for k, n in custom_counts.items():
                        g = df[df[label_col].astype(str) == str(k)]
                        if len(g)==0: continue
                        take = min(int(n), len(g))
                        parts.append(g.sample(n=take, random_state=seed, replace=(take>len(g))))
                    sdf = pd.concat(parts).sample(frac=1.0, random_state=seed) if parts else df.head(0)
            sdf.to_csv(sampled_csv, mode="w" if first_sample else "a",
                       header=first_sample, index=False, encoding="utf-8")
            first_sample = False
            tot_sample += len(sdf)

    for path in paths:
        opener = gzip.open if path.endswith(".gz") else open
        enc = _detect_encoding_safe(path)
        try:
            with opener(path, "rt", encoding=enc, errors="replace") as f:
                buf = []
                if not QUIET:
                    print(f"{Fore.MAGENTA}📁 處理檔案：{os.path.basename(path)}")
                for i, line in enumerate(tqdm(f, desc=os.path.basename(path) if not QUIET else None, unit="行", disable=QUIET)):
                    rec = parse_log_line(line)
                    if rec:
                        # 寫外掛字典（可選）
                        _write_rawdict_line(rawdict_fp, rec)
                        # 收集唯一值
                        for k in UNIQUE_COLS:
                            uniques[k].add(rec.get(k,"") or "unknown")
                        buf.append(rec)
                    if len(buf) >= CHUNK_LINES:
                        _process_df(pd.DataFrame(buf))
                        buf = []
                if buf:
                    _process_df(pd.DataFrame(buf))
        except Exception as e:
            logging.error(f"讀取失敗：{path} - {e}")
            if not QUIET:
                print(f"{Fore.RED}檔案讀取錯誤：{path}")

    # 唯一值清單
    uniq = {k: sorted(list(v)) for k,v in uniques.items()}
    with open("log_unique_values.json", "w", encoding="utf-8") as fj:
        json.dump(uniq, fj, ensure_ascii=False, indent=2)
    with open("log_unique_values.txt", "w", encoding="utf-8") as ft:
        for k in uniq:
            ft.write(f"{k}: {', '.join(uniq[k])}\n")

    if rawdict_fp is not None:
        rawdict_fp.close()
        if not QUIET:
            print(f"{Fore.GREEN}✅ 已輸出 idseq→raw_log 字典：{RAWDICT_GZ_PATH}")

    if not QUIET:
        print(f"{Fore.GREEN}✅ 清洗完成：{clean_csv}（{tot_clean}）")
        if sampled_csv:
            print(f"{Fore.GREEN}✅ 抽樣完成：{sampled_csv}（{tot_sample}）")
    return clean_csv

def main():
    # 僅當使用者直接執行本檔，才進入互動式
    clean_logs(quiet=False)

if __name__ == "__main__":
    main()
