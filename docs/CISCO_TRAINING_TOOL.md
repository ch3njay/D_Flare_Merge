# Cisco ASA 訓練工具新增說明

## 📋 變更摘要

為 Cisco ASA 模組新增了完整的機器學習模型訓練工具，使其功能與 Fortinet 模組對等。

## 🎯 新增功能

### 1. 訓練管線主程式
**檔案**: `Cisco_ui/training_pipeline/pipeline_main.py`

#### 主要類別：`CiscoTrainingPipeline`

提供完整的訓練流程整合：

**功能特點**：
- ✅ 支援二元分類（攻擊偵測）
- ✅ 支援多元分類（風險等級）
- ✅ 整合 LightGBM、XGBoost、CatBoost
- ✅ 自動資料分割和驗證
- ✅ 模型評估和效能比較
- ✅ 自動儲存模型和報告

**使用範例**：
```python
from Cisco_ui.training_pipeline.pipeline_main import CiscoTrainingPipeline

# 建立訓練管線
pipeline = CiscoTrainingPipeline(
    task_type="binary",  # 或 "multiclass"
    config={
        "test_size": 0.2,
        "random_state": 42,
        "output_dir": "./artifacts"
    }
)

# 執行訓練
results = pipeline.run("training_data.csv")

# 查看結果
if results["success"]:
    print(f"最佳模型: {results['best_model']}")
    print(f"準確率: {results['best_accuracy']:.4f}")
```

### 2. 訓練介面
**檔案**: `Cisco_ui/ui_pages/training_ui.py`

#### UI 功能

**頁面結構**：
1. **檔案上傳區**
   - 支援 CSV 格式
   - 即時檔案資訊顯示

2. **訓練參數設定**
   - 任務類型選擇（二元/多元分類）
   - 測試集比例調整
   - 隨機種子設定
   - 輸出目錄配置

3. **訓練執行與監控**
   - 即時進度顯示
   - 訓練日誌輸出
   - 錯誤處理和提示

4. **結果展示**
   - 最佳模型標示
   - 模型效能比較表
   - 儲存路徑顯示
   - 下載和使用指引

**介面特色**：
- 🎨 深色主題整合
- 📊 即時進度條
- 💡 清楚的使用說明
- ⚠️ 完整的錯誤處理
- 📁 檔案路徑追蹤

### 3. 選單整合
**檔案**: `Cisco_ui/ui_app.py`

#### 變更內容

**新增頁面**：
```python
_RAW_PAGES: Mapping[str, Callable[[], None]] = {
    "模型訓練": training_ui.app,  # ← 新增
    "通知模組": notifications.app,
    "Log 擷取": log_monitor.app,
    "模型推論": model_inference.app,
    "圖表預覽": visualization.app,
    "資料清理": data_cleaning.app,
}
```

**頁面配置**：
- 圖示：🤖 gear
- 描述：訓練二元/多元分類模型，支援多種演算法
- 位置：選單首位（最常用功能）

## 📐 架構設計

### 訓練流程圖

```
上傳 CSV 檔案
    ↓
資料載入與驗證
    ↓
特徵分離 (X, y)
    ↓
資料分割 (Train/Test)
    ↓
模型訓練
    ├─ LightGBM
    ├─ XGBoost
    └─ CatBoost
    ↓
模型評估
    ├─ 準確率計算
    ├─ 混淆矩陣
    └─ 分類報告
    ↓
選擇最佳模型
    ↓
儲存結果
    ├─ models/binary_*.pkl
    └─ reports/binary_evaluation.json
    ↓
顯示結果
```

### 檔案結構

```
Cisco_ui/
├── training_pipeline/
│   ├── __init__.py
│   ├── config.py           # 訓練配置
│   ├── model_builder.py    # 模型建構器
│   ├── evaluator.py        # 評估器
│   ├── trainer.py          # 訓練執行器
│   └── pipeline_main.py    # ← 新增：主程式
├── ui_pages/
│   ├── __init__.py
│   ├── training_ui.py      # ← 新增：訓練介面
│   ├── log_monitor.py
│   ├── model_inference.py
│   ├── notifications.py
│   ├── visualization.py
│   └── data_cleaning.py
└── ui_app.py              # ← 更新：加入訓練頁面
```

