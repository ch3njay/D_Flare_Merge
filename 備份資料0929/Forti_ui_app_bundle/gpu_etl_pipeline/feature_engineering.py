# -*- coding: utf-8 -*-
"""
feature_engineering.py（GPU 版，強化 v3.1）
- 分塊處理、append 輸出（維持）
- 兩階段全域統計（Top-K）/ approx_mode（維持）
- 狀態上限保護（MAX_STATE_SIZE/PRUNE_FACTOR）（維持）
- **修正：速率/倒數 off-by-one（移除 +1 偽平滑，改為安全除法 + 旗標）**
- **新增：duration_zero_flag / rcvd_zero_flag**
- **新增：pkt_total_qbin（互斥四分位桶）與 pkt_total_qrank（0~1）**
- **改良：pkt_rate_z 以 Robust Z（Median/MAD）計算**
- **擴充：常見埠清單（含 53/123/1521/8080/…），修正 is_common_port 可用性**
- **遵循：raw_log 永遠置底**
- 加上相容匯入層：package 或單檔皆可執行（維持）
"""
import os
import sys
import json
import hashlib
import math
from collections import deque, Counter, defaultdict
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
    import cupy as xp
else:
    import pandas as xdf  # type: ignore
    import numpy as xp    # type: ignore

colorama_init(autoreset=True)

# ---- CONFIG（可被 pipeline/參數覆寫）----
CSV_CHUNK_SIZE = 100_000
DEFAULT_INPUT  = "preprocessed_data.csv"
DEFAULT_OUTPUT = "engineered_data.csv"

# 個別功能開關
ENABLE_TRAFFIC_STATS    = True
ENABLE_PROTO_PORT_FEATS = True
ENABLE_WINDOWED_FEATS   = False
ENABLE_RELATIONAL_BASE  = True
ENABLE_RELATIONAL_TOPK  = False
ENABLE_ANOMALY_INDIC    = True
ENCODE_ENGINEERED_CATS  = True

# 窗口/Top-K/狀態
WINDOW_MINUTES = 5
WINDOW_RATE_FLAGS = [0.90, 0.99]
MAX_STATE_SIZE = 200_000   # 狀態上限
PRUNE_FACTOR   = 0.5       # 超限修剪比例

TOPK_K = 20
TOPK_SRC_PORT_JSON = "topk_srcip_dstport.json"
TOPK_PAIR_JSON     = "topk_srcip_dstip.json"

# 擴充常見埠清單（含 DNS/Oracle/HTTP-alt/NTP/…）
GLOBAL_HOT_PORTS   = {
    20,21,22,23,25,53,67,68,69,80,110,123,135,137,138,139,143,161,162,
    389,443,445,465,587,993,995,1433,1521,2049,3128,3306,3389,5432,5900,
    6379,8080,8443,853,5060,5061
}
_BUCKET_MAP = {"unknown":0, "well_known":1, "registered":2, "dynamic":3}

CORE_ORDER = [
    "idseq", "datetime", "subtype",
    "srcip", "srcport", "srcintf",
    "dstip", "dstport", "dstintf",
    "action", "sentpkt", "rcvdpkt",
    "duration", "service", "devtype", "level",
    "crscore", "crlevel", "is_attack"
]

# === 等長 Series 產生器（不論 pandas / cuDF） ===
def _series_full_like(series, fill, dtype=None):
    n = int(len(series)) if hasattr(series, "__len__") else 0
    if _HAS_CUDF:
        return xdf.Series([fill] * n, dtype=dtype)
    else:
        idx = series.index if hasattr(series, "index") else None
        return pd.Series([fill] * n, index=idx, dtype=dtype)

def _reorder_append(df):
    # 補齊核心欄位
    for c in CORE_ORDER:
        if c not in df.columns:
            if c == "datetime":
                df[c] = xdf.NaT
            elif c in ("sentpkt","rcvdpkt","duration"):
                df[c] = 0
            else:
                df[c] = ""
    rest = [c for c in df.columns if c not in CORE_ORDER]
    # raw_log 永遠置底
    if "raw_log" in rest:
        rest = [c for c in rest if c != "raw_log"] + ["raw_log"]
    return df[CORE_ORDER + rest]

