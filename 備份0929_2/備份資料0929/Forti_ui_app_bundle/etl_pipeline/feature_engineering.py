# -*- coding: utf-8 -*-
"""
feature_engineering.py
職責：
- 在映射完成的 CSV 上，追加「學術上常見且有效」的五大類特徵（資安流量分析）
- 模組化、可開關；預設啟用成本低的子集，高成本（時間窗/Top-K）預設關閉
- TB 級流式處理、tqdm 進度條、colorama 色彩、CLI 防笨
- 不使用 CMS；時間窗採輕量短窗，且預設關閉
- Top-K 使用離線字典查表（若無字典則自動跳過相關欄位）
- 新增：duration_zero_flag、rcvd_zero_flag、pkt_total_qbin、pkt_total_qrank

輸入：preprocessed_data.csv（由 log_mapping 輸出）
輸出：engineered_data.csv
"""

import os, json, math
import pandas as pd
import numpy as np
import hashlib
from collections import deque, Counter
from tqdm import tqdm
from colorama import Fore, Style, init as colorama_init
from .utils import check_and_flush

# ---- 初始化 ----
colorama_init(autoreset=True)

# ---- CONFIG：流程與效能 ----
CSV_CHUNK_SIZE = 100_000
DEFAULT_INPUT  = "preprocessed_data.csv"
DEFAULT_OUTPUT = "engineered_data.csv"

# 個別功能開關（低成本者預設開；中高成本預設關）
ENABLE_TRAFFIC_STATS    = True   # 1. 流量統計（低成本）
ENABLE_PROTO_PORT_FEATS = True   # 2. 協定/端口（低成本）
ENABLE_WINDOWED_FEATS   = False  # 3. 時間窗口（中成本；輕量短窗）
ENABLE_RELATIONAL_BASE  = True   # 4a. 關係（基礎：聯合類別對）
ENABLE_RELATIONAL_TOPK  = False  # 4b. 關係（進階：Top-K 查表）
ENABLE_ANOMALY_INDIC    = True   # 5. 異常指標（低成本）
ENCODE_ENGINEERED_CATS  = True   # 6.對工程後類別欄位做最終數值化

# 3. 時間窗口設定（僅在 ENABLE_WINDOWED_FEATS=True 時生效）
WINDOW_MINUTES = 5  # 短窗（分）
WINDOW_RATE_FLAGS = [0.90, 0.99]  # 對 log1p 計數計分位切旗標（本檔分塊內估計）

# 4b. Top-K 查表字典（可留空；不存在時自動跳過）
TOPK_SRC_PORT_JSON = "topk_srcip_dstport.json"  # 例：{"1.2.3.4":[80,443,22,...], ...}
TOPK_PAIR_JSON     = "topk_srcip_dstip.json"    # 例：{"1.2.3.4":["8.8.8.8","1.1.1.1",...], ...}
GLOBAL_HOT_PORTS   = {80,443,22,25,110,143,993,995,3306,3389,445,23}  # 可擴充

# 5. bucket 映射
_BUCKET_MAP = {"unknown":0, "well_known":1, "registered":2, "dynamic":3}

# ---- 共用：欄位 ----
CORE_ORDER = [
    "idseq", "datetime", "subtype",
    "srcip", "srcport", "srcintf",
    "dstip", "dstport", "dstintf",
    "action", "sentpkt", "rcvdpkt",
    "duration", "service", "devtype", "level",
    "crscore", "crlevel", "is_attack"
]
# 工程新增欄位會附加在核心之後（不丟失其它既有欄位）
def _reorder_append(df: pd.DataFrame) -> pd.DataFrame:
    for c in CORE_ORDER:
        if c not in df.columns:
            df[c] = "" if c != "datetime" else pd.NaT
    rest = [c for c in df.columns if c not in CORE_ORDER]
    return df[CORE_ORDER + rest]

# ---- 工具 ----
def _ask_path(prompt, default_path):
    p = input(Fore.CYAN + f"{prompt}（預設 {default_path}）：").strip()
    return p if p else default_path