## 🔧 技術細節

### 依賴模組

**必要套件**：
```python
- pandas          # 資料處理
- numpy           # 數值運算
- scikit-learn    # 機器學習基礎
- lightgbm        # LightGBM 模型
- xgboost         # XGBoost 模型
- catboost        # CatBoost 模型
- joblib          # 模型序列化
- streamlit       # UI 框架
```

### 資料格式要求

#### 二元分類 (Binary Classification)
```csv
feature1,feature2,feature3,...,is_attack
1.2,3.4,5.6,...,0
2.3,4.5,6.7,...,1
...
```
- **目標欄位**：`is_attack`
- **標籤值**：0 (正常) 或 1 (攻擊)

#### 多元分類 (Multiclass Classification)
```csv
feature1,feature2,feature3,...,crlevel
1.2,3.4,5.6,...,0
2.3,4.5,6.7,...,4
...
```
- **目標欄位**：`crlevel`
- **標籤值**：0-4 (風險等級)

### 模型配置

**LightGBM 參數**：
```python
{
    "n_estimators": 100,
    "learning_rate": 0.1,
    "max_depth": 7,
    "num_leaves": 31,
    "random_state": 42
}
```

**XGBoost 參數**：
```python
{
    "n_estimators": 100,
    "learning_rate": 0.1,
    "max_depth": 7,
    "random_state": 42
}
```

**CatBoost 參數**：
```python
{
    "iterations": 100,
    "learning_rate": 0.1,
    "depth": 7,
    "random_state": 42,
    "verbose": False
}
```

### 輸出格式

#### 模型檔案
```
artifacts/
└── 20251008_123456/
    └── models/
        ├── binary_lightgbm.pkl
        ├── binary_xgboost.pkl
        └── binary_catboost.pkl
```

#### 評估報告
```json
{
  "LightGBM": {
    "accuracy": 0.9523,
    "classification_report": {...},
    "confusion_matrix": [[...], [...]]
  },
  "XGBoost": {...},
  "CatBoost": {...}
}
```

## 🚀 使用指南

### 1. 啟動訓練工具

**方法一：直接執行**
```bash
cd c:\Users\U02020\Desktop\D_Flare_Merge-master
python launch_unified_dashboard.py
```

**方法二：Streamlit 直接運行**
```bash
streamlit run unified_ui/app.py
```

### 2. 選擇 Cisco 模組

在統一介面側邊欄：
1. 點擊 Cisco 平台圖示
2. 展開「功能目錄」
3. 選擇「🤖 模型訓練」

### 3. 準備訓練資料

**資料檢查清單**：
- ✅ CSV 格式檔案
- ✅ 包含目標欄位（is_attack 或 crlevel）
- ✅ 特徵欄位為數值型態
- ✅ 無過多缺失值（< 10%）
- ✅ 資料筆數充足（建議 > 1000 筆）
- ✅ 類別平衡（不要過度偏斜）

### 4. 設定訓練參數

**建議設定**：
- **任務類型**：根據需求選擇
  - 二元分類：攻擊偵測
  - 多元分類：風險分級
- **測試集比例**：20% (預設值)
- **隨機種子**：42 (保證可重現)
- **輸出目錄**：./artifacts (預設值)

### 5. 執行訓練

1. 點擊「🚀 開始訓練」按鈕
2. 觀察進度條和日誌輸出
3. 等待訓練完成（約 1-5 分鐘）

### 6. 查看結果

**訓練完成後會顯示**：
- 🏆 最佳模型名稱和準確率
- 📈 所有模型效能比較
- 📁 模型和報告儲存位置
- 💡 後續使用提示

### 7. 使用訓練好的模型

前往「模型推論」頁面：
1. 上傳模型檔案（.pkl）
2. 載入測試資料
3. 執行預測
4. 查看結果

## 🔍 功能對比

