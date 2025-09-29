# -*- coding: utf-8 -*-
"""
GPU ETL Pipeline：清洗 → 映射 → 特徵工程（控制器，所有互動一次完成版）

目標：
- 長時間執行時，所有「需要使用者選擇」的對話，在開跑前一次做完。
- 清洗交給 log_cleaning.clean_logs()（其內建抽樣互動與原始輸入檔選擇），但仍在「開始處理之前」完成。
- CLI 一律 quiet=False（顯示回饋）；UI/背景呼叫 run_pipeline() 時 quiet=True。

互動時機（CLI）：
1) 問是否執行各階段（清洗/映射/特徵工程），Batch 參數。
2) 問 FE 選項（Approx / Top-K JSON），並**先問最終輸出檔 out_path**。
3) 若跳過清洗 → 先選 processed_logs.csv。
   若跳過映射但執行 FE → 先選 preprocessed_data.csv。
4) 開始執行：清洗（LC 會在開跑前完成抽樣與原始輸入檔選擇），映射，特徵工程（直接用前面已選 out_path，不再彈窗）。

注意：
- 若在無視窗環境執行（例如 SSH 或無 X server），tkinter 對話框將失敗；本檔已提供自動降級為 CLI 輸入的 fallback。
"""

import os, time
import sys
from typing import Optional, Dict, Any, List, Tuple
from colorama import Fore, Style, init as colorama_init

colorama_init(autoreset=True)

# =============== Tk 對話框工具（自動降級） ===============
def _has_tk() -> bool:
    try:
        import tkinter as tk  # noqa
        return True
    except Exception:
        return False

def _pick_files(title="選擇輸入檔案", multiple=True,
                patterns=(("Log/CSV Files", "*.csv *.txt *.gz"),
                          ("All files", "*.*"))) -> List[str] | str:
    """
    首選：tk 對話框；失敗則降級到 CLI 輸入（避免 headless crash）。
    multiple=True 回傳 List[str]；multiple=False 回傳 str（或 ""）
    """
    if _has_tk():
        try:
            import tkinter as tk
            from tkinter import filedialog
            root = tk.Tk()
            root.withdraw()
            root.attributes('-topmost', True)
            root.update()
            try:
                if multiple:
                    paths = filedialog.askopenfilenames(title=title, filetypes=list(patterns))
                    return list(paths) if paths else []
                else:
                    path = filedialog.askopenfilename(title=title, filetypes=list(patterns))
                    return path or ""
            finally:
                root.destroy()
        except Exception:
            pass  # 轉為 CLI 模式

    # CLI 降級
    print(Fore.YELLOW + f"⚠️ 無法使用圖形選檔，改用 CLI 輸入 → {title}")
    if multiple:
        s = input(Fore.CYAN + "請輸入路徑（多檔以分號 ; 分隔）：").strip()
        paths = [p.strip() for p in s.split(";") if p.strip()]
        return [p for p in paths if os.path.isfile(p)]
    else:
        p = input(Fore.CYAN + "請輸入檔案路徑：").strip()
        return p if os.path.isfile(p) else ""

def _save_file(title="選擇輸出檔案", default="engineered_data.csv") -> str:
    if _has_tk():
        try:
            import tkinter as tk
            from tkinter import filedialog
            root = tk.Tk()
            root.withdraw()
            root.attributes('-topmost', True)
            root.update()
            try:
                path = filedialog.asksaveasfilename(
                    title=title, initialfile=default, defaultextension=".csv",
                    filetypes=[("CSV files", "*.csv")]
                )
                return path or default
            finally:
                root.destroy()
        except Exception:
            pass
    # CLI 降級
    s = input(Fore.CYAN + f"{title}（預設 {default}）：").strip()
    return s or default

def _pick_optional_json(title) -> Optional[str]:
    patterns = (("JSON files", "*.json"), ("All files", "*.*"))
    p = _pick_files(title=title, multiple=False, patterns=patterns)
    return p or None

# === 匯入子模組（優先 package，失敗則 local） ===
try:
    from .gpu_etl_pipeline.log_cleaning import clean_logs as LC
    from .gpu_etl_pipeline.log_mapping import main as LM
    from .gpu_etl_pipeline.feature_engineering import main as FE