def _to_int(series, default=0):
    return pd.to_numeric(series, errors="coerce").fillna(default).astype("int64")

def _to_float(series, default=0.0):
    return pd.to_numeric(series, errors="coerce").fillna(default).astype("float64")

def _load_json_if_exists(path):
    if path and os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            print(Fore.YELLOW + f"⚠️ 無法讀取 Top-K 字典：{path}")
    return None

def _stable_hash32(text: str) -> int:
    """對字串做穩定 32-bit 正整數雜湊（跨執行環境一致）。"""
    h = hashlib.md5(text.encode("utf-8", errors="ignore")).hexdigest()
    return int(h[:8], 16)  # 0 ~ 2^32-1

def _safe_div(numer, denom):
    """逐元素安全除法：denom>0 才做除法，否則回傳 0.0"""
    return (numer / denom).where(denom > 0, 0.0)

# ======================
# 1) 流量統計特徵（低成本）
# ======================
def add_traffic_stats(df: pd.DataFrame) -> pd.DataFrame:
    # 來源資料常見欄位：sentpkt/rcvdpkt/duration；統一轉型
    for c in ["sentpkt","rcvdpkt","duration"]:
        if c in df.columns:
            df[c] = _to_float(df[c])

    sent = df.get("sentpkt", pd.Series(0.0, index=df.index))
    rcvd = df.get("rcvdpkt", pd.Series(0.0, index=df.index))
    dur  = df.get("duration", pd.Series(0.0, index=df.index))

    total = sent + rcvd
    df["pkt_total"] = total
    df["pkt_ratio"] = _safe_div(sent, rcvd)
    df["pkt_rate"]  = _safe_div(total, dur)
    df["sent_rate"] = _safe_div(sent, dur)
    df["rcvd_rate"] = _safe_div(rcvd, dur)

    # 簡易「封包間隔」替代（若有 per-event 時長，這裡用 1/dur 作為 proxy）
    df["inv_duration"] = _safe_div(1.0, dur)

    # 0/1 旗標
    df["duration_zero_flag"] = (dur == 0).astype("int8")
    df["rcvd_zero_flag"]     = (rcvd == 0).astype("int8")

    # 分布百分位：以本 chunk 內的 pkt_total 做粗估（避免全域統計成本）
    q = total.quantile([0.25,0.5,0.75,0.90]) if len(total) else pd.Series([0,0,0,0], index=[.25,.5,.75,.9])
    p25,p50,p75,p90 = q.get(0.25,0.0), q.get(0.5,0.0), q.get(0.75,0.0), q.get(0.9,0.0)
    df["pkt_total_pctl25"] = (total >= p25).astype("int8")
    df["pkt_total_pctl50"] = (total >= p50).astype("int8")
    df["pkt_total_pctl75"] = (total >= p75).astype("int8")
    df["pkt_total_pctl90"] = (total >= p90).astype("int8")

    # 互斥四分位桶與百分位排名
    qbin = pd.Series(0, index=df.index, dtype="int8")
    qbin = qbin.where(total < p25, 1)
    qbin = qbin.where(total < p50, 2)
    qbin = qbin.where(total < p75, 3)
    df["pkt_total_qbin"] = qbin.astype("int8")
    df["pkt_total_qrank"] = total.rank(pct=True)
    return df

# ==================================
# 2) 協定與端口特徵（低成本，查表）
# ==================================
def add_proto_port_feats(df: pd.DataFrame) -> pd.DataFrame:
    # 端口分桶
    if "dstport" in df.columns:
        port = _to_int(df["dstport"])
        cat = pd.Series("unknown", index=df.index)
        cat = cat.mask((port>0) & (port<=1023), "well_known")
        cat = cat.mask((port>=1024) & (port<=49151), "registered")
        cat = cat.mask((port>=49152) & (port<=65535), "dynamic")
        df["dstport_bucket"] = cat.astype("category")

        # 常見/熱門端口旗標
        df["is_common_port"] = port.isin(list(GLOBAL_HOT_PORTS)).astype("int8")

    # 協定 + 端口（若有 proto，以 proto；否則以 service）
    proto_col = "proto" if "proto" in df.columns else ("service" if "service" in df.columns else None)
    if proto_col and "dstport" in df.columns:
        df["proto_port"] = df[proto_col].astype(str).str.lower() + "|" + df["dstport"].astype(str)
    return df

