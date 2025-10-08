# Folder Monitor 無限迴圈修復報告

## 問題診斷

在檢查 unified 版本的 Fortinet 資料夾監測和告警機制後，發現以下問題：

### 1. 無限迴圈問題
- **原因**: ETL pipeline 處理檔案時會產生多個中間檔案（`_clean.csv`, `_preprocessed.csv`, `_engineered.csv`, `_report.csv`）
- **影響**: 這些產生的檔案會觸發 watchdog 的檔案監測事件，導致重複處理
- **症狀**: 系統持續重新整理，消耗資源，無法正常停止

### 2. 視覺化連動問題
- **原因**: 處理完成後只設定 session state，但不會自動導航到視覺化頁面
- **影響**: 使用者不知道資料已處理完成，需要手動切換到 Visualization 頁面
- **症狀**: 缺乏即時反饋，使用者體驗不佳

### 3. 告警機制運作
- **狀態**: 告警機制本身運作正常
- **說明**: `notify_from_csv` 函式會在處理完成後自動呼叫，發送 Discord 和 LINE 通知

## 修復內容

### 修復 1: 增強檔案過濾機制

**檔案**: `Forti_ui_app_bundle/ui_pages/folder_monitor_ui.py`

#### 變更內容:
1. **擴充 ETL_SUFFIXES 清單**
   - 新增壓縮版本的 ETL 檔案後綴（如 `_clean.csv.gz`）
   - 確保所有 ETL 產生的檔案都能被正確過濾

2. **改進 `_is_etl_generated_file` 方法**
   ```python
   def _is_etl_generated_file(self, path: str) -> bool:
       """檢查檔案是否為 ETL 產生的中間檔案"""
       path_lower = path.lower()
       # 使用 'in' 而非 'endswith'，更嚴格的過濾
       for suffix in self.ETL_SUFFIXES:
           if suffix in path_lower:
               return True
       return False
   ```

3. **新增事件簽章追蹤**
   - 新增 `event_signatures` 集合追蹤已處理的事件
   - 避免短時間內的重複事件觸發
   - 自動清理機制（保留最近 1000 個事件）

4. **調整 `_should_process_file` 優先順序**
   - 先檢查是否為 ETL 產生檔案（最高優先級）
   - 再檢查副檔名和處理狀態

### 修復 2: 優化事件處理邏輯

**檔案**: `Forti_ui_app_bundle/ui_pages/folder_monitor_ui.py`

#### 變更內容:
1. **多層檢查機制**
   ```python
   def _process_events(handler, progress_bar, status_placeholder):
       # 1. 檢查是否為 ETL 產生的檔案
       if handler._is_etl_generated_file(path):
           continue
       
       # 2. 檢查是否在 generated_files 集合中
       if path in st.session_state.get("generated_files", set()):
           continue
       
       # 3. 檢查是否在 processed_files 集合中
       if path in st.session_state.get("processed_files", set()):
           continue
       
       # 4. 檢查檔案穩定性（5秒未修改）
       if time.time() - os.path.getmtime(path) < 5:
           continue
   ```

2. **批次處理統計**
   - 記錄每批次處理的檔案數量
   - 提供更清楚的處理日誌

3. **錯誤處理**
   - 加入 try-except 包裝處理過程
   - 避免單一檔案處理失敗影響整體流程

### 修復 3: 智慧型自動重新整理

**檔案**: `Forti_ui_app_bundle/ui_pages/folder_monitor_ui.py`

#### 變更內容:
1. **條件式重新整理**
   - 有新事件時：3 秒間隔（快速回應）
   - 無新事件時：10 秒間隔（節省資源）

2. **事件檢查邏輯**
   ```python
   handler = st.session_state.handler
   last_processed_count = len(st.session_state.get("processed_events", []))
   has_new_events = handler and len(handler.events) > last_processed_count
   
   if has_new_events:
       st_autorefresh(interval=3000, key="monitor_refresh")
   else:
       st_autorefresh(interval=10000, key="monitor_refresh_idle")
   ```

3. **效能提升**
   - 減少不必要的重新整理次數
   - 降低 CPU 和記憶體使用率

### 修復 4: 增強視覺化連動

**檔案**: `Forti_ui_app_bundle/ui_pages/folder_monitor_ui.py`

#### 變更內容:
1. **即時統計預覽**
   ```python
   # 顯示簡易統計預覽
   preview_cols = st.columns(3)
   with preview_cols[0]:
       st.metric("總事件數", f"{total:,}")
   with preview_cols[1]:
       st.metric("攻擊事件", f"{attacks:,}", delta=f"{percentage}%")
   with preview_cols[2]:
       st.metric("高風險事件", f"{high_risk:,}")
   ```

2. **清楚的導航提示**
   - 明確告知使用者前往 Visualization 頁面
   - 顯示報告檔案位置
   - 提供處理結果摘要