except ImportError:
    try:
        from gpu_etl_pipeline.log_cleaning import clean_logs as LC
        from gpu_etl_pipeline.log_mapping import main as LM
        from gpu_etl_pipeline.feature_engineering import main as FE
    except ImportError:
        cur_dir = os.path.dirname(os.path.abspath(__file__))
        pipeline_dir = os.path.join(cur_dir, "gpu_etl_pipeline")
        if pipeline_dir not in sys.path:
            sys.path.append(pipeline_dir)
        from log_cleaning import clean_logs as LC
        from log_mapping import main as LM
        from feature_engineering import main as FE

# =============== 小工具：問答/檢查/保底 ===============
def _ask_yn_10(msg: str, default_true: bool) -> bool:
    """1/0 問答；Enter 套預設"""
    while True:
        s = input(Fore.CYAN + f"{msg} (1=是,0=否；預設 {1 if default_true else 0})：").strip()
        if s == "": return default_true
        if s in ("0","1"): return s == "1"
        print(Fore.RED + "❌ 輸入錯誤，請重新輸入！")

def _ask_int(msg: str, default: int) -> int:
    s = input(Fore.CYAN + f"{msg}（預設 {default}）：").strip()
    try:
        return int(s) if s else default
    except Exception:
        return default

def _check_file_exists(path: Optional[str], module_name: str, allow_small=False) -> str:
    """#DEBUG 檢查：檔案存在；必要時檢查非空"""
    if not path:
        raise RuntimeError(f"❌ [{module_name}] 未取得輸出檔路徑")
    if not os.path.isfile(path):
        raise RuntimeError(f"❌ [{module_name}] 找不到輸出檔：{path}")
    if (not allow_small) and os.path.getsize(path) < 100:
        raise RuntimeError(f"❌ [{module_name}] 輸出檔過小或為空：{path}")
    print(Fore.GREEN + f"[DEBUG] {module_name} 輸出檔檢查通過：{path}")
    return path

def _coalesce_return(ret_value: Optional[str], fallback: str, module_name: str) -> str:
    """
    某些 module.main() 可能不回傳路徑；使用 fallback（我們傳入的 out_csv）
    再做存在檢查，避免 silent fail。
    """
    path = ret_value or fallback
    return _check_file_exists(path, module_name)

# =============== 核心 Pipeline（供 UI / 自動化呼叫） ===============
def run_pipeline(
    in_paths: Optional[List[str] | str],
    out_path: str = "engineered_data.csv",
    do_clean: bool = True,
    do_map: bool = True,
    do_fe: bool = True,
    batch_mode: bool = False,
    batch_size: int = 50_000,
    sampling_config: Optional[Dict[str, Any]] = None,  # e.g. {"method":"random","ratio":0.1,"label_col":"is_attack","seed":42}
    fe_enable=None,
    topk_src_port_json: Optional[str] = None,
    topk_pair_json: Optional[str] = None,
    approx_mode: bool = False,
    quiet: bool = True
) -> str:
    """
    建議 UI/背景呼叫（quiet=True）。
    do_clean=True：若 quiet=True，會以靜默參數呼叫 LC（需提供 paths）；quiet=False 則交給 LC 自行互動。
    do_clean=False：in_paths 應提供 processed_logs.csv。
    do_map=False 但 do_fe=True：in_paths 應提供 preprocessed_data.csv。
    """
    # 1) 正常化輸入路徑
    if isinstance(in_paths, str):
        in_paths = [in_paths]
    paths_list = in_paths or []

    current_input: Optional[str] = None

    # 2) 清洗
    if do_clean:
        if quiet:
            # UI/背景：靜默呼叫 LC（paths 可為多檔；LC 會處理）
            lc_kwargs = dict(
                quiet=True,
                paths=paths_list if paths_list else None,
                clean_csv="processed_logs.csv",
                enable_sampling=False
            )
            if sampling_config is not None:
                lc_kwargs["sampling_cfg"] = sampling_config
            lc_out = LC(**lc_kwargs)  # 期望回傳 processed_logs.csv
        else:
            # CLI：交給 LC 自行互動
            lc_out = LC(quiet=False, enable_sampling=True)
        current_input = _coalesce_return(lc_out, "processed_logs.csv", "Cleaning")
        print(Style.BRIGHT + Fore.GREEN + f"✅ Cleaning 完成 → {current_input}" + Style.RESET_ALL)
    else:
        # 略過清洗：使用外部傳入的 processed_logs.csv
        if not paths_list:
            raise FileNotFoundError("略過清洗時，需提供 processed_logs.csv 或等價 CSV 路徑")
        current_input = _check_file_exists(paths_list[0], "Cleaning(skip)", allow_small=True)

    # 3) 映射
    if do_map:
        lm_out_path = "preprocessed_data.csv"
        lm_ret = LM(in_csv=current_input, out_csv=lm_out_path,
                    batch_mode=batch_mode, batch_size=batch_size, quiet=quiet)
        current_input = _coalesce_return(lm_ret, lm_out_path, "Mapping")
        if not quiet:
            print(Style.BRIGHT + Fore.GREEN + f"✅ Mapping 完成 → {current_input}" + Style.RESET_ALL)
    else:
        # 略過映射：current_input 必須是 FE 可讀的 CSV（通常為 preprocessed_data.csv）
        current_input = _check_file_exists(current_input, "Mapping(skip)", allow_small=False)

    # 4) 特徵工程
    if do_fe:
        fe_ret = FE(
            in_csv=current_input,
            out_csv=out_path,   # 使用一開始就決定好的 out_path，不再彈窗
            fe_enable=fe_enable,
            topk_src_port_json=topk_src_port_json,
            topk_pair_json=topk_pair_json,
            batch_mode=batch_mode,
            batch_size=batch_size,
            approx_mode=approx_mode,
            quiet=quiet
        )
        final_out = _coalesce_return(fe_ret, out_path, "FeatureEngineering")
        if not quiet:
            print(Style.BRIGHT + Fore.GREEN + f"✅ Feature Engineering 完成 → {final_out}" + Style.RESET_ALL)
        return final_out
    else:
        if not quiet:
            print(Fore.YELLOW + f"⚠️ 已跳過特徵工程；最終輸出為上一階段檔案：{current_input}")
        return current_input  # type: ignore