# ==================================================
# 3) 時間窗口特徵（可選，輕量短窗；預設關閉）
# ==================================================
def add_windowed_feats(df: pd.DataFrame, state):
    """
    以 O(1)/列 的方式計算短窗計數：
      - state: {
          "window": deque([(minute, c_src, c_dst, c_pair), ...]),
          "agg_src": Counter(), "agg_dst": Counter(), "agg_pair": Counter()
        }
    """
    if "datetime" not in df.columns:
        df["datetime"] = pd.NaT
    if not pd.api.types.is_datetime64_any_dtype(df["datetime"]):
        df["datetime"] = pd.to_datetime(df["datetime"], errors="coerce")

    # 初始化跨 chunk 狀態
    window = state.setdefault("window", deque())
    agg_src = state.setdefault("agg_src", Counter())
    agg_dst = state.setdefault("agg_dst", Counter())
    agg_pair = state.setdefault("agg_pair", Counter())

    # 準備輸出欄位
    n = len(df)
    df["cnt_5m_srcip"] = 0
    df["cnt_5m_dstip"] = 0
    df["cnt_5m_pair"]  = 0

    # 為了效率，取出必要欄位為陣列
    dt_vals = df["datetime"].values
    src_vals = df["srcip"].astype(str).values if "srcip" in df.columns else np.array([""]*n, dtype=object)
    dst_vals = df["dstip"].astype(str).values if "dstip" in df.columns else np.array([""]*n, dtype=object)

    # 快速掃描
    for i in range(n):
        ts = dt_vals[i]
        mk = pd.Timestamp(ts).floor("min") if not pd.isna(ts) else None
        if mk is None:
            continue

        # 視窗滾動：移除過舊分鐘並從聚合 Counter 扣除
        while window and (mk - window[0][0]).total_seconds() > WINDOW_MINUTES * 60:
            old_minute, csrc_old, cdst_old, cpair_old = window.popleft()
            agg_src.subtract(csrc_old)
            agg_dst.subtract(cdst_old)
            agg_pair.subtract(cpair_old)
            # 清理 <=0 的 key（Counter subtract 可能留下 0 或負值）
            for C in (agg_src, agg_dst, agg_pair):
                to_del = [k for k, v in C.items() if v <= 0]
                for k in to_del:
                    del C[k]

        # 若最後一個桶不是當前分鐘，補一個新桶
        if not window or window[-1][0] != mk:
            window.append((mk, Counter(), Counter(), Counter()))
        _, csrc, cdst, cpair = window[-1]

        s = src_vals[i]; d = dst_vals[i]; pair = f"{s}>{d}"

        # 讀取當前窗口的聚合值（不含本列）
        df.iat[i, df.columns.get_loc("cnt_5m_srcip")] = agg_src.get(s, 0)
        df.iat[i, df.columns.get_loc("cnt_5m_dstip")] = agg_dst.get(d, 0)
        df.iat[i, df.columns.get_loc("cnt_5m_pair")]  = agg_pair.get(pair, 0)

        # 將本列加入桶與聚合 Counter
        csrc[s]  += 1; agg_src[s]  += 1
        cdst[d]  += 1; agg_dst[d]  += 1
        cpair[pair] += 1; agg_pair[pair] += 1

    # 將計數做 log1p 與分位旗標（以本 chunk 估計）
    for c in ["cnt_5m_srcip","cnt_5m_dstip","cnt_5m_pair"]:
        x = pd.to_numeric(df[c], errors="coerce").fillna(0.0)
        df[c + "_log1p"] = np.log1p(x)
        if len(x):
            qs = x.quantile(WINDOW_RATE_FLAGS)
            for qv in WINDOW_RATE_FLAGS:
                df[f"{c}_ge_p{int(qv*100)}"] = (x >= float(qs.loc[qv])).astype("int8")
        else:
            for qv in WINDOW_RATE_FLAGS:
                df[f"{c}_ge_p{int(qv*100)}"] = 0
    return df