# === 安全的 float 轉型（失敗時等長補值） ===
def _to_float(series, default=0.0):
    # 1) 直接 astype
    try:
        return series.astype("float64")
    except Exception:
        pass
    # 2) 先轉字串再 astype
    try:
        return series.astype("str").astype("float64")
    except Exception:
        pass
    # 3) pandas 安全轉型（含 NaN→default），再回到 cuDF（若有）
    try:
        if _HAS_CUDF:
            ser = pd.to_numeric(series.to_pandas(), errors="coerce").fillna(default).astype("float64")
            return xdf.from_pandas(ser) if hasattr(xdf, "from_pandas") else xdf.Series(ser.values, dtype="float64")
        else:
            return pd.to_numeric(series, errors="coerce").fillna(default).astype("float64")
    except Exception:
        # 4) 仍失敗 → 等長預設值
        return _series_full_like(series, default, dtype="float64")

# === 安全的 int 轉型（失敗時等長補值） ===
def _to_int(series, default=0):
    # 1) 直接 astype
    try:
        return series.astype("int64")
    except Exception:
        pass
    # 2) 先轉字串再 astype
    try:
        return series.astype("str").astype("int64")
    except Exception:
        pass
    # 3) pandas 安全轉型（含 NaN→default），再回到 cuDF（若有）
    try:
        if _HAS_CUDF:
            ser = pd.to_numeric(series.to_pandas(), errors="coerce").fillna(default).astype("int64")
            return xdf.from_pandas(ser) if hasattr(xdf, "from_pandas") else xdf.Series(ser.values, dtype="int64")
        else:
            return pd.to_numeric(series, errors="coerce").fillna(default).astype("int64")
    except Exception:
        # 4) 仍失敗 → 等長預設值
        return _series_full_like(series, default, dtype="int64")

def _safe_div(numer, denom):
    """逐元素安全除法：denom>0 才做除法，否則回傳 0.0"""
    # pandas/cudf Series 皆支援 where
    return (numer / denom).where(denom > 0, 0.0)

def _stable_hash32(text: str) -> int:
    h = hashlib.md5(text.encode("utf-8", errors="ignore")).hexdigest()
    return int(h[:8], 16)

def _load_json_if_exists(path):
    if path and os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            print(Fore.YELLOW + f"⚠️ 無法讀取 Top-K 字典：{path}")
    return None


def _read_manifest(run_dir: str = None) -> dict:
    """嘗試讀取 run_dir/manifest.json；找不到時回傳空 dict。"""
    candidates = []
    if run_dir:
        candidates.append(os.path.join(run_dir, "manifest.json"))
    candidates += [
        os.path.abspath("./manifest.json"),
        os.path.join(os.getcwd(), "manifest.json"),
    ]
    for p in candidates:
        if os.path.exists(p):
            try:
                with open(p, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
    return {}

# ---- DateTime 解析設定（一次偵測，全程沿用）----
DATETIME_COL = "datetime"
PREFERRED_DT_FORMATS = [
    "%Y-%m-%d %H:%M:%S",      # 例：2024-11-22 11:49:55
    "%Y/%m/%d %H:%M:%S",      # 例：2024/11/22 11:49:55
    "%Y-%m-%dT%H:%M:%S",      # 例：2024-11-22T11:49:55
]

def _detect_dt_format(sample_strs):
    import re
    pats = {
        "%Y-%m-%d %H:%M:%S": re.compile(r"^\d{4}-\d{2}-\d{2}\s\d{2}:\d{2}:\d{2}$"),
        "%Y/%m/%d %H:%M:%S": re.compile(r"^\d{4}/\d{2}/\d{2}\s\d{2}:\d{2}:\d{2}$"),
        "%Y-%m-%dT%H:%M:%S": re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}$"),
    }
    counts = {k:0 for k in pats}
    for s in sample_strs:
        if not s: 
            continue
        for fmt, rgx in pats.items():
            if rgx.match(s):
                counts[fmt] += 1
                break
    return max(counts, key=counts.get) if max(counts.values()) > 0 else None

