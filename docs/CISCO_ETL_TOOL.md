# Cisco ETL 工具建立報告

## 📋 概述

為 Cisco 模組建立了獨立的 ETL 處理 UI 頁面，支援 Cisco ASA 防火牆日誌的清洗與預處理。

**建立日期**：2025年10月8日

---

## 🎯 目標

1. 為 Cisco 模組新增獨立的 ETL 處理介面
2. 支援 Cisco ASA 特定的日誌格式解析
3. 提供使用者友善的檔案上傳與處理流程
4. 與 Fortinet 模組保持功能對等

---

## 📁 建立的檔案

### 1. **ETL UI 頁面** (`Cisco_ui/ui_pages/etl_ui.py`)

**功能特點**：
- ✅ 多檔案上傳支援（.csv, .txt, .log, .gz）
- ✅ 兩階段 ETL 處理：清洗 (log_cleaning) → 映射 (log_mapping)
- ✅ 即時進度顯示與處理統計
- ✅ 結果下載功能
- ✅ 詳細的使用說明與格式說明

**主要函式**：
```python
def app() -> None:
    """Cisco ETL Pipeline UI 主函式"""
    # 1. 檔案上傳區
    # 2. 輸出設定區
    # 3. 執行區
    # 4. 結果顯示區
```

**核心流程**：
```python
# 執行 ETL Pipeline
outputs = run_etl_pipeline(
    raw_log_path=saved_paths[0],
    output_dir=output_dir,
    show_progress=show_progress
)
```

---

## 🔧 Cisco ASA 日誌格式特點

### 格式差異

**Cisco ASA**：
```
Datetime=2024-01-01 10:30:45 SyslogID=106023 Severity=4 
SourceIP=192.168.1.100 SourcePort=51234 
DestinationIP=8.8.8.8 DestinationPort=443 
Protocol=tcp Action=Built Duration=120 Bytes=4096
```

**Fortinet**：
```
date=2024-01-01,time=10:30:45,logid=0000000013,
type=traffic,subtype=forward,level=notice,
srcip=192.168.1.100,srcport=51234,
dstip=8.8.8.8,dstport=443
```

### 標準欄位對應

| Cisco ASA 欄位 | 說明 | 對應 Fortinet |
|---|---|---|
| `Datetime` | 日期時間 | `date` + `time` |
| `SyslogID` | Syslog 訊息 ID | `logid` |
| `Severity` | 嚴重程度 (1-7) | `level` |
| `SourceIP/SourcePort` | 來源 IP/埠號 | `srcip`/`srcport` |
| `DestinationIP/DestinationPort` | 目的地 IP/埠號 | `dstip`/`dstport` |
| `Protocol` | 通訊協定 | `proto` |
| `Action` | 動作 | `action` |
| `Duration` | 連線持續時間 | `duration` |
| `Bytes` | 傳輸位元組數 | `sentbyte`/`rcvdbyte` |

### 解析邏輯差異

**Cisco ASA**：
- 使用**鍵值對**格式：`key=value`
- 空格分隔不同欄位
- 需要正則表達式解析：`r'(\w+)=(".*?"|\'.*?\'|[^"\',\s]+)'`

**Fortinet**：
- 使用**逗號分隔**格式
- 等號分隔鍵值
- 較為規則的 CSV 風格

---

## 🔄 ETL Pipeline 流程

### Step 1: 日誌清洗 (`log_cleaning.py`)

**輸入**：原始 Cisco ASA 日誌檔案

**處理**：
1. 偵測檔案編碼（使用 chardet）
2. 解析鍵值對格式
3. 標準化欄位名稱到 `STANDARD_COLUMNS`
4. 收集唯一值統計
5. 新增 `batch_id` 和 `raw_log` 欄位

**輸出**：
- `processed_logs.csv` - 清洗後的結構化資料
- `log_unique_values.json` - 唯一值統計

**標準欄位**：
```python
STANDARD_COLUMNS = [
    "batch_id",
    "Datetime",
    "SyslogID",
    "Severity",
    "SourceIP",
    "SourcePort",
    "DestinationIP",
    "DestinationPort",
    "Duration",
    "Bytes",
    "Protocol",
    "Action",
    "Description",
    "raw_log",
]
```

