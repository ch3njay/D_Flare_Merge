# CSV 格式錯誤解決方案

## 問題描述

用戶在訓練過程中遇到以下錯誤：
```
Training failed: Error tokenizing data. C error: Expected 4 fields in line 22, saw 6
```

這個錯誤表示 CSV 文件在第22行有格式問題 - 預期有4個欄位，但實際發現了6個欄位。

## 實施的解決方案

### 1. 改善 DataLoader 類別的 CSV 讀取

**文件位置**: `Forti_ui_app_bundle/training_pipeline/data_loader.py`

**改進內容**:
- 添加了三級容錯機制：
  1. **標準讀取**: 使用 `pd.read_csv(file_path)`
  2. **容錯模式**: 使用 `error_bad_lines=False` 跳過有問題的行
  3. **Python 引擎**: 使用 `engine='python'` 和寬鬆參數

```python
def load_data(self, file_path: str) -> pd.DataFrame:
    """安全載入 CSV 文件，處理格式不一致問題"""
    try:
        # 第一次嘗試：標準讀取
        df = pd.read_csv(file_path)
    except pd.errors.ParserError as e:
        # 第二次嘗試：容錯模式
        df = pd.read_csv(
            file_path,
            error_bad_lines=False,
            warn_bad_lines=True,
            on_bad_lines='warn'
        )
    # 第三次嘗試：Python 引擎...
```

### 2. 更新其他 CSV 讀取位置

**文件位置**:
- `Cisco_ui/training_pipeline/model_builder.py`
- `Forti_ui_app_bundle/training_pipeline/optuna_tuner.py`

**改進內容**: 為所有 CSV 讀取操作添加了相同的容錯機制。

### 3. 在 UI 中添加 CSV 診斷功能

**文件位置**:
- `Cisco_ui/ui_pages/training_ui.py`
- `Forti_ui_app_bundle/ui_pages/training_ui.py`

**新增功能**:
- 自動檢測 CSV 格式錯誤
- 提供詳細的診斷信息和修復建議
- 包含自動修復工具按鈕

### 4. 創建獨立的 CSV 診斷工具

**文件位置**: `csv_diagnostics.py`

**功能**:
- 完整的 CSV 文件診斷
- 識別常見格式問題
- 提供修復建議
- 可以獨立運行的診斷工具

## 常見 CSV 格式問題及解決方法

### 問題類型 1: 欄位數量不一致
**原因**: 某些行的逗號數量與標題行不匹配
**解決方法**:
- 檢查數據中是否有未轉義的逗號
- 使用雙引號包圍包含逗號的文本字段

### 問題類型 2: 引號格式錯誤
**原因**: 文本字段中的引號沒有正確轉義
**解決方法**:
- 確保文本字段使用正確的引號格式
- 使用 Excel 重新保存 CSV 文件

### 問題類型 3: 換行符問題
**原因**: 文本字段中包含換行符
**解決方法**:
- 移除或替換文本中的換行符
- 使用適當的文本編輯器處理

## 使用建議

### 對用戶的建議:
1. **預防性檢查**: 在上傳大型 CSV 文件前，先用前100行進行測試
2. **格式標準化**: 使用 Excel 或專業工具確保 CSV 格式正確
3. **備份原始數據**: 在修復前備份原始文件
4. **逐步測試**: 如果問題持續，嘗試分批處理數據

### 對開發者的建議:
1. **持續監控**: 監控用戶報告的新格式問題
2. **日誌記錄**: 記錄所有 CSV 讀取錯誤以便分析
3. **用戶回饋**: 收集用戶對診斷工具的使用回饋
4. **格式驗證**: 考慮添加上傳前的格式驗證

## 技術細節

### 容錯參數說明:
- `error_bad_lines=False`: 跳過無法解析的行
- `warn_bad_lines=True`: 顯示警告信息
- `on_bad_lines='warn'`: 現代 pandas 版本的參數
- `engine='python'`: 使用 Python 解析引擎（較慢但更寬鬆）
- `sep=None`: 自動檢測分隔符
- `quoting=3`: 忽略引號處理

### 性能考量:
- 標準讀取是最快的方法
- 容錯模式會略微降低性能
- Python 引擎是最慢但最寬鬆的選項

## 測試驗證

建議使用以下測試案例驗證修復效果:
1. 正常格式的 CSV 文件
2. 包含不一致欄位數量的 CSV 文件
3. 包含未轉義逗號的 CSV 文件
4. 包含引號問題的 CSV 文件
5. 大型 CSV 文件（測試性能影響）

## 未來改進方向

1. **更智能的格式檢測**: 使用機器學習方法自動識別和修復格式問題
2. **實時預覽**: 在上傳時提供 CSV 內容預覽
3. **格式轉換**: 支持其他格式（如 Excel）的直接導入
4. **批量處理**: 支持多文件批量格式檢查和修復