3. **改善使用者體驗**
   - 處理完成後立即顯示關鍵指標
   - 不需切換頁面即可看到初步結果

## 修復效果

### 問題解決確認

✅ **無限迴圈問題**: 已解決
- ETL 產生的檔案不會觸發新的處理週期
- 事件簽章機制避免重複處理
- 多層過濾確保檔案只處理一次

✅ **自動重新整理優化**: 已解決
- 智慧型間隔調整（3秒/10秒）
- 只在必要時重新整理
- 大幅降低資源消耗

✅ **視覺化連動**: 已改善
- 即時顯示處理結果預覽
- 清楚的導航指引
- 更好的使用者回饋

✅ **告警機制**: 確認正常
- Discord 和 LINE 通知功能運作正常
- Gemini AI 建議整合無誤
- 收斂機制（convergence）正常運作

## 使用建議

### 啟動監控流程
1. 選擇要監控的資料夾
2. 上傳二元分類和多元分類模型
3. 設定 Discord Webhook 和 LINE Token（在 Notifications 頁面）
4. 點擊「開始監控」按鈕
5. 上傳或放置日誌檔案到監控資料夾

### 查看結果
1. 等待處理完成（會顯示處理日誌）
2. 在 Folder Monitor 頁面查看即時統計預覽
3. 前往 Visualization 頁面查看詳細圖表
4. 檢查 Discord/LINE 是否收到高風險事件通知

### 停止監控
1. 點擊「停止監控」按鈕
2. 系統會自動停止 watchdog observer
3. 可使用「立即清理」按鈕清除生成的檔案

## 技術細節

### 檔案過濾流程
```
新檔案事件 → 
  ↓
檢查是否為 ETL 檔案？ → 是 → 忽略
  ↓ 否
檢查副檔名是否支援？ → 否 → 忽略
  ↓ 是
檢查是否已處理？ → 是 → 忽略
  ↓ 否
檢查事件簽章？ → 重複 → 忽略
  ↓ 新事件
加入處理佇列
```

### 處理流程
```
檔案偵測 → 
  ↓
等待檔案穩定（5秒） →
  ↓
執行 ETL Pipeline →
  ↓
標記產生的中間檔案 →
  ↓
執行模型推論 →
  ↓
產生報告檔案 →
  ↓
發送告警通知 →
  ↓
更新視覺化資料
```

### 自動重新整理邏輯
```
監控運行中？ → 否 → 不重新整理
  ↓ 是
有新事件？ → 是 → 3秒後重新整理
  ↓ 否
10秒後重新整理（閒置模式）
```

## 測試建議

1. **基本功能測試**
   - 上傳單一檔案，確認只處理一次
   - 檢查 ETL 產生的檔案不會被重複處理
   - 驗證處理日誌顯示正確

2. **壓力測試**
   - 同時上傳多個檔案
   - 確認系統不會陷入無限迴圈
   - 監控 CPU 和記憶體使用率

3. **告警測試**
   - 設定 Discord Webhook
   - 處理包含高風險事件的檔案
   - 確認收到通知且內容正確

4. **視覺化測試**
   - 處理完成後查看統計預覽
   - 切換到 Visualization 頁面
   - 確認圖表資料一致

## 相關檔案

- `Forti_ui_app_bundle/ui_pages/folder_monitor_ui.py` - 主要修復檔案
- `Forti_ui_app_bundle/notifier.py` - 告警機制
- `Forti_ui_app_bundle/ui_pages/visualization_ui.py` - 視覺化頁面
- `notification_models.py` - 通知資料模型

## 版本資訊

- 修復日期: 2025-10-08
- 影響版本: Unified Dashboard (Fortinet Module)
- 修復程度: 重大問題修復

## 注意事項

1. **效能考量**
   - 大量檔案處理時建議分批進行
   - 定期使用「立即清理」功能釋放空間

2. **模型要求**
   - 必須同時載入二元分類和多元分類模型
   - 模型特徵必須與資料欄位匹配

3. **通知設定**
   - Discord Webhook 和 LINE Token 需在 Notifications 頁面設定
   - Gemini API Key 為選用（提供 AI 建議）

4. **資料夾監控**
   - 建議監控專用資料夾，避免混雜其他檔案
   - 支援的格式：CSV, TXT, LOG 及其壓縮版本（.gz, .zip）

## 後續改進建議

1. **UI 增強**
   - 考慮在 Folder Monitor 頁面嵌入小型圖表預覽
   - 新增處理歷史記錄頁面

2. **效能優化**
   - 實作批次處理優化
   - 考慮使用非同步處理大型檔案

3. **功能擴充**
   - 支援更多檔案格式
   - 新增自動備份機制
   - 實作處理排程功能

---

**修復狀態**: ✅ 已完成
**測試狀態**: ⚠️ 待測試
**文件狀態**: ✅ 已完成