| 功能 | Fortinet | Cisco | 說明 |
|------|----------|-------|------|
| 二元分類訓練 | ✅ | ✅ | 攻擊偵測 |
| 多元分類訓練 | ✅ | ✅ | 風險分級 |
| 多演算法支援 | ✅ | ✅ | LightGBM, XGBoost, CatBoost |
| Optuna 調參 | ✅ | ⚠️ | Cisco 暫未實作 |
| 集成學習 | ✅ | ⚠️ | Cisco 暫未實作 |
| 模型評估 | ✅ | ✅ | 準確率、混淆矩陣等 |
| 自動儲存 | ✅ | ✅ | 模型和報告 |
| UI 介面 | ✅ | ✅ | 完整的訓練介面 |
| GPU 加速 | ✅ | ⚠️ | 需額外實作 |

**圖例**：
- ✅ = 已實作
- ⚠️ = 部分實作或待實作
- ❌ = 未實作

## 📝 注意事項

### 限制與建議

1. **資料品質**
   - 確保資料清理完整
   - 特徵工程要充分
   - 處理異常值和缺失值

2. **運算資源**
   - 大型資料集需要較多記憶體
   - 訓練時間視資料量而定
   - 建議使用 GPU 加速（未來功能）

3. **模型選擇**
   - LightGBM：速度快，記憶體效率高
   - XGBoost：效能穩定，廣泛使用
   - CatBoost：處理類別特徵佳

4. **參數調整**
   - 預設參數適合大部分情況
   - 需要更好效能可手動調參
   - 或等待 Optuna 整合

### 已知問題

1. **Optuna 調參未整合**
   - 影響：無法自動尋找最佳參數
   - 解決：未來版本會加入

2. **GPU 加速未支援**
   - 影響：大型資料集訓練較慢
   - 解決：可參考 Fortinet 的 GPU 實作

3. **集成學習缺失**
   - 影響：無法組合多個模型
   - 解決：未來版本會加入

## 🔄 與 Fortinet 的差異

### 相同功能
- ✅ 基礎訓練流程
- ✅ 多演算法支援
- ✅ 模型評估與儲存
- ✅ UI 介面設計
- ✅ 主題樣式

### Cisco 獨特設計
- 簡化的訓練流程
- 更直覺的介面配置
- 針對 ASA 日誌優化

### 待補齊功能
- Optuna 超參數調整
- 集成學習模組
- GPU 加速支援
- 進階評估指標

## 🎯 後續發展規劃

### 短期目標（1-2 週）
1. ✅ 基礎訓練功能
2. ⏳ 加入 GPU ETL UI
3. ⏳ 整合 Optuna 調參
4. ⏳ 完善錯誤處理

### 中期目標（1 個月）
1. ⏳ 集成學習支援
2. ⏳ GPU 訓練加速
3. ⏳ 進階評估指標
4. ⏳ 模型版本管理

### 長期目標（3 個月）
1. ⏳ AutoML 整合
2. ⏳ 分散式訓練
3. ⏳ 模型監控面板
4. ⏳ A/B 測試支援

## 📚 相關文件

- [Cisco UI 使用手冊](./CISCO_UI_GUIDE.md)
- [訓練管線 API 文件](./TRAINING_API.md)
- [模型部署指南](./MODEL_DEPLOYMENT.md)
- [故障排除指南](./TROUBLESHOOTING.md)

## 🔗 相關檔案

- `Cisco_ui/training_pipeline/pipeline_main.py` - 訓練管線主程式
- `Cisco_ui/ui_pages/training_ui.py` - 訓練介面
- `Cisco_ui/ui_app.py` - 主應用程式（已更新）
- `Cisco_ui/training_pipeline/model_builder.py` - 模型建構器
- `Cisco_ui/training_pipeline/evaluator.py` - 評估器

## 📊 版本資訊

- **版本**：v1.0.0
- **建立日期**：2025-10-08
- **作者**：GitHub Copilot
- **狀態**：✅ 已完成基礎功能

---

**注意**：此為 Cisco ASA 模組的訓練工具首次發布，歡迎提供回饋和建議！