### Step 2: 資料映射 (`log_mapping.py`)

**輸入**：`processed_logs.csv`

**處理**：
1. 欄位映射與轉換
2. 資料型態標準化（數值、時間等）
3. 缺失值處理
4. 準備特徵工程所需格式

**輸出**：
- `preprocessed_data.csv` - 預處理完成的資料

---

## 📊 UI 介面設計

### 1. 檔案上傳區

```python
uploaded_files = st.file_uploader(
    "選擇 Cisco ASA 日誌檔案 (支援多檔案選擇)",
    type=["csv", "txt", "log", "gz"],
    accept_multiple_files=True,
    help="支援格式：CSV, TXT, LOG, GZ | 最大檔案大小：2GB"
)
```

**特點**：
- 支援多檔案選擇
- 顯示檔案清單與大小
- 支援壓縮檔格式

### 2. 輸出設定區

```python
output_dir = st.text_input(
    "輸出目錄",
    value="./cisco_etl_output",
    help="處理後的檔案將儲存在此目錄"
)

show_progress = st.checkbox(
    "顯示詳細進度",
    value=True
)
```

### 3. 執行區

- 進度條顯示（0% → 30% → 90% → 100%）
- 狀態訊息更新
- 錯誤處理與除錯資訊

### 4. 結果顯示區

**統計指標**：
- Batch ID
- 處理記錄數
- 處理時間

**輸出檔案**：
- 檔案路徑顯示
- 檔案大小資訊
- 下載按鈕

---

## 🔌 整合設定

### ui_app.py 更新

**匯入模組**：
```python
from ui_pages import (
    apply_dark_theme,
    data_cleaning,
    etl_ui,  # ← 新增
    log_monitor,
    model_inference,
    notifications,
    training_ui,
    visualization,
)
```

**頁面註冊**：
```python
_RAW_PAGES = {
    "ETL 處理": etl_ui.app,  # ← 新增
    "模型訓練": training_ui.app,
    "通知模組": notifications.app,
    # ...
}

PAGE_EMOJIS = {
    "ETL 處理": "🔧",  # ← 新增
    # ...
}

PAGE_ICONS = {
    "ETL 處理": "tools",  # ← 新增
    # ...
}

PAGE_DESCRIPTIONS = {
    "ETL 處理": "執行 Cisco ASA 日誌的清洗與預處理。",  # ← 新增
    # ...
}
```

---

## 🎨 UI 功能亮點

### 1. 多檔案支援
- 可一次選擇多個日誌檔案
- 顯示檔案清單與大小資訊
- 目前處理第一個檔案（可擴展為批次處理）

### 2. 進度追蹤
```python
# 階段 1: 準備 (10%)
status_text.text("📋 初始化 ETL Pipeline...")

# 階段 2: 執行 (30%)
status_text.text("🔄 執行日誌清洗與映射...")

# 階段 3: 完成 (100%)
status_text.text("🎉 所有處理已完成")
```

### 3. 錯誤處理
- 例外捕捉與顯示
- 詳細的除錯資訊展開區
- 自動清理臨時檔案

### 4. 結果展示
- 即時統計指標（Batch ID、記錄數、時間）
- 輸出檔案資訊（路徑、大小）
- 下載功能（預處理資料）

### 5. 說明文件
- Cisco ASA 格式說明
- 標準欄位列表
- 與 Fortinet 的差異說明
- 使用步驟指引

---

## 🧪 測試建議

### 1. 基本功能測試
```python
# 測試流程：
1. 啟動 Cisco UI：python -m Cisco_ui.ui_app
2. 導航到「ETL 處理」頁面
3. 上傳測試日誌檔案（.csv 或 .txt）
4. 執行 ETL 處理
5. 檢查輸出檔案與統計資訊
```

### 2. 格式相容性測試
- 測試不同格式：.csv, .txt, .log, .gz
- 測試大檔案（> 100MB）
- 測試編碼問題（UTF-8, Big5 等）

