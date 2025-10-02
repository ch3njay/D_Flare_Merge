# D-Flare 專案依賴安裝指南

## 📋 概述

本指南提供多種方式來安裝 D-Flare 專案所需的所有外部依賴項目。

## 🔧 依賴項目清單

### 核心依賴項目

| 類別 | 套件名稱 | 版本要求 | 用途 |
|------|----------|----------|------|
| **Web UI** | streamlit | >=1.28.0 | 網頁應用框架 |
| | streamlit-autorefresh | latest | 自動重新整理元件 |
| **資料處理** | pandas | >=1.5.0 | 資料處理與分析 |
| | numpy | >=1.21.0 | 數值計算 |
| | scipy | >=1.9.0 | 科學計算 |
| **機器學習** | scikit-learn | >=1.2.0 | 機器學習核心庫 |
| | joblib | >=1.2.0 | 並行處理與序列化 |
| | xgboost | >=1.6.0 | XGBoost 梯度提升 |
| | lightgbm | >=3.3.0 | LightGBM 梯度提升 |
| | catboost | >=1.1.0 | CatBoost 梯度提升 |
| | optuna | >=3.0.0 | 超參數最佳化 |
| **視覺化** | matplotlib | >=3.6.0 | 基礎繪圖 |
| | seaborn | >=0.11.0 | 統計視覺化 |
| | plotly | >=5.11.0 | 互動式視覺化 |
| **系統工具** | tqdm | >=4.64.0 | 進度條顯示 |
| | colorama | >=0.4.5 | 終端機色彩輸出 |
| | psutil | >=5.9.0 | 系統資源監控 |
| | watchdog | >=2.1.0 | 檔案系統監控 |
| **網路通訊** | requests | >=2.28.0 | HTTP 請求 |
| | chardet | >=4.0.0 | 字元編碼檢測 |

### 可選依賴項目

| 類別 | 套件名稱 | 用途 |
|------|----------|------|
| **AI 服務** | google-generativeai | Google Gemini API |
| **GPU 加速** | cupy-cuda11x | CUDA 11.x GPU 加速 |
| | cupy-cuda12x | CUDA 12.x GPU 加速 |
| **開發工具** | pytest | 測試框架 |
| | black | 程式碼格式化 |

## 🚀 安裝方式

### 方式 1: 使用 Windows 批次檔 (推薦)

**最簡單的方式**，適合 Windows 用戶：

```batch
# 雙擊執行或在命令提示字元中執行
install_dependencies.bat
```

此批次檔會提供三種安裝選項：
1. 使用 requirements.txt 安裝 (推薦)
2. 使用自動安裝腳本  
3. 僅安裝核心依賴項目

### 方式 2: 使用 requirements.txt

```bash
# 升級 pip
python -m pip install --upgrade pip

# 安裝所有依賴項目
python -m pip install -r requirements.txt
```

### 方式 3: 使用自動安裝腳本

```bash
# 執行自動安裝腳本
python install_simple.py
```

這個腳本會：
- 自動檢查已安裝的套件
- 安裝缺少的依賴項目
- 檢查 GPU 支援並安裝相應套件
- 驗證核心套件安裝狀況

### 方式 4: 手動安裝

如果自動安裝失敗，可以手動安裝核心套件：

```bash
# 升級 pip
python -m pip install --upgrade pip

# 安裝核心套件
python -m pip install streamlit pandas numpy scikit-learn matplotlib requests tqdm colorama

# 安裝機器學習套件
python -m pip install xgboost lightgbm catboost optuna

# 安裝視覺化套件  
python -m pip install seaborn plotly

# 安裝系統工具
python -m pip install psutil watchdog chardet
```

## 🏃‍♂️ 啟動專案

安裝依賴項目後，有多種方式啟動專案：

### 使用批次檔啟動 (Windows)

```batch
# 雙擊執行或在命令提示字元中執行
launch_dashboard.bat
```

### 使用 Python 命令

```bash
python launch_unified_dashboard.py
```

### 使用 Streamlit 命令

```bash
streamlit run unified_ui/app.py
```

## 🔍 故障排除

### 常見問題

1. **Python 未安裝**
   - 下載並安裝 Python 3.8+ : https://www.python.org/downloads/
   - 安裝時記得勾選 "Add Python to PATH"

2. **pip 版本過舊**
   ```bash
   python -m pip install --upgrade pip
   ```

3. **套件安裝失敗**
   - 檢查網路連線
   - 嘗試使用國內鏡像：
     ```bash
     pip install -i https://pypi.tuna.tsinghua.edu.cn/simple/ <package_name>
     ```

4. **權限問題 (Linux/Mac)**
   ```bash
   # 使用 --user 標誌
   pip install --user -r requirements.txt
   ```

5. **GPU 加速套件安裝問題**
   - 確認 NVIDIA 驅動已安裝
   - 確認 CUDA 版本並選擇對應的 cupy 版本：
     - CUDA 11.x: `cupy-cuda11x`
     - CUDA 12.x: `cupy-cuda12x`

### 驗證安裝

執行以下命令驗證核心套件：

```python
python -c "
import streamlit as st
import pandas as pd
import numpy as np
import sklearn
print('✅ 所有核心套件安裝成功！')
"
```

## 📁 檔案說明

- `requirements.txt` - 標準 Python 依賴項目清單
- `install_simple.py` - 簡化版自動安裝腳本  
- `install_dependencies.py` - 完整版自動安裝腳本
- `install_dependencies.bat` - Windows 批次安裝檔
- `launch_dashboard.bat` - Windows 專案啟動檔
- `launch_unified_dashboard.py` - 專案主啟動檔

## 💡 建議

1. **首次安裝**：建議使用 `install_dependencies.bat` (Windows) 或 `requirements.txt` 方式
2. **開發環境**：建議使用虛擬環境隔離依賴項目
3. **生產環境**：固定套件版本避免相容性問題
4. **GPU 環境**：確認 CUDA 版本後安裝對應的 CuPy

## 🔗 相關連結

- [Python 官方網站](https://www.python.org/)
- [Streamlit 文件](https://docs.streamlit.io/)
- [scikit-learn 文件](https://scikit-learn.org/)
- [XGBoost 文件](https://xgboost.readthedocs.io/)

---

如有安裝問題，請檢查錯誤訊息並參考上述故障排除指南。