def normalize_datetime(df, state, col=DATETIME_COL):
    """
    以固定 format 高速解析；偵測不到才回退慢速 dateutil（抑制警告）。
    將偵測到的 format 存在 state["dt_fmt"]，下個 chunk 直接沿用。
    """
    import warnings
    if col not in df.columns:
        df[col] = xdf.NaT
        return df

    # 已是 datetime64 直接返回
    try:
        if str(df[col].dtype).startswith("datetime64"):
            return df
    except Exception:
        pass

    fmt = state.get("dt_fmt")
    s = df[col].astype("str").str.strip()

    # 首次：從抽樣與既定清單推斷 format
    if fmt is None:
        sample = (s.head(256).to_pandas().dropna().tolist() if _HAS_CUDF 
                  else s.head(256).dropna().tolist())
        # 先嘗試常見清單
        fmt = _detect_dt_format(sample)
        if fmt is None:
            for cand in PREFERRED_DT_FORMATS:
                # 嘗試用 cand 解析少量樣本；能大量成功就採用
                try:
                    parsed = pd.to_datetime(sample, format=cand, errors="coerce")
                    if parsed.notna().mean() >= 0.8:
                        fmt = cand
                        break
                except Exception:
                    continue
        state["dt_fmt"] = fmt  # 可能是 None

    # 1) 有固定格式 → 高速解析
    if fmt:
        try:
            if _HAS_CUDF:
                df[col] = xdf.to_datetime(s, format=fmt, errors="coerce")
            else:
                df[col] = pd.to_datetime(s, format=fmt, errors="coerce", cache=True)
            return df
        except Exception:
            pass

    # 2) 回退：不噴大量 UserWarning（慢速，但只在偵測失敗時用）
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        if _HAS_CUDF:
            df[col] = xdf.to_datetime(s, errors="coerce")
        else:
            df[col] = pd.to_datetime(s, errors="coerce", cache=True)
    return df


# 1) 流量統計特徵（修正 +1 問題，加入旗標/互斥四分位/排名）
def add_traffic_stats(df):
    """
    修正後版本：
    - 保留：pkt_total、pkt_ratio、pkt_rate、sent_rate、rcvd_rate、inv_duration
    - 新增/保留：duration_zero_flag、rcvd_zero_flag
    - 保留：pkt_total_pctl90（極值旗標）、pkt_total_qbin（互斥四分位）、pkt_total_qrank（0~1）
    - 已移除：pkt_total_pctl25、pkt_total_pctl50、pkt_total_pctl75（避免冗餘/常數欄）
    - 其餘邏輯完全沿用，不破壞原本流程與輸出風格
    """
    for c in ["sentpkt","rcvdpkt","duration"]:
        if c in df.columns:
            df[c] = _to_float(df[c])

    sent = df.get("sentpkt", 0.0)
    rcvd = df.get("rcvdpkt", 0.0)
    dur  = df.get("duration", 0.0)

    total = sent + rcvd
    df["pkt_total"] = total
    df["pkt_ratio"] = _safe_div(sent, rcvd)        # rcvd==0 → 0
    df["pkt_rate"]  = _safe_div(total, dur)        # dur==0 → 0
    df["sent_rate"] = _safe_div(sent, dur)
    df["rcvd_rate"] = _safe_div(rcvd, dur)
    df["inv_duration"] = _safe_div(1.0, dur)

    # 0/1 旗標
    df["duration_zero_flag"] = (dur == 0).astype("int8")
    df["rcvd_zero_flag"]     = (rcvd == 0).astype("int8")

    # 分位統計（保留 qbin / qrank；僅保留 pctl90 極值旗標）
    try:
        if len(df):
            q = xdf.Series(total).quantile([0.25, 0.50, 0.75, 0.90])
            q25, q50, q75, q90 = float(q[0.25]), float(q[0.50]), float(q[0.75]), float(q[0.90])

            # ✅ 僅保留極值旗標（高位分位更有異常代表性）
            df["pkt_total_pctl90"] = (total >= q90).astype("int8")

            # ✅ 互斥四分位桶（0~3）
            qbin = xdf.Series([0] * len(df), dtype="int8")
            qbin = qbin.where(total < q25, 1)
            qbin = qbin.where(total < q50, 2)
            qbin = qbin.where(total < q75, 3)
            df["pkt_total_qbin"] = qbin.astype("int8")

            # ✅ 百分位排名（0~1），平滑且對樞紐模型友好
            if _HAS_CUDF:
                df["pkt_total_qrank"] = pd.Series(total.to_pandas().rank(pct=True).values)
            else:
                df["pkt_total_qrank"] = total.rank(pct=True)

            # ❌ 已移除冗餘旗標以避免常數/空欄與多重共線
            # df["pkt_total_pctl25"] = (total >= q25).astype("int8")
            # df["pkt_total_pctl50"] = (total >= q50).astype("int8")
            # df["pkt_total_pctl75"] = (total >= q75).astype("int8")
    except Exception:
        # 分位計算容錯，不中斷主流程
        pass

    return df