# ==========================================
# 4) 關係型特徵（基礎＋Top-K；Top-K 預設關）
# ==========================================
def add_relational_basic(df: pd.DataFrame) -> pd.DataFrame:
    # 聯合類別（使用映射後的整數或字串皆可）
    if "subtype" in df.columns and "action" in df.columns:
        df["sub_action"] = df["subtype"].astype(str) + "|" + df["action"].astype(str)
    if "service" in df.columns and "action" in df.columns:
        df["svc_action"] = df["service"].astype(str).str.lower() + "|" + df["action"].astype(str)
    return df

def add_relational_topk(df: pd.DataFrame, topk_src_port: dict, topk_pair: dict) -> pd.DataFrame:
    # 若無字典，直接跳過（安全）
    if topk_src_port:
        # (srcip, dstport) 是否在 srcip 的 Top-K 列表內；另給簡單排名分桶
        sp = []
        for src, ports in topk_src_port.items():
            try:
                sp.append((src, [int(p) for p in ports]))
            except Exception:
                sp.append((src, []))
        sp_dict = dict(sp)

        if "srcip" in df.columns and "dstport" in df.columns:
            src = df["srcip"].astype(str)
            dpt = _to_int(df["dstport"])
            df["is_topk_src_port"] = [
                1 if (s in sp_dict and int(p) in sp_dict[s]) else 0
                for s, p in zip(src, dpt)
            ]
            # 簡單排名分桶（1,2,3,>3,none=0）
            def _rank_bin(s, p):
                lst = sp_dict.get(s)
                if not lst: return 0
                try:
                    r = lst.index(int(p)) + 1
                except ValueError:
                    return 0
                return r if r <= 3 else 4
            df["rank_src_port_bin"] = [ _rank_bin(s, p) for s, p in zip(src, dpt) ]

    if topk_pair:
        if "srcip" in df.columns and "dstip" in df.columns:
            src = df["srcip"].astype(str); dst = df["dstip"].astype(str)
            tp = {k: set(v) for k, v in topk_pair.items()}
            df["is_topk_pair"] = [1 if (s in tp and d in tp[s]) else 0 for s, d in zip(src, dst)]

    # 全域熱門埠旗標（已在 proto/port 特徵提供 is_common_port；這裡不重覆）
    return df

# ======================
# 5) 異常行為指標（低成本）
# ======================
def add_anomaly_indicators(df: pd.DataFrame) -> pd.DataFrame:
    # 以 pkt_rate 做簡易 Z-score（就地標準化於本 chunk，降低計算成本）
    if "pkt_rate" not in df.columns:
        # 若尚未計算（可能關閉了流量統計），用 sent/rcv/ dur 先造
        for c in ["sentpkt","rcvdpkt","duration"]:
            if c in df.columns: df[c] = _to_float(df[c])
        total = df.get("sentpkt",0.0) + df.get("rcvdpkt",0.0)
        df["pkt_rate"] = total / (_to_float(df.get("duration",0.0)) + 1.0)

    x = _to_float(df["pkt_rate"])
    mu = float(x.mean()) if len(x) else 0.0
    sd = float(x.std(ddof=0)) if len(x) else 1.0
    sd = sd if sd > 0 else 1.0
    z = (x - mu) / sd
    df["pkt_rate_z"] = z
    df["pkt_rate_outlier"] = (z.abs() >= 3.0).astype("int8")

    # 簡易 burst 指標：當前 sent_rate 是否高於本 chunk p99
    if "sent_rate" in df.columns:
        qs = _to_float(df["sent_rate"]).quantile(0.99) if len(df) else 0.0
        df["burst_sent_p99"] = (_to_float(df["sent_rate"]) >= qs).astype("int8")
    return df