# =============== 互動式控制器（CLI；所有互動先問完） ===============
def run_pipeline_cli() -> None:
    print(Style.BRIGHT + "==== GPU ETL Pipeline 控制器（CLI）====")

    # ★ 0) 建立本次執行的 run_dir（集中所有產物）
    run_dir = os.path.abspath(f"./artifacts/{time.strftime('%Y%m%d_%H%M%S')}")
    os.makedirs(run_dir, exist_ok=True)
    print(Fore.CYAN + f"[INFO] 本次 artifacts 目錄：{run_dir}")

    # 1) 階段選擇（一次問完）
    do_clean = _ask_yn_10("是否執行 清洗/標準化（log_cleaning）", True)
    do_map   = _ask_yn_10("是否執行 字典映射/排序（log_mapping）", True)
    do_fe    = _ask_yn_10("是否執行 特徵工程（feature_engineering）", True)

    # 2) Batch 參數（一次問完）
    batch_mode = _ask_yn_10("是否啟用 Batch Mode", False)
    batch_size = _ask_int("batch_size", 50_000) if batch_mode else 50_000

    # 3) 特徵工程選項（開始前就一次選完）
    approx_mode: bool = False
    topk_src: Optional[str] = None
    topk_pair: Optional[str] = None
    out_csv: str = "engineered_data.csv"

    if do_fe:
        approx_mode = _ask_yn_10("啟用 Approx 模式（僅批內近似統計）", False)
        if _ask_yn_10("指定 Top-K SrcPort JSON？", False):
            topk_src = _pick_optional_json("選擇 Top-K Src Port JSON") or None
        if _ask_yn_10("指定 Top-K Pair JSON？", False):
            topk_pair = _pick_optional_json("選擇 Top-K Pair JSON") or None
        print("💾 請選擇最終輸出檔（engineered_data.csv）")
        user_pick = _save_file(title="選擇最終輸出檔", default="engineered_data.csv")
        # ★ 3.1 若使用者沒改名或選相對路徑，統一落到 02_fe/
        if os.path.isabs(user_pick):
            out_csv = user_pick
        else:
            out_csv = os.path.join(run_dir, "02_fe", os.path.basename(user_pick))
        os.makedirs(os.path.dirname(out_csv), exist_ok=True)

    # 4) 前置檔案選擇（跳過某階段時，先把路徑問好）
    in_source: Optional[str] = None   # 供映射的輸入（略過清洗時）
    fe_in_csv: Optional[str] = None   # 供 FE 的輸入（略過清洗與映射時）

    if not do_clean:
        if do_map:
            print("📂 已略過清洗，請選擇作為『映射輸入』的 processed_logs.csv（或等價 CSV）")
            p = _pick_files(
                title="選擇映射輸入（processed_logs.csv 或等價）",
                multiple=False,
                patterns=(("CSV files", "*.csv"), ("All files", "*.*"))
            )
            in_source = p if isinstance(p, str) else (p[0] if p else "")
            if not in_source:
                print(Fore.RED + "❌ 未選擇映射輸入，流程結束")
                return
        else:
            if do_fe:
                print("📂 已略過清洗與映射，請選擇『特徵工程輸入』的 CSV")
                p = _pick_files(
                    title="選擇 FE 輸入 CSV",
                    multiple=False,
                    patterns=(("CSV files", "*.csv"), ("All files", "*.*"))
                )
                fe_in_csv = p if isinstance(p, str) else (p[0] if p else "")
                if not fe_in_csv:
                    print(Fore.RED + "❌ 未選擇 FE 輸入，流程結束")
                    return

    # 5) 開始執行（之後不再出現任何對話框）
    print(Style.BRIGHT + f"🚀 開始執行（CLI 模式 quiet=False；所有選項已一次設定完成）...")
    print(Fore.YELLOW + f"[DEBUG] do_clean={do_clean}, do_map={do_map}, do_fe={do_fe}, "
                        f"batch_mode={batch_mode}, batch_size={batch_size}, approx_mode={approx_mode}")
    if do_fe:
        print(Fore.YELLOW + f"[DEBUG] FE out_csv={out_csv}, topk_src={topk_src}, topk_pair={topk_pair}")

    # 5.1 清洗
    if do_clean:
        # ★ 5.1-a 傳入 run_dir；讓 LC 把 processed/sample 落在 00_clean/，並寫 manifest.clean.active_clean_file
        cleaned_csv = LC(quiet=False, enable_sampling=True, run_dir=run_dir)
        current_input = _coalesce_return(cleaned_csv, "processed_logs.csv", "Cleaning")
    else:
        current_input = in_source or fe_in_csv  # 兩者只會有一個被賦值
        current_input = _check_file_exists(current_input, "Cleaning(skip)", allow_small=True)

    # 5.2 映射
    if do_map:
        # ★ 5.2-a 出力固定到 run_dir/01_map/
        lm_out_path = os.path.join(run_dir, "01_map", "preprocessed_data.csv")
        os.makedirs(os.path.dirname(lm_out_path), exist_ok=True)

        # ★ 5.2-b 傳 run_dir + use_manifest=True → LM 會優先吃 manifest.clean.active_clean_file（抽樣優先）
        lm_ret = LM(
            in_csv=current_input,
            out_csv=lm_out_path,
            batch_mode=batch_mode,
            batch_size=batch_size,
            quiet=False,
            run_dir=run_dir,          # ★
            use_manifest=True         # ★
        )
        current_input = _coalesce_return(lm_ret, lm_out_path, "Mapping")
        print(Fore.GREEN + f"✅ Mapping 完成 → {current_input}" + Style.RESET_ALL)
    else:
        if do_fe:
            print(Fore.YELLOW + f"⚠️ 已跳過映射；輸入給 FE：{current_input}")

    # 5.3 特徵工程
    if do_fe:
        # ★ 5.3-a 若映射有執行 → FE 可用 manifest.map.output；否則就用使用者選的 fe_in_csv
        use_manifest_for_fe = bool(do_map)

        fe_ret = FE(
            in_csv=current_input,
            out_csv=out_csv,
            fe_enable=None,
            topk_src_port_json=topk_src,
            topk_pair_json=topk_pair,
            batch_mode=batch_mode,
            batch_size=batch_size,
            approx_mode=approx_mode,
            quiet=False,
            run_dir=run_dir,                  # ★ 讓 FE 能寫入 02_fe 並更新 manifest.fe
            use_manifest=use_manifest_for_fe  # ★ 映射有跑才用 manifest 的 map.output
        )
        final_out = _coalesce_return(fe_ret, out_csv, "FeatureEngineering")
        print(Style.BRIGHT + Fore.GREEN + f"✅ Feature Engineering 完成 → {final_out}" + Style.RESET_ALL)
        print(Style.BRIGHT + Fore.YELLOW + f"🎉 Pipeline 全部完成，最終輸出：{final_out}" + Style.RESET_ALL)
    else:
        print(Style.BRIGHT + Fore.YELLOW + f"🎉 Pipeline 完成（FE 跳過），最終輸出：{current_input}" + Style.RESET_ALL)
# =============== 入口 ===============
if __name__ == "__main__":
    run_pipeline_cli()
