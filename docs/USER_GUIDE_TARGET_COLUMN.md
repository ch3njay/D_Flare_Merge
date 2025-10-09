# 🎯 目標欄位彈性偵測功能 - 使用者指南

## ✨ 新功能概覽

您遇到的「找不到目標欄位：is_attack」錯誤已經完全解決！現在系統支援：

✅ **自動偵測目標欄位** - 智慧識別您資料中的標籤欄位  
✅ **手動指定目標欄位** - 明確指定您的標籤欄位名稱  
✅ **資料檢查工具** - 分析資料並推薦最佳目標欄位  
✅ **改善的錯誤訊息** - 提供具體的解決建議

---

## 🚀 快速解決方案

### 方案 1：使用資料檢查工具（最推薦）

```powershell
python data_inspector.py "C:\Users\U02020\AppData\Local\Temp\preprocessed_data.csv"
```

這個工具會：
- 📊 分析您的資料結構
- 🎯 自動識別可能的目標欄位
- 💡 提供具體使用建議

### 方案 2：在 UI 中使用（最簡單）

1. 開啟 D-FLARE 訓練介面
2. 上傳您的資料
3. 在「🎯 目標欄位設定」選擇：
   - **自動偵測**：讓系統自動找目標欄位
   - **手動指定**：輸入您的標籤欄位名稱
4. 開始訓練

### 方案 3：在程式碼中使用

```python
from Cisco_ui.training_pipeline.pipeline_main import CiscoTrainingPipeline

# 自動偵測
pipeline = CiscoTrainingPipeline(
    task_type="binary",
    target_column=None  # 或不指定此參數
)

# 或手動指定
pipeline = CiscoTrainingPipeline(
    task_type="binary",
    target_column="your_label_column_name"
)

results = pipeline.run("your_data.csv")
```

---

## 📚 詳細文件

### 📖 使用指南
- **`docs/TARGET_COLUMN_GUIDE.md`** - 完整的使用指南
  - 如何準備資料
  - 如何新增標籤欄位
  - 常見問題解答
  - 程式碼範例

### 🔧 技術文件
- **`TARGET_COLUMN_SOLUTION_SUMMARY.md`** - 技術實作總結
  - 實作細節
  - 偵測策略
  - 效能評估

### 💡 快速範例
- **`QUICK_START_GUIDE.py`** - 互動式快速指南
  ```powershell
  python QUICK_START_GUIDE.py
  ```

---

## 🛠️ 新增的工具

### 1. 資料檢查工具（`data_inspector.py`）

**功能**：
- 分析 CSV 檔案結構
- 自動識別可能的目標欄位
- 提供詳細的分析報告

**使用方式**：
```powershell
python data_inspector.py "your_data.csv"
```

### 2. 功能測試工具（`test_target_column_detection.py`）

**功能**：
- 測試目標欄位自動偵測
- 驗證手動指定功能
- 確保功能正常運作

**使用方式**：
```powershell
python test_target_column_detection.py
```

---

## 💡 常見使用情境

### 情境 1：資料已有標籤欄位（如 'label', 'class' 等）

**解決方案**：使用自動偵測或手動指定

```python
# UI 中：選擇「自動偵測」或「手動指定」輸入 "label"

# 程式碼中：
pipeline = CiscoTrainingPipeline(target_column="label")
```

### 情境 2：資料使用標準欄位（'is_attack' 或 'crlevel'）

**解決方案**：直接使用，系統會自動識別

```python
# 不需要特別設定，系統會自動找到標準欄位
pipeline = CiscoTrainingPipeline(task_type="binary")
```

### 情境 3：資料沒有明顯的標籤欄位

**解決方案**：
1. 先使用 `data_inspector.py` 檢查
2. 如果有候選欄位，使用手動指定
3. 如果完全沒有，需要先建立標籤欄位

```python
# 先檢查
# python data_inspector.py "data.csv"

# 根據建議使用
pipeline = CiscoTrainingPipeline(target_column="推薦的欄位名稱")
```

### 情境 4：資料完全沒有標籤

**解決方案**：需要先建立標籤欄位

```python
import pandas as pd

df = pd.read_csv("your_data.csv")

# 範例：根據 action 欄位建立標籤
df['is_attack'] = (df['action'] == 'deny').astype(int)

# 儲存
df.to_csv("labeled_data.csv", index=False)

# 然後使用 labeled_data.csv 進行訓練
```

詳細的標籤建立方法請參考 `docs/TARGET_COLUMN_GUIDE.md`

---

## 🎯 偵測策略說明

系統會按照以下優先順序尋找目標欄位：

### 1️⃣ 使用者指定（最高優先）
如果您明確指定了 `target_column` 參數，系統會優先使用

### 2️⃣ 標準欄位名稱
- 二元分類：`is_attack`
- 多類別分類：`crlevel`

### 3️⃣ 常見標籤欄位
系統會自動識別以下常見名稱（不區分大小寫）：
- `label`, `target`, `class`, `y`
- `attack_type`, `category`, `classification`
- `severity`, `priority`, `risk_level`
- `threat_level`, `status`, `type`

### 4️⃣ 智慧偵測
系統會分析數值型欄位，識別：
- 唯一值數量較少（< 20）
- 唯一值比例很低（< 1%）
- 可能是分類標籤的欄位

---

## 📊 測試結果

所有測試均已通過 ✅：

```
總測試數：6
通過：6 ✅
失敗：0 ❌
成功率：100.0%
```

測試涵蓋：
- ✅ 標準標籤欄位自動偵測
- ✅ 常見標籤欄位自動偵測
- ✅ 智慧偵測（無明顯標籤）
- ✅ 手動指定目標欄位
- ✅ 完整訓練流程

---

## 🔗 相關資源

### 文件
- 📖 `docs/TARGET_COLUMN_GUIDE.md` - 完整使用指南
- 🔧 `TARGET_COLUMN_SOLUTION_SUMMARY.md` - 技術實作總結
- 📝 `README.md` - 系統主文件

### 工具
- 🔍 `data_inspector.py` - 資料分析工具
- 🧪 `test_target_column_detection.py` - 功能測試
- 💡 `QUICK_START_GUIDE.py` - 快速開始指南

### 核心程式碼
- 📦 `Cisco_ui/training_pipeline/pipeline_main.py` - 訓練管線
- 🖥️ `Cisco_ui/ui_pages/training_ui.py` - UI 介面

---

## ❓ 需要協助？

### 如果您遇到問題

1. **先查看錯誤訊息**
   - 新的錯誤訊息會提供具體的解決建議

2. **使用資料檢查工具**
   ```powershell
   python data_inspector.py "your_data.csv"
   ```

3. **查看詳細指南**
   - `docs/TARGET_COLUMN_GUIDE.md` 包含常見問題解答

4. **執行測試**
   ```powershell
   python test_target_column_detection.py
   ```
   確認功能是否正常運作

---

## 📝 更新日誌

**版本 2.0** - 2025-10-09

✅ 新增目標欄位自動偵測功能  
✅ 新增手動指定目標欄位功能  
✅ 新增資料檢查分析工具  
✅ 改善錯誤訊息與使用者體驗  
✅ 新增完整的文件與測試  
✅ 保持向後相容性

---

**祝您使用愉快！🎉**

如有任何問題或建議，歡迎回饋！