# ======================
# 6) 工程後類別欄位數值化
# ======================
def encode_engineered_categoricals(df: pd.DataFrame) -> pd.DataFrame:
    """
    對工程新增的類別欄位做數值化：
      - dstport_bucket: 固定映射
      - proto_port / sub_action / svc_action: 穩定雜湊（32-bit）
    """
    # 1) dstport_bucket → int
    if "dstport_bucket" in df.columns and not pd.api.types.is_numeric_dtype(df["dstport_bucket"]):
        s = df["dstport_bucket"].astype(str).str.lower().str.strip().fillna("unknown")
        df["dstport_bucket"] = s.map(lambda x: _BUCKET_MAP.get(x, 0)).astype("int32", errors="ignore")

    # 2) 其餘組合類別 → 穩定 hash
    for col in ("proto_port", "sub_action", "svc_action"):
        if col in df.columns and not pd.api.types.is_numeric_dtype(df[col]):
            s = df[col].astype(str).fillna("")
            df[col + "_code"] = s.map(_stable_hash32).astype("uint32")
            # 若要直接覆蓋原欄位，改成：df[col] = s.map(_stable_hash32).astype("uint32")
    return df
# ---- 主流程 ----
def main():
    print(Style.BRIGHT + "==== 特徵工程（feature_engineering）====")
    in_csv  = _ask_path("輸入檔（preprocessed_data.csv）", DEFAULT_INPUT)
    out_csv = _ask_path("輸出檔（engineered_data.csv）", DEFAULT_OUTPUT)

    if not os.path.exists(in_csv):
        print(Fore.RED + f"❌ 找不到輸入檔：{in_csv}")
        return

    # 嘗試載入 Top-K 字典（若不存在自動為 None）
    topk_src_port = _load_json_if_exists(TOPK_SRC_PORT_JSON)
    topk_pair     = _load_json_if_exists(TOPK_PAIR_JSON)

    first = True
    total = 0
    state = {}  # 給時間窗特徵跨 chunk 的小狀態

    for chunk in tqdm(pd.read_csv(in_csv, chunksize=CSV_CHUNK_SIZE, encoding="utf-8"),
                      desc="分塊處理", unit="chunk"):
        # 時間欄位型別保險
        if "datetime" in chunk.columns and not pd.api.types.is_datetime64_any_dtype(chunk["datetime"]):
            chunk["datetime"] = pd.to_datetime(chunk["datetime"], errors="coerce")

        # 1) 流量統計
        if ENABLE_TRAFFIC_STATS:
            chunk = add_traffic_stats(chunk)

        # 2) 協定/端口
        if ENABLE_PROTO_PORT_FEATS:
            chunk = add_proto_port_feats(chunk)

        # 3) 時間窗口（可選）
        if ENABLE_WINDOWED_FEATS:
            chunk = add_windowed_feats(chunk, state)

        # 4) 關係特徵
        if ENABLE_RELATIONAL_BASE:
            chunk = add_relational_basic(chunk)
        if ENABLE_RELATIONAL_TOPK:
            chunk = add_relational_topk(chunk, topk_src_port, topk_pair)

        # 5) 異常指標
        if ENABLE_ANOMALY_INDIC:
            chunk = add_anomaly_indicators(chunk)

        # 6) 工程後類別欄位數值化（若有）
        if ENCODE_ENGINEERED_CATS:
            chunk = encode_engineered_categoricals(chunk)

        # 7) 檢查記憶體並 flush（若超過 75% 使用率）
        check_and_flush("feature_engineering", chunk)
        chunk.to_csv(output_csv, mode="w" if first else "a",
                    header=first, index=False, encoding="utf-8")
        first = False
        
        # 排序附加（核心在前，新特徵附在後）
        chunk = _reorder_append(chunk)
        chunk.drop_duplicates(inplace=True)

        # 寫出
        chunk.to_csv(out_csv, mode="w" if first else "a", header=first, index=False, encoding="utf-8")
        first = False
        total += len(chunk)

    print(Fore.GREEN + f"✅ 完成：{out_csv}（{total} 筆）")

if __name__ == "__main__":
    main()