### 3. 錯誤處理測試
- 上傳無效格式檔案
- 上傳空檔案
- 輸出目錄權限問題

---

## 📚 使用範例

### 基本使用流程

1. **上傳檔案**
   - 點擊「選擇 Cisco ASA 日誌檔案」
   - 選擇一個或多個 .csv/.txt/.log 檔案
   - 查看檔案清單確認選擇

2. **設定輸出**
   - 指定輸出目錄（預設：`./cisco_etl_output`）
   - 選擇是否顯示詳細進度

3. **執行處理**
   - 點擊「🚀 開始處理」按鈕
   - 觀察進度條與狀態訊息
   - 等待處理完成

4. **查看結果**
   - 檢視統計指標（Batch ID、記錄數、時間）
   - 查看輸出檔案路徑與大小
   - 下載預處理資料

---

## 🔍 與 Fortinet ETL 的差異

| 項目 | Cisco ETL | Fortinet ETL |
|---|---|---|
| **日誌格式** | 鍵值對（空格分隔） | 逗號分隔 |
| **欄位數量** | 14 個標準欄位 | 19 個標準欄位 |
| **解析方式** | 正則表達式 | CSV reader |
| **特殊欄位** | SyslogID, Severity | logid, subtype, level |
| **時間格式** | 單一 Datetime | date + time |
| **位元組欄位** | 單一 Bytes | sentbyte + rcvdbyte |

---

## ✅ 完成項目

- [x] 建立 `etl_ui.py` UI 頁面
- [x] 實作檔案上傳與多檔案支援
- [x] 整合 `run_etl_pipeline` 函式
- [x] 新增進度追蹤與狀態顯示
- [x] 實作結果展示與下載功能
- [x] 新增詳細說明文件（格式、使用、差異）
- [x] 更新 `ui_app.py` 選單註冊
- [x] 錯誤處理與除錯資訊

---

## 🚀 後續建議

### 1. 功能擴展
- [ ] 支援批次處理多個檔案
- [ ] 新增壓縮檔自動解壓功能
- [ ] 實作資料預覽功能（顯示前 10 筆）
- [ ] 新增欄位映射自訂功能

### 2. 效能優化
- [ ] 大檔案串流處理（避免記憶體溢位）
- [ ] 多執行緒處理加速
- [ ] 進度條更精準的百分比計算

### 3. 使用者體驗
- [ ] 新增處理歷史記錄
- [ ] 實作檔案拖放上傳
- [ ] 新增處理時間預估
- [ ] 支援中斷與恢復處理

### 4. 整合功能
- [ ] 與特徵工程頁面串接
- [ ] 與模型訓練頁面串接
- [ ] 自動化 Pipeline 流程

---

## 📝 注意事項

1. **檔案格式**：確保上傳的是 Cisco ASA 格式的日誌
2. **記憶體使用**：大檔案可能需要較長處理時間
3. **臨時檔案**：處理完成後會自動清理臨時檔案
4. **輸出目錄**：確保有寫入權限

---

## 🎓 技術細節

### 相依套件
```python
import streamlit as st
import os
import time
import tempfile
from pathlib import Path
from typing import List, Tuple
from etl_pipeliner import run_etl_pipeline
```

### 核心函式

1. **`_save_uploaded_files()`**：儲存上傳檔案到臨時目錄
2. **`_display_file_info()`**：顯示檔案清單資訊
3. **`_display_etl_results()`**：展示處理結果與統計
4. **`app()`**：主 UI 函式

---

## 📞 問題排除

### 常見問題

**Q1: 上傳失敗**
- 檢查檔案大小是否超過 2GB
- 確認檔案格式是否支援

**Q2: 處理錯誤**
- 檢查日誌格式是否為 Cisco ASA
- 查看除錯資訊中的詳細錯誤訊息

**Q3: 下載失敗**
- 確認輸出檔案是否成功建立
- 檢查檔案路徑是否正確

---

**建立者**：GitHub Copilot  
**最後更新**：2025年10月8日