# 2) 協定與端口特徵
def add_proto_port_feats(df):
    if "dstport" in df.columns:
        port = _to_int(df["dstport"])
        n = len(df)
        cat = xdf.Series(["unknown"] * n) if n else xdf.Series([])
        try:
            cat = cat.mask((port>0) & (port<=1023), "well_known")
            cat = cat.mask((port>=1024) & (port<=49151), "registered")
            cat = cat.mask((port>=49152) & (port<=65535), "dynamic")
        except Exception:
            pass
        df["dstport_bucket"] = cat

        try:
            df["is_common_port"] = port.isin(list(GLOBAL_HOT_PORTS)).astype("int8")
        except Exception:
            try:
                df["is_common_port"] = df["dstport"].astype("int64").isin(list(GLOBAL_HOT_PORTS)).astype("int8")
            except Exception:
                df["is_common_port"] = 0  # 落敗保護

    proto_col = "proto" if "proto" in df.columns else ("service" if "service" in df.columns else None)
    if proto_col and "dstport" in df.columns:
        df["proto_port"] = df[proto_col].astype("str").str.lower() + "|" + df["dstport"].astype("str")
    return df

# 3) 時間窗口特徵（含狀態上限）
def _prune_counter(counter: Counter, factor=PRUNE_FACTOR):
    if len(counter) <= MAX_STATE_SIZE:
        return
    k = int(len(counter) * factor)
    if k <= 0:
        return
    for key, _ in sorted(counter.items(), key=lambda kv: kv[1])[:k]:
        counter.pop(key, None)

