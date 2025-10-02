# 🚀 D-Flare 簡潔使用指南

## 📂 清理後的目錄結構

```
D-Flare merge/
├── 🎯 主要檔案
│   ├── launch_unified_dashboard.py    ← 主要啟動器 (推薦使用)
│   ├── launch_dashboard.bat           ← 簡單啟動器 (備用)
│   └── requirements.txt               ← 依賴清單
│
├── 📁 重要目錄  
│   ├── unified_ui/                    ← 主應用程式
│   └── .streamlit/                    ← 配置檔案
│
├── 📚 文檔目錄
│   └── docs/                          ← 所有說明文件
│
└── 🛠️ 工具目錄
    └── tools/                         ← 回滾工具等
```

## 🎯 日常使用 - 只需記住這些！

### 🚀 啟動 D-Flare
```powershell
# 方法 1: Python 直接啟動 (推薦)
python launch_unified_dashboard.py

# 方法 2: 批次檔啟動 (備用)  
.\launch_dashboard.bat
```

### 🔄 如果出問題，緊急回滾
```powershell
# 執行智能回滾工具
.\tools\smart_rollback.bat
```

### 📚 需要幫助時
```powershell
# 查看文檔
Get-ChildItem docs\
```

## ✅ 清理成果

### 🗑️ 已刪除的冗余檔案
- ❌ `direct_launch*.py` (4個重複啟動器)
- ❌ `config_fixed.toml` (已應用的修復檔案)
- ❌ `app_fixed.py` (確認的副本檔案)
- ❌ `ui_fixes.py` (參考檔案)
- ❌ `launch_improved.bat` (重複功能)

### 📁 已整理的檔案
- 📚 9個說明文件 → `docs/` 目錄
- 🛠️ 3個工具檔案 → `tools/` 目錄

### 🔒 保留的重要檔案
- ✅ 主要功能檔案 (正常使用)
- ✅ 備份檔案 (緊急回滾)
- ✅ 配置檔案 (已修復)

## 💡 現在您只需要記住

**日常使用**：
```
python launch_unified_dashboard.py
```

**有問題時**：
```  
.\tools\smart_rollback.bat
```

**就這麼簡單！不會再搞混了！** 🎉

## 🧹 目錄現在乾淨多了

- 從 **30+個檔案** 減少到 **核心必要檔案**
- 所有雜亂檔案都已分類整理
- 清晰的目錄結構，一目了然

**現在可以專心使用 D-Flare，不用再為一堆檔案困惑！** ✨