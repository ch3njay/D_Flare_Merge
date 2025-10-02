# -*- coding: utf-8 -*-
"""
pipeline_controller.py
目的：
- 串接 log_cleaning / log_mapping / feature_engineering 三階段
- 同檔同介面支援 CLI 與 UI（程式化）兩種用法
- 大檔流式處理、進度條、色彩、防笨

相依：
- log_cleaning.py: clean_logs()（互動式）
- log_mapping.py: _apply_mappings(), _reorder_preserve(), _load_unique_values(), _check_coverage(), 常數
- feature_engineering.py: 各 add_* 函式與常數設定

使用：
CLI： python pipeline_controller.py
UI / 程式化：from pipeline_controller import run_pipeline
"""

import os
import json
import pandas as pd
from typing import Optional, Dict, Any
from tqdm import tqdm
from colorama import Fore, Style, init as colorama_init

# 初始化色彩
colorama_init(autoreset=True)

# 匯入個既有模組（支援套件內呼叫與單檔執行）
try:
    from etl_pipeline import log_cleaning as LC  # 提供 clean_logs() 互動流程
    from etl_pipeline import log_mapping as LM  # 提供映射與排序的工具方法
    from etl_pipeline import feature_engineering as FE  # 提供五大類特徵工程方法
    from etl_pipeline.utils import check_and_flush
except ModuleNotFoundError as exc:
    if exc.name != "etl_pipeline":
        raise
    from Forti_ui_app_bundle.etl_pipeline import log_cleaning as LC
    from Forti_ui_app_bundle.etl_pipeline import log_mapping as LM
    from Forti_ui_app_bundle.etl_pipeline import feature_engineering as FE
    from Forti_ui_app_bundle.etl_pipeline.utils import check_and_flush

# 全域靜默模式（非互動呼叫時可避免多餘提示）
LC.QUIET = False
LM.QUIET = False
FE.QUIET = False
# ------------------------- 全域設定 -------------------------
# 記憶體使用率閾值（超過此值才觸發 flush）
MEMORY_FLUSH_THRESHOLD = 80.0  # 變更此值可調整全流程 flush 閾值
# ------------------------- 預設參數 -------------------------
# 預設路徑
DEFAULT_CLEAN_OUT   = "processed_logs.csv"
DEFAULT_PREPROC_OUT = "preprocessed_data.csv"
DEFAULT_FE_OUT      = "engineered_data.csv"
DEFAULT_UNIQUE_JSON = "log_unique_values.json"

# I/O 設定
CSV_CHUNK_SIZE = 100_000
CSV_ENCODING   = "utf-8"

# ------------------------- 工具 -------------------------
def _ask_yn(prompt: str, default: bool) -> bool:
    while True:
        s = input(Fore.CYAN + f"{prompt} (1=是,0=否；預設 {1 if default else 0})：").strip()
        if s == "": return default
        if s in ("0","1"): return s == "1"
        print(Fore.RED + "❌ 輸入錯誤，請重新輸入！")

def _ask_path(prompt: str, default_path: str) -> str:
    p = input(Fore.CYAN + f"{prompt}（預設 {default_path}）：").strip()
    return p if p else default_path

def _ensure_datetime(col):
    # 將 DataFrame 的 datetime 欄位轉為真正的 datetime 型別（若存在）
    if "datetime" in col.columns and not pd.api.types.is_datetime64_any_dtype(col["datetime"]):
        col["datetime"] = pd.to_datetime(col["datetime"], errors="coerce")
    return col

def _resolve_out_path(in_csv: str, out_csv: str) -> str:
    """若 out_csv 未含資料夾，改寫到 in_csv 同資料夾。"""
    out_csv = os.path.expanduser(out_csv)
    if os.path.isabs(out_csv):
        return out_csv
    base_dir = os.path.dirname(os.path.abspath(in_csv)) if in_csv else os.getcwd()
    return os.path.join(base_dir, out_csv)