def add_windowed_feats(df, state):
    if "datetime" not in df.columns:
        df["datetime"] = xdf.NaT
    else:
        # main() 已先正規化；若仍不是 datetime64，再保底轉一次
        if not str(df["datetime"].dtype).startswith("datetime64"):
            df = normalize_datetime(df, state, col="datetime")

    window = state.setdefault("window", deque())            # (minute_bucket, csrc, cdst, cpair)
    agg_src = state.setdefault("agg_src", Counter())
    agg_dst = state.setdefault("agg_dst", Counter())
    agg_pair = state.setdefault("agg_pair", Counter())

    n = len(df)
    df["cnt_5m_srcip"] = 0
    df["cnt_5m_dstip"] = 0
    df["cnt_5m_pair"]  = 0

    if _HAS_CUDF:
        dt_vals = df["datetime"].to_pandas().values
        src_vals = df["srcip"].astype("str").to_pandas().values if "srcip" in df.columns else [""]*n
        dst_vals = df["dstip"].astype("str").to_pandas().values if "dstip" in df.columns else [""]*n
    else:
        dt_vals = df["datetime"].values
        src_vals = df["srcip"].astype("str").values if "srcip" in df.columns else [""]*n
        dst_vals = df["dstip"].astype("str").values if "dstip" in df.columns else [""]*n

    out_src = [0]*n; out_dst = [0]*n; out_pair = [0]*n
    import pandas as _pdt
    for i in range(n):
        ts = dt_vals[i]
        mk = _pdt.Timestamp(ts).floor("min") if not _pdt.isna(ts) else None
        if mk is None:
            continue

        # 視窗滾動
        while window and (mk - window[0][0]).total_seconds() > WINDOW_MINUTES * 60:
            old_minute, csrc_old, cdst_old, cpair_old = window.popleft()
            agg_src.subtract(csrc_old); agg_dst.subtract(cdst_old); agg_pair.subtract(cpair_old)
            for C in (agg_src, agg_dst, agg_pair):
                to_del = [k for k, v in C.items() if v <= 0]
                for k in to_del: del C[k]

        # 新桶
        if not window or window[-1][0] != mk:
            window.append((mk, Counter(), Counter(), Counter()))
        _, csrc, cdst, cpair = window[-1]

        s = src_vals[i]; d = dst_vals[i]; pair = f"{s}>{d}"
        out_src[i]  = agg_src.get(s, 0)
        out_dst[i]  = agg_dst.get(d, 0)
        out_pair[i] = agg_pair.get(pair, 0)

        csrc[s]  += 1; agg_src[s]  += 1
        cdst[d]  += 1; agg_dst[d]  += 1
        cpair[pair] += 1; agg_pair[pair] += 1

        # 狀態上限保護
        if (len(agg_src) > MAX_STATE_SIZE) or (len(agg_dst) > MAX_STATE_SIZE) or (len(agg_pair) > MAX_STATE_SIZE):
            _prune_counter(agg_src); _prune_counter(agg_dst); _prune_counter(agg_pair)

    df["cnt_5m_srcip"] = out_src
    df["cnt_5m_dstip"] = out_dst
    df["cnt_5m_pair"]  = out_pair

    # log1p 與分位旗標
    for c in ["cnt_5m_srcip","cnt_5m_dstip","cnt_5m_pair"]:
        x = df[c].astype("float64")
        try:
            if _HAS_CUDF:
                df[c + "_log1p"] = x.to_pandas().map(lambda v: math.log1p(v))
            else:
                df[c + "_log1p"] = x.map(lambda v: math.log1p(v))
        except Exception:
            import numpy as _np
            df[c + "_log1p"] = _np.log1p(x.to_pandas()) if _HAS_CUDF else _np.log1p(x)

        try:
            qs = xdf.Series(x).quantile([0.90,0.99]) if len(df) else None
            if qs is not None:
                for qv in [0.90,0.99]:
                    df[f"{c}_ge_p{int(qv*100)}"] = (x >= float(qs[qv])).astype("int8")
        except Exception:
            pass
    return df

# 4) 關係型特徵
def add_relational_basic(df):
    if "subtype" in df.columns and "action" in df.columns:
        df["sub_action"] = df["subtype"].astype("str") + "|" + df["action"].astype("str")
    if "service" in df.columns and "action" in df.columns:
        df["svc_action"] = df["service"].astype("str") + "|" + df["action"].astype("str")
    return df

def add_relational_topk(df, topk_src_port: dict, topk_pair: dict):
    if topk_src_port and "srcip" in df.columns and "dstport" in df.columns:
        try:
            dpt = df["dstport"].astype("int64")
        except Exception:
            dpt = df["dstport"].astype("str").astype("int64")
        src = df["srcip"].astype("str")

        tp_src = {str(k): set(v) for k, v in topk_src_port.items()}
        df["is_topk_src_port"] = [
            1 if (str(s) in tp_src and int(p) in tp_src[str(s)]) else 0
            for s, p in zip(src.to_pandas() if _HAS_CUDF else src,
                            dpt.to_pandas() if _HAS_CUDF else dpt)
        ]

    if topk_pair and "srcip" in df.columns and "dstip" in df.columns:
        src = df["srcip"].astype("str")
        dst = df["dstip"].astype("str")
        tp_pair = {str(k): set(map(str, v)) for k, v in topk_pair.items()}
        df["is_topk_pair"] = [
            1 if (str(s) in tp_pair and str(d) in tp_pair[str(s)]) else 0
            for s, d in zip(src.to_pandas() if _HAS_CUDF else src,
                            dst.to_pandas() if _HAS_CUDF else dst)
        ]
    return df

# 5) 異常行為指標（改用 Robust Z）
def add_anomaly_indicators(df):
    for c in ["sentpkt","rcvdpkt","duration"]:
        if c in df.columns: df[c] = _to_float(df[c])
    if "pkt_rate" not in df.columns:
        total = df.get("sentpkt",0.0) + df.get("rcvdpkt",0.0)
        df["pkt_rate"] = _safe_div(total, df.get("duration",0.0))

    x = df["pkt_rate"].astype("float64")
    try:
        med = float(x.median()) if len(df) else 0.0
        mad = float((x - med).abs().median()) if len(df) else 0.0
    except Exception:
        xx = x.to_pandas() if _HAS_CUDF else x
        med = float(xx.median()) if len(xx) else 0.0
        mad = float((xx - med).abs().median()) if len(xx) else 0.0
    denom = 1.4826 * mad if mad > 0 else 1.0
    z = (x - med) / denom
    df["pkt_rate_z"] = z
    try:
        df["pkt_rate_outlier"] = (abs(z) >= 3.5).astype("int8")
    except Exception:
        df["pkt_rate_outlier"] = (abs(z) >= 3.5)

    if "sent_rate" in df.columns:
        try:
            qs = xdf.Series(df["sent_rate"].astype("float64")).quantile(0.99) if len(df) else 0.0
            df["burst_sent_p99"] = (df["sent_rate"].astype("float64") >= float(qs)).astype("int8")
        except Exception:
            df["burst_sent_p99"] = 0
    return df

# 6) 工程後類別欄位數值化
def encode_engineered_categoricals(df):
    if "dstport_bucket" in df.columns:
        s = df["dstport_bucket"].astype("str").str.lower().str.strip().fillna("unknown")
        mp = _BUCKET_MAP
        try:
            df["dstport_bucket"] = s.map(mp).fillna(0).astype("int32")
        except Exception:
            df["dstport_bucket"] = [mp.get(str(v), 0) for v in (s.to_pandas() if _HAS_CUDF else s)]

    for col in ("proto_port", "sub_action", "svc_action"):
        if col in df.columns:
            s = df[col].astype("str").fillna("")
            try:
                df[col + "_code"] = s.map(lambda x: _stable_hash32(str(x))).astype("uint32")
            except Exception:
                vals = (s.to_pandas() if _HAS_CUDF else s).astype(str).tolist()
                hashed = [ _stable_hash32(v) for v in vals ]
                if _HAS_CUDF:
                    df[col + "_code"] = xdf.Series(hashed, dtype="uint32")
                else:
                    df[col + "_code"] = hashed
    return df

# ===== 全域統計（兩階段）=====
def _collect_partials_for_topk(in_csv, chunksize, out_dir="parts"):
    os.makedirs(out_dir, exist_ok=True)
    src_port = defaultdict(Counter)
    pair_cnt = defaultdict(Counter)

    for chunk_pd in tqdm(pd.read_csv(in_csv, chunksize=chunksize, encoding="utf-8"),
                         desc="全域統計 Pass-1", unit="chunk"):
        df = chunk_pd
        if "srcip" in df.columns and "dstport" in df.columns:
            try:
                dstport_vals = pd.to_numeric(df["dstport"], errors="coerce").fillna(0).astype(int)
            except Exception:
                dstport_vals = df["dstport"].astype(str)
            for s, p in zip(df["srcip"].astype(str), dstport_vals):
                src_port[s][p] += 1

        if "srcip" in df.columns and "dstip" in df.columns:
            for s, d in zip(df["srcip"].astype(str), df["dstip"].astype(str)):
                pair_cnt[s][d] += 1

        # 狀態上限：按需落地+清空
        def _dump_and_reset(counter_map, fname):
            path = os.path.join(out_dir, fname)
            with open(path, "a", encoding="utf-8") as f:
                for k, ctr in counter_map.items():
                    for kk, vv in ctr.items():
                        f.write(f"{k}\t{kk}\t{vv}\n")
            counter_map.clear()

        total_keys = len(src_port) + len(pair_cnt)
        if total_keys > MAX_STATE_SIZE:
            _dump_and_reset(src_port, "src_port_parts.tsv")
            _dump_and_reset(pair_cnt, "pair_parts.tsv")

    # 最後落地
    if src_port:
        with open(os.path.join(out_dir, "src_port_parts.tsv"), "a", encoding="utf-8") as f:
            for k, ctr in src_port.items():
                for kk, vv in ctr.items():
                    f.write(f"{k}\t{kk}\t{vv}\n")
    if pair_cnt:
        with open(os.path.join(out_dir, "pair_parts.tsv"), "a", encoding="utf-8") as f:
            for k, ctr in pair_cnt.items():
                for kk, vv in ctr.items():
                    f.write(f"{k}\t{kk}\t{vv}\n")

