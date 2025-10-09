# 資料前處理與訓練指南

## 問題說明

當您使用自行前處理的資料進行訓練時，系統可能會顯示以下錯誤：

```
❌ 訓練失敗：❌ 找不到目標欄位：is_attack
```

這表示系統找不到用於訓練的標籤欄位（目標欄位）。

## 解決方案

### 方案 1：使用資料檢查工具（推薦）

我們提供了一個資料檢查工具，可以自動分析您的資料並推薦合適的目標欄位：

```powershell
python data_inspector.py "C:\Users\U02020\AppData\Local\Temp\preprocessed_data.csv"
```

這個工具會：
- 📊 分析所有欄位的特性
- 🎯 自動識別可能的目標欄位
- 💡 提供具體的建議

### 方案 2：在 UI 中手動指定目標欄位

1. 開啟訓練介面
2. 在「🎯 目標欄位設定」區域選擇「手動指定」
3. 輸入您的目標欄位名稱（例如：`label`, `class`, `attack_type`）

### 方案 3：讓系統自動偵測（推薦新手）

系統現在支援智慧偵測目標欄位，會自動嘗試：

1. **標準欄位名稱**：`is_attack`, `crlevel`
2. **常見標籤欄位**：`label`, `target`, `class`, `category`, `severity`
3. **智慧偵測**：數值型且唯一值較少的欄位（可能是分類標籤）

只需在「🎯 目標欄位設定」選擇「自動偵測」即可。

## 資料準備建議

### 對於二元分類（攻擊偵測）

您的資料應該包含一個欄位來標示每筆記錄是否為攻擊，常見的欄位名稱：

- `is_attack`：0 = 正常，1 = 攻擊
- `label`：0/1 或 normal/attack
- `class`：0/1
- `attack_type`：normal 或具體攻擊類型

### 對於多類別分類（風險等級）

您的資料應該包含風險等級欄位：

- `crlevel`：0-6（風險等級）
- `severity`：low/medium/high/critical
- `priority`：數值等級

## 範例：使用 Python 新增標籤欄位

如果您的資料尚未標註，可以使用以下範例程式碼新增標籤：

```python
import pandas as pd

# 讀取您的資料
df = pd.read_csv("your_preprocessed_data.csv")

# 範例 1：根據某個條件建立二元標籤
# 假設 'action' 欄位包含 'deny' 或 'drop' 表示攻擊
df['is_attack'] = df['action'].isin(['deny', 'drop']).astype(int)

# 範例 2：根據多個條件建立標籤
# 假設根據 severity 欄位決定
def determine_attack(row):
    if row['severity'] in ['critical', 'high']:
        return 1
    return 0

df['is_attack'] = df.apply(determine_attack, axis=1)

# 範例 3：建立多類別標籤（風險等級）
severity_map = {
    'informational': 0,
    'low': 1,
    'medium': 2,
    'high': 3,
    'critical': 4
}
df['crlevel'] = df['severity'].map(severity_map)

# 儲存處理後的資料
df.to_csv("labeled_data.csv", index=False)
print(f"✅ 已新增標籤欄位，共 {len(df)} 筆資料")
print(f"標籤分佈：\n{df['is_attack'].value_counts()}")
```

## 常見問題

### Q1: 我的資料已經有標籤了，為什麼還是找不到？

**A:** 可能的原因：
1. 欄位名稱不是標準名稱（`is_attack` 或 `crlevel`）
2. 解決方法：使用「手動指定」功能，輸入您的實際欄位名稱

### Q2: 資料檢查工具報錯「FileNotFoundError」？

**A:** 檔案可能已被刪除或移動。請：
1. 重新上傳資料
2. 或直接在 UI 中使用上傳功能

### Q3: 智慧偵測選到錯誤的欄位？

**A:** 智慧偵測可能會選到看起來像標籤的欄位。請：
1. 使用「手動指定」明確指定正確的欄位
2. 或先使用 `data_inspector.py` 檢查所有候選欄位

### Q4: 我的資料沒有標籤，可以訓練嗎？

**A:** 不行。監督式學習必須有標籤資料。您需要：
1. 手動標註部分資料
2. 使用規則（如上面的 Python 範例）自動產生標籤
3. 考慮使用無監督學習方法（異常偵測等）

## 快速測試

使用以下命令快速測試您的資料：

```powershell
# 1. 檢查資料結構
python data_inspector.py "your_data.csv"

# 2. 如果找到合適的目標欄位，直接使用 UI 訓練
# 在 UI 中選擇「自動偵測」或「手動指定」

# 3. 如果需要新增標籤，使用上面的 Python 範例
```

## 技術支援

如果您遇到問題，請提供以下資訊：

1. 資料的欄位列表（使用 `data_inspector.py` 產生）
2. 您期望使用哪個欄位作為標籤
3. 完整的錯誤訊息

---

**更新日誌**：
- ✅ 新增自動目標欄位偵測功能
- ✅ 新增手動指定目標欄位功能
- ✅ 新增資料檢查工具 `data_inspector.py`
- ✅ 改善錯誤訊息，提供具體解決方案