# ------------------------- S2：映射（非互動，供 UI 用） -------------------------
def run_mapping_noninteractive(
    in_csv: str,
    out_csv: str = DEFAULT_PREPROC_OUT,
    unique_json: Optional[str] = DEFAULT_UNIQUE_JSON
) -> str:
    """
    非互動版本的映射與排序（直接重用 log_mapping 內部方法）。
    - 僅做字典映射與欄位排序
    - 檢查唯一值覆蓋（若提供 unique_json）
    """
    if not os.path.exists(in_csv):
        raise FileNotFoundError(f"找不到輸入檔：{in_csv}")
    
    out_csv = _resolve_out_path(in_csv, out_csv)
    
    uniq_map, do_check = ({}, False)
    if unique_json and os.path.exists(unique_json):
        uniq_map, do_check = LM._load_unique_values(unique_json)  # 使用現有方法

    first = True
    total = 0
    missing = {}

    for chunk in tqdm(pd.read_csv(in_csv, chunksize=CSV_CHUNK_SIZE, encoding=CSV_ENCODING),
                    desc="映射分塊", unit="chunk"):
        if "raw_log" in chunk.columns:
            chunk.drop(columns=["raw_log"], inplace=True)
        chunk = _ensure_datetime(chunk)

        # 覆蓋檢查要在映射前（service 還是字串）
        if do_check:
            LM._check_coverage(chunk, uniq_map, missing)

        # 這裡把 uniq_map 傳進去，確保 service 穩定映射
        chunk = LM._apply_mappings(chunk, uniq_map)

        if "is_attack" not in chunk.columns:
            if "crscore" in chunk.columns:
                chunk["is_attack"] = (pd.to_numeric(chunk["crscore"], errors="coerce")
                                    .fillna(0).astype(int) > 0).astype(int)
            else:
                chunk["is_attack"] = 0

        chunk.drop_duplicates(inplace=True)
        chunk = LM._reorder_preserve(chunk)

        chunk.to_csv(out_csv, mode="w" if first else "a", header=first,
                    index=False, encoding=CSV_ENCODING)
        first = False
        total += len(chunk)

    # 報告
    report_path = os.path.splitext(out_csv)[0] + "_mapping_report.json"
    rep = {"total_rows": total}
    if missing:
        rep["uncovered_values"] = {k: sorted(list(v)) for k, v in missing.items()}
    else:
        rep["uncovered_values"] = "none or not-checked"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(rep, f, ensure_ascii=False, indent=2)

    print(Fore.GREEN + f"✅ 映射完成：{out_csv}（{total} 筆）")
    print(Fore.GREEN + f"📝 報告：{report_path}")
    return out_csv

# ------------------------- S3：特徵工程（非互動，供 UI 用） -------------------------
def run_feature_engineering_noninteractive(
    in_csv: str,
    out_csv: str = DEFAULT_FE_OUT,
    # 依照 FE 模組的開關設計，提供可覆寫參數
    enable_traffic_stats: Optional[bool] = None,
    enable_proto_port: Optional[bool] = None,
    enable_windowed: Optional[bool] = None,
    enable_rel_base: Optional[bool] = None,
    enable_rel_topk: Optional[bool] = None,
    enable_anomaly: Optional[bool] = None,
    topk_src_port_json: Optional[str] = None,
    topk_pair_json: Optional[str] = None,
) -> str:
    """
    非互動版本的特徵工程（重用 feature_engineering 內部方法與常數）。
    可用參數覆寫 FE 的預設開關與 top-k 字典路徑。
    """
    if not os.path.exists(in_csv):
        raise FileNotFoundError(f"找不到輸入檔：{in_csv}")
    out_csv = _resolve_out_path(in_csv, out_csv)
    
    # 以參數覆寫 FE 模組內的旗標（若有提供）
    if enable_traffic_stats is not None:  FE.ENABLE_TRAFFIC_STATS    = enable_traffic_stats
    if enable_proto_port is not None:     FE.ENABLE_PROTO_PORT_FEATS = enable_proto_port
    if enable_windowed is not None:       FE.ENABLE_WINDOWED_FEATS   = enable_windowed
    if enable_rel_base is not None:       FE.ENABLE_RELATIONAL_BASE  = enable_rel_base
    if enable_rel_topk is not None:       FE.ENABLE_RELATIONAL_TOPK  = enable_rel_topk
    if enable_anomaly is not None:        FE.ENABLE_ANOMALY_INDIC    = enable_anomaly

    if topk_src_port_json: FE.TOPK_SRC_PORT_JSON = topk_src_port_json
    if topk_pair_json:     FE.TOPK_PAIR_JSON     = topk_pair_json

    # 載入 Top-K 字典（若沒有就回傳 None，FE 內部會安全跳過）
    topk_src_port = FE._load_json_if_exists(FE.TOPK_SRC_PORT_JSON)
    topk_pair     = FE._load_json_if_exists(FE.TOPK_PAIR_JSON)

    first = True
    total = 0
    state: Dict[str, Any] = {}  # 給時間窗特徵跨 chunk 的小狀態

    for chunk in tqdm(pd.read_csv(in_csv, chunksize=CSV_CHUNK_SIZE, encoding=CSV_ENCODING),
                      desc="工程分塊", unit="chunk"):
        # 時間欄位型別保險
        chunk = _ensure_datetime(chunk)

        # 1) 流量統計
        if FE.ENABLE_TRAFFIC_STATS:
            chunk = FE.add_traffic_stats(chunk)

        # 2) 協定/端口
        if FE.ENABLE_PROTO_PORT_FEATS:
            chunk = FE.add_proto_port_feats(chunk)

        # 3) 時間窗口（可選）
        if FE.ENABLE_WINDOWED_FEATS:
            chunk = FE.add_windowed_feats(chunk, state)

        # 4) 關係特徵
        if FE.ENABLE_RELATIONAL_BASE:
            chunk = FE.add_relational_basic(chunk)
        if FE.ENABLE_RELATIONAL_TOPK:
            chunk = FE.add_relational_topk(chunk, topk_src_port, topk_pair)

        # 5) 異常指標
        if FE.ENABLE_ANOMALY_INDIC:
            chunk = FE.add_anomaly_indicators(chunk)

        # 6) 工程後類別欄位數值化（若有）
        if getattr(FE, "ENCODE_ENGINEERED_CATS", False) and hasattr(FE, "encode_engineered_categoricals"):
            chunk = FE.encode_engineered_categoricals(chunk)
        
        # 核心在前，新特徵附在後；去重
        chunk = FE._reorder_append(chunk)
        chunk.drop_duplicates(inplace=True)

        # 寫出
        chunk.to_csv(out_csv, mode="w" if first else "a", header=first,
                     index=False, encoding=CSV_ENCODING)
        first = False
        total += len(chunk)

    print(Fore.GREEN + f"✅ 特徵工程完成：{out_csv}（{total} 筆）")
    return out_csv