def _reduce_topk_parts(parts_path, key_is_int=False, topk=TOPK_K):
    result = defaultdict(Counter)
    if not os.path.exists(parts_path):
        return {}
    with open(parts_path, "r", encoding="utf-8") as f:
        for line in f:
            s, t, c = line.rstrip("\n").split("\t")
            c = int(c)
            if key_is_int:
                try:
                    t = int(t)
                except Exception:
                    continue
            result[s][t] += c
    out = {}
    for s, ctr in result.items():
        out[s] = [k for k, _ in ctr.most_common(topk)]
    return out

def _build_or_load_topk(in_csv, chunksize, approx_mode, topk_src_path, topk_pair_path):
    if approx_mode:
        return _load_json_if_exists(topk_src_path), _load_json_if_exists(topk_pair_path)

    parts_dir = "parts"
    _collect_partials_for_topk(in_csv, chunksize, parts_dir)
    src_port_topk = _reduce_topk_parts(os.path.join(parts_dir, "src_port_parts.tsv"), key_is_int=True, topk=TOPK_K)
    pair_topk     = _reduce_topk_parts(os.path.join(parts_dir, "pair_parts.tsv"), key_is_int=False, topk=TOPK_K)

    with open(topk_src_path or TOPK_SRC_PORT_JSON, "w", encoding="utf-8") as f:
        json.dump(src_port_topk, f, ensure_ascii=False, indent=2)
    with open(topk_pair_path or TOPK_PAIR_JSON, "w", encoding="utf-8") as f:
        json.dump(pair_topk, f, ensure_ascii=False, indent=2)

    return src_port_topk, pair_topk

