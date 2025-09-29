# -*- coding: utf-8 -*-
"""
utils.py（GPU 版通用工具）
- 記憶體監控與暫存 flush（支援 cuDF / pandas）
- 自動偵測 cudf/cupy 是否可用，無 GPU 時退回 CPU 以確保流程不中斷
"""
try:
    import psutil
except Exception:  # pragma: no cover - fallback when psutil not installed
    from ui_pages import psutil_stub as psutil  # type: ignore
import gc
import os
import tempfile
import time
import uuid
from colorama import Fore

# ---- 嘗試載入 GPU 相依套件 ----
try:
    import cudf  # type: ignore
    _HAS_CUDF = True
except Exception:
    cudf = None
    _HAS_CUDF = False

try:
    import cupy as cp  # type: ignore
    _HAS_CUPY = True
except Exception:
    cp = None
    _HAS_CUPY = False

try:
    import pandas as pd
except Exception:
    pd = None

_last_flush_time = 0  # 冷卻變數
MEMORY_FLUSH_THRESHOLD = 60.0  # 全域閾值（%）

def _is_cudf_dataframe(obj) -> bool:
    return _HAS_CUDF and obj is not None and obj.__class__.__module__.startswith("cudf.")

def _to_csv_generic(df, path: str):
    """同一介面寫入 CSV：優先使用 df.to_csv（cuDF/pandas 皆支援）。"""
    df.to_csv(path, index=False)

def check_and_flush(module_name: str,
                    df=None,
                    threshold: float = None,
                    temp_dir: str = None,
                    cooldown_sec: int = 10) -> None:
    """
    通用記憶體檢查與 flush 函式（GPU 版）

    - module_name: 呼叫的模組名稱（例如 "log_cleaning"）
    - df: 若提供，會先寫入暫存檔再釋放（支援 cuDF / pandas DataFrame）
    - threshold: 記憶體使用率超過此百分比才觸發（None 則用 MEMORY_FLUSH_THRESHOLD）
    - temp_dir: 暫存檔存放資料夾（預設系統暫存目錄）
    - cooldown_sec: 冷卻時間（秒），避免短時間重複觸發
    """
    global _last_flush_time
    now = time.time()

    if threshold is None:
        threshold = MEMORY_FLUSH_THRESHOLD

    # 冷卻限制
    if now - _last_flush_time < cooldown_sec:
        return

    mem_percent = psutil.virtual_memory().percent
    if mem_percent >= threshold:
        _last_flush_time = now
        print(Fore.YELLOW + f"⚠️ [MemoryGuard] {module_name} 記憶體使用率 {mem_percent:.1f}%，執行 flush...")

        if df is not None:
            temp_dir = temp_dir or tempfile.gettempdir()
            temp_path = os.path.join(
                temp_dir,
                f"{module_name}_flush_{os.getpid()}_{int(time.time()*1000)}_{uuid.uuid4().hex[:6]}.csv"
            )
            try:
                _to_csv_generic(df, temp_path)
                print(Fore.YELLOW + f"💾 已將暫存資料寫入：{temp_path}")
                try:
                    del df
                except Exception:
                    pass
            except Exception as e:
                print(Fore.RED + f"❌ 暫存資料寫入失敗：{e}")

        # 釋放 CPU 記憶體
        gc.collect()
        # 嘗試釋放 GPU 記憶體（如有 cupy/cudf）
        if _HAS_CUPY:
            try:
                cp.get_default_memory_pool().free_all_blocks()
            except Exception:
                pass
        print(Fore.GREEN + f"✅ [MemoryGuard] Flush 完成，記憶體釋放後：{psutil.virtual_memory().percent:.1f}%")