# ------------------------- 總管：CLI 與 UI 皆可 -------------------------
def run_pipeline(
    do_clean: bool = True,
    do_map: bool = True,
    do_fe: bool = False,
    # I/O 路徑（可為 None → 依前一步輸出決定）
    clean_out: str = DEFAULT_CLEAN_OUT,
    preproc_out: str = DEFAULT_PREPROC_OUT,
    fe_out: str = DEFAULT_FE_OUT,
    unique_json: Optional[str] = DEFAULT_UNIQUE_JSON,
    # FE 參數（供 UI/程式化覆寫）
    fe_enable: Optional[Dict[str, bool]] = None,
    fe_topk_src_port_json: Optional[str] = None,
    fe_topk_pair_json: Optional[str] = None
) -> str:
    """
    UI/程式化入口：以參數決定各階段是否執行與輸入輸出路徑。
    - 清洗階段：呼叫 LC.clean_logs()（互動）；或使用者可先行產出 processed_logs.csv 再只跑後兩階段
    - 映射與特徵工程：皆使用非互動版本（本檔提供），不會彈窗
    回傳：最終輸出檔路徑
    """
    current_path = None

    # S1 清洗（若啟用，走原模組互動流程；輸出檔名可在互動中指定）
    if do_clean:
        print(Style.BRIGHT + "—— 第 1 階段：清洗 / 標準化 ——")
        current_path = LC.clean_logs()  # 互動式；會回傳實際輸出路徑  :contentReference[oaicite:6]{index=6}
        check_and_flush("pipeline_controller_after_cleaning")
    else:
        # 若未執行清洗，預設用指定之 processed_logs.csv
        current_path = clean_out
        if not os.path.exists(current_path):
            raise FileNotFoundError(f"找不到 processed_logs：{current_path}")

    # S2 映射（非互動；安全不彈窗）
    if do_map:
        print(Style.BRIGHT + "—— 第 2 階段：字典映射 / 欄位排序 ——")
        current_path = run_mapping_noninteractive(
            in_csv=current_path,
            out_csv=preproc_out,
            unique_json=unique_json
        )
        check_and_flush("pipeline_controller_after_mapping")
    else:
        current_path = preproc_out
        if not os.path.exists(current_path):
            raise FileNotFoundError(f"找不到 preprocessed_data：{current_path}")

    # S3 特徵工程（非互動）
    if do_fe:
        print(Style.BRIGHT + "—— 第 3 階段：特徵工程 ——")
        fe_kwargs = {}
        if fe_enable:
            fe_kwargs.update(dict(
                enable_traffic_stats=fe_enable.get("traffic_stats"),
                enable_proto_port=fe_enable.get("proto_port"),
                enable_windowed=fe_enable.get("windowed"),
                enable_rel_base=fe_enable.get("rel_base"),
                enable_rel_topk=fe_enable.get("rel_topk"),
                enable_anomaly=fe_enable.get("anomaly"),
            ))
        current_path = run_feature_engineering_noninteractive(
            in_csv=current_path,
            out_csv=fe_out,
            topk_src_port_json=fe_topk_src_port_json,
            topk_pair_json=fe_topk_pair_json,
            **fe_kwargs
        )
        check_and_flush("pipeline_controller_after_feature_eng") 

    print(Fore.GREEN + f"✅ Pipeline 完成。最終輸出：{current_path}")
    return current_path

# ------------------------- CLI 入口 -------------------------
def run_pipeline_cli():
    print(Style.BRIGHT + "==== D-FLARE Pipeline 控制器（CLI）====")
    do_clean = _ask_yn("是否執行 第1階段：清洗/標準化（log_cleaning）", True)
    do_map   = _ask_yn("是否執行 第2階段：字典映射/排序（log_mapping）", True)
    do_fe    = _ask_yn("是否執行 第3階段：特徵工程（feature_engineering）", False)

    # 路徑設定（當未執行前一步時需人工指定）
    clean_out   = _ask_path("第1階段輸出（processed_logs.csv）", DEFAULT_CLEAN_OUT) if not do_clean else DEFAULT_CLEAN_OUT
    preproc_out = _ask_path("第2階段輸出（preprocessed_data.csv）", DEFAULT_PREPROC_OUT) if not do_map else DEFAULT_PREPROC_OUT
    fe_out      = _ask_path("第3階段輸出（engineered_data.csv）", DEFAULT_FE_OUT)

    unique_json = _ask_path("唯一值清單（按 Enter 跳過）", DEFAULT_UNIQUE_JSON)

    # FE 選項
    fe_enable = None
    fe_topk_src = None
    fe_topk_pair = None
    if do_fe:
        print(Style.BRIGHT + "—— 特徵工程開關（輸入 1=開,0=關，Enter=預設）——")
        def ask_flag(q, default):
            s = input(Fore.CYAN + f"{q}（預設 {1 if default else 0}）：").strip()
            if s == "": return None  # 使用預設
            return (s == "1")
        fe_enable = {
            "traffic_stats": ask_flag("1) 流量統計", FE.ENABLE_TRAFFIC_STATS),
            "proto_port":    ask_flag("2) 協定/端口", FE.ENABLE_PROTO_PORT_FEATS),
            "windowed":      ask_flag("3) 時間窗口", FE.ENABLE_WINDOWED_FEATS),
            "rel_base":      ask_flag("4a) 關係特徵（基礎）", FE.ENABLE_RELATIONAL_BASE),
            "rel_topk":      ask_flag("4b) 關係特徵（Top-K）", FE.ENABLE_RELATIONAL_TOPK),
            "anomaly":       ask_flag("5) 異常指標", FE.ENABLE_ANOMALY_INDIC),
        }
        fe_topk_src = _ask_path("Top-K 字典（srcip→dstport JSON，Enter 跳過）", FE.TOPK_SRC_PORT_JSON)
        fe_topk_pair= _ask_path("Top-K 字典（srcip→dstip JSON，Enter 跳過）", FE.TOPK_PAIR_JSON)

    # 執行
    return run_pipeline(
        do_clean=do_clean, do_map=do_map, do_fe=do_fe,
        clean_out=clean_out, preproc_out=preproc_out, fe_out=fe_out,
        unique_json=unique_json if os.path.exists(unique_json) else None,
        fe_enable=fe_enable,
        fe_topk_src_port_json=fe_topk_src if fe_topk_src and os.path.exists(fe_topk_src) else None,
        fe_topk_pair_json=fe_topk_pair if fe_topk_pair and os.path.exists(fe_topk_pair) else None
    )

if __name__ == "__main__":
    run_pipeline_cli()