# ===== 主程式 =====
def main(in_csv: str = None,
         out_csv: str = None,
         fe_enable: dict = None,
         topk_src_port_json: str = None,
         topk_pair_json: str = None,
         batch_mode: bool = False,
         batch_size: int = 100_000,
         approx_mode: bool = False,
         quiet: bool = True,
         run_dir: str = None,
         use_manifest: bool = True,
         **kwargs):
    global CSV_CHUNK_SIZE, MAX_STATE_SIZE, PRUNE_FACTOR
    print(Style.BRIGHT + "==== 特徵工程（gpu_feature_engineering）====")

    # --- I/O ---
    src_from_manifest = None
    if use_manifest:
        m = _read_manifest(run_dir)
        try:
            src_from_manifest = m.get("map", {}).get("output", None)
        except Exception:
            src_from_manifest = None

    in_csv = src_from_manifest or in_csv or (input(Fore.CYAN + f"輸入檔（{DEFAULT_INPUT}）或 Enter 取預設：").strip() or DEFAULT_INPUT)
    out_csv = out_csv or (input(Fore.CYAN + f"輸出檔（{DEFAULT_OUTPUT}）或 Enter 取預設：").strip() or DEFAULT_OUTPUT)

    if run_dir:
        dir_fe = os.path.join(run_dir, "02_fe")
        os.makedirs(dir_fe, exist_ok=True)
        if not os.path.isabs(out_csv):
            out_csv = os.path.join(dir_fe, os.path.basename(out_csv))

    if not os.path.exists(in_csv):
        print(Fore.RED + f"❌ 找不到輸入檔：{in_csv}")
        return

    CSV_CHUNK_SIZE = int(batch_size) if batch_size else CSV_CHUNK_SIZE

    # --- 覆蓋功能開關 ---
    if fe_enable:
        globals()["ENABLE_TRAFFIC_STATS"]    = fe_enable.get("traffic_stats", ENABLE_TRAFFIC_STATS)
        globals()["ENABLE_PROTO_PORT_FEATS"] = fe_enable.get("proto_port", ENABLE_PROTO_PORT_FEATS)
        globals()["ENABLE_WINDOWED_FEATS"]   = fe_enable.get("windowed", ENABLE_WINDOWED_FEATS)
        globals()["ENABLE_RELATIONAL_BASE"]  = fe_enable.get("rel_base", ENABLE_RELATIONAL_BASE)
        globals()["ENABLE_RELATIONAL_TOPK"]  = fe_enable.get("rel_topk", ENABLE_RELATIONAL_TOPK)
        globals()["ENABLE_ANOMALY_INDIC"]    = fe_enable.get("anomaly", ENABLE_ANOMALY_INDIC)
        globals()["ENCODE_ENGINEERED_CATS"]  = fe_enable.get("encode_cats", ENCODE_ENGINEERED_CATS)

    # === [兩階段] 全域 Top-K 統計（若啟用且非 approx） ===
    topk_src_port = None
    topk_pair     = None
    if ENABLE_RELATIONAL_TOPK:
        topk_src_port, topk_pair = _build_or_load_topk(
            in_csv=in_csv,
            chunksize=CSV_CHUNK_SIZE,
            approx_mode=approx_mode,
            topk_src_path=topk_src_port_json or TOPK_SRC_PORT_JSON,
            topk_pair_path=topk_pair_json or TOPK_PAIR_JSON
        )

    # === 第二輪：實際特徵工程與 append 輸出 ===
    first = True
    total = 0
    state = {}

    if not batch_mode:
        df_all = pd.read_csv(in_csv, encoding="utf-8")
        chunks = [df_all]
    else:
        chunks = pd.read_csv(in_csv, chunksize=CSV_CHUNK_SIZE, encoding="utf-8")

    for chunk_pd in tqdm(chunks, desc="分塊處理", unit="chunk"):
        chunk = xdf.DataFrame.from_pandas(chunk_pd) if _HAS_CUDF else chunk_pd

        # 統一由 normalize_datetime 做高效解析（含偵測與快取）
        chunk = normalize_datetime(chunk, state, col="datetime")

        if ENABLE_TRAFFIC_STATS:
            chunk = add_traffic_stats(chunk)
        if ENABLE_PROTO_PORT_FEATS:
            chunk = add_proto_port_feats(chunk)
        if ENABLE_WINDOWED_FEATS:
            chunk = add_windowed_feats(chunk, state)
        if ENABLE_RELATIONAL_BASE:
            chunk = add_relational_basic(chunk)
        if ENABLE_RELATIONAL_TOPK and (topk_src_port or topk_pair):
            chunk = add_relational_topk(chunk, topk_src_port, topk_pair)
        if ENABLE_ANOMALY_INDIC:
            chunk = add_anomaly_indicators(chunk)
        if ENCODE_ENGINEERED_CATS:
            chunk = encode_engineered_categoricals(chunk)

        chunk = _reorder_append(chunk)
        chunk.to_csv(out_csv, mode="w" if first else "a", header=first, index=False)
        first = False
        total += len(chunk)

        check_and_flush("gpu_feature_engineering", chunk)

    print(Fore.GREEN + f"✅ 完成特徵工程 → {out_csv}（累計 {total} 筆）")

    if run_dir:
        m = _read_manifest(run_dir)
        m.setdefault("fe", {})
        m["fe"]["input"] = os.path.abspath(in_csv)
        m["fe"]["output"] = os.path.abspath(out_csv)
        try:
            with open(os.path.join(run_dir, "manifest.json"), "w", encoding="utf-8") as f:
                json.dump(m, f, ensure_ascii=False, indent=2)
            if not quiet:
                print(Style.BRIGHT + Fore.GREEN + "🧭 manifest.fe 已更新")
        except Exception as e:
            if not quiet:
                print(Fore.YELLOW + f"⚠️ manifest.fe 寫入失敗：{e}")

    return out_csv
