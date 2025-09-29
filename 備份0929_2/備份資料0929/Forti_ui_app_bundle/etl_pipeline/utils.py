import psutil
import gc
import os
import tempfile
import pandas as pd
import time
import uuid
from colorama import Fore

_last_flush_time = 0  # 冷卻變數
MEMORY_FLUSH_THRESHOLD = 80.0  # 全域閾值

def check_and_flush(module_name: str,
                    df: pd.DataFrame = None,
                    threshold: float = None,
                    temp_dir: str = None,
                    cooldown_sec: int = 10) -> None:
    """
    通用記憶體檢查與 flush 函式
    - module_name: 呼叫的模組名稱（例如 "log_cleaning"）
    - df: 若提供，會先寫入暫存檔再釋放
    - threshold: 記憶體使用率超過此百分比才觸發（None 則用 MEMORY_FLUSH_THRESHOLD）
    - temp_dir: 暫存檔存放資料夾（預設系統暫存目錄）
    - cooldown_sec: 冷卻時間（秒），避免短時間重複觸發

    用法：
    from utils import check_and_flush
    check_and_flush("log_cleaning", df_chunk)  # 不傳 threshold 則使用全域設定
    """
    global _last_flush_time
    now = time.time()

    # 預設使用全域閾值
    if threshold is None:
        threshold = MEMORY_FLUSH_THRESHOLD

    # 冷卻時間檢查
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
                df.to_csv(temp_path, index=False)
                print(Fore.YELLOW + f"💾 已將暫存資料寫入：{temp_path}")
                del df  # 不會刪掉呼叫端的變數，只會移除函式內參考
            except Exception as e:
                print(Fore.RED + f"❌ 暫存資料寫入失敗：{e}")

        gc.collect()
        print(Fore.GREEN + f"✅ [MemoryGuard] Flush 完成，記憶體釋放後：{psutil.virtual_memory().percent:.1f}%")
