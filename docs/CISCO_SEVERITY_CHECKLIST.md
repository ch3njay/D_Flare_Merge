# ✅ Cisco ASA Severity 修正檢查清單

## 🎯 快速驗證步驟

### 1. 執行自動化測試
```bash
python test_severity_colors.py
```
**預期結果**: 5/5 測試通過 ✅

---

### 2. 檢查配置檔案

#### notification_models.py
```python
# ✅ 應該包含 0-7 級別
SEVERITY_LABELS = {
    0: "緊急", 1: "警報", 2: "嚴重", 3: "錯誤",
    4: "警告", 5: "通知", 6: "資訊", 7: "除錯"
}
```

#### Cisco_ui/utils_labels.py
```python
# ✅ 應該包含 8 種顏色
SEVERITY_COLORS = {
    0: "#8B0000", 1: "#DC143C", 2: "#FF4500", 3: "#FF8C00",
    4: "#FFD700", 5: "#90EE90", 6: "#87CEEB", 7: "#D3D3D3"
}

# ✅ 應該有 3 個輔助函式
get_severity_color()
get_severity_label()
format_severity_display()
```

---

### 3. 檢查推播邏輯

#### Cisco_ui/ui_pages/log_monitor.py (Line 368)
```python
# ✅ 應該檢查 0-4
if not df["Severity"].astype(str).isin(["0", "1", "2", "3", "4"]).any():
```

#### Cisco_ui/notifier.py (Line 107-110)
```python
# ✅ 應該過濾 0-4
work = work[work["_severity"].isin([0, 1, 2, 3, 4])]
```

---

### 4. 視覺化驗證

| Severity | 顏色 | 標籤 | 視覺檢查 |
|----------|------|------|----------|
| 0 | #8B0000 深紅 | 緊急 | □ 確認 |
| 1 | #DC143C 猩紅 | 警報 | □ 確認 |
| 2 | #FF4500 橙紅 | 嚴重 | □ 確認 |
| 3 | #FF8C00 深橙 | 錯誤 | □ 確認 |
| 4 | #FFD700 金色 | 警告 | □ 確認 |
| 5 | #90EE90 淺綠 | 通知 | □ 確認 |
| 6 | #87CEEB 天藍 | 資訊 | □ 確認 |
| 7 | #D3D3D3 淺灰 | 除錯 | □ 確認 |

---

### 5. 功能驗證

#### 推播觸發
- [ ] Severity 0: 不處理（過濾）
- [ ] Severity 1-4: 觸發推播 ✅
- [ ] Severity 5-7: 不觸發推播 ✅

#### UI 顯示
- [ ] 高風險事件顯示紅/橙色
- [ ] 正常事件顯示綠/藍/灰色
- [ ] 標籤顯示正確的中文名稱

#### 資料處理
- [ ] Severity 0 在 parser 階段過濾
- [ ] Severity 1-4 標記 is_attack=1
- [ ] Severity 5-7 標記 is_attack=0

---

## 📁 修正檔案清單

- [x] `notification_models.py` - SEVERITY_LABELS (0-7)
- [x] `Cisco_ui/utils_labels.py` - SEVERITY_COLORS (8 級)
- [x] `Cisco_ui/utils_labels.py` - 輔助函式 (3 個)
- [x] `Cisco_ui/ui_pages/log_monitor.py` - 高風險判斷 (0-4)
- [x] `Cisco_ui/notifier.py` - 推播過濾 (0-4)

---

## 📚 相關文件

- [x] `docs/CISCO_SEVERITY_VISUALIZATION_GUIDE.md` - 視覺化指南
- [x] `CISCO_SEVERITY_FIX_REPORT.md` - 修正報告
- [x] `test_severity_colors.py` - 自動化測試

---

## 🚀 下一步建議

1. **執行完整測試**
   ```bash
   python test_severity_colors.py
   python rigorous_test_suite.py
   ```

2. **啟動 UI 測試**
   ```bash
   streamlit run Cisco_ui/ui_app.py
   ```

3. **驗證推播功能**
   - 上傳包含不同 Severity 的測試日誌
   - 確認 Severity 0-4 觸發通知
   - 確認顏色顯示正確

4. **視覺檢查**
   - 檢查儀表板的 Severity 顯示
   - 檢查圖表的顏色配置
   - 確認通知訊息的標籤

---

## ✅ 完成確認

- [ ] 所有測試通過
- [ ] UI 顯示正確
- [ ] 推播功能正常
- [ ] 文件已建立

**檢查日期**: __________  
**檢查人員**: __________  
**確認簽名**: __________
