# 🧹 D-Flare 工作目錄清理計畫

## 🚨 問題分析
您的工作目錄確實太亂了！有：
- **5個不同的啟動器**
- **16個修復/指南/報告檔案**  
- **多個備份和臨時檔案**

## 🎯 清理目標
**保留必要檔案，刪除雜亂檔案，讓目錄乾淨易懂**

## 📋 檔案分類與處理決策

### ✅ 必須保留（核心系統檔案）
```
launch_unified_dashboard.py     ← 主要啟動器（唯一需要的）
launch_dashboard.bat           ← 簡單啟動器（二選一保留）
unified_ui/                    ← 主要應用目錄
.streamlit/                    ← 配置目錄
requirements.txt               ← 依賴清單
```

### 🔒 必須保留（安全備份）
```
.streamlit/config.toml.backup          ← 配置備份
unified_ui/app.py.backup              ← UI備份  
launch_dashboard.bat.backup           ← 啟動器備份
```

### 🗑️ 可以刪除（重複的啟動器）
```
direct_launch.py               ← 重複功能
direct_launcher.py             ← 重複功能
emergency_launcher.py          ← 重複功能
simple_launcher.py             ← 重複功能
launch_improved.bat            ← 已測試，可用 launch_dashboard.bat 替代
```

### 🗑️ 可以刪除（修復檔案 - 任務完成）
```
config_fixed.toml              ← 已應用
app_fixed.py                   ← 已確認為副本
ui_fixes.py                    ← 僅供參考
tempCodeRunnerFile.py          ← 臨時檔案
```

### 📚 整理到文檔目錄（可選保留）
```
所有 .md 檔案 → 移到 docs/ 目錄
所有 .bat 回滾工具 → 移到 tools/ 目錄
```

## 🚀 立即執行清理

### 步驟 1: 創建整理目錄
```powershell
New-Item -ItemType Directory -Path "docs" -Force
New-Item -ItemType Directory -Path "tools" -Force  
New-Item -ItemType Directory -Path "temp_cleanup" -Force
```

### 步驟 2: 移動文檔檔案
```powershell
Move-Item "*_GUIDE.md" "docs/" -Force -ErrorAction SilentlyContinue
Move-Item "*_REPORT.md" "docs/" -Force -ErrorAction SilentlyContinue
Move-Item "ROLLBACK_EXPLANATION.md" "docs/" -Force -ErrorAction SilentlyContinue
```

### 步驟 3: 移動工具檔案
```powershell
Move-Item "*rollback.bat" "tools/" -Force -ErrorAction SilentlyContinue
Move-Item "streamlit_config_guide.toml" "tools/" -Force -ErrorAction SilentlyContinue
```

### 步驟 4: 刪除重複啟動器
```powershell
Remove-Item "direct_launch*.py" -Force -ErrorAction SilentlyContinue
Remove-Item "emergency_launcher.py" -Force -ErrorAction SilentlyContinue  
Remove-Item "simple_launcher.py" -Force -ErrorAction SilentlyContinue
Remove-Item "launch_improved.bat" -Force -ErrorAction SilentlyContinue
```

### 步驟 5: 刪除已用完的修復檔案
```powershell
Remove-Item "config_fixed.toml" -Force -ErrorAction SilentlyContinue
Remove-Item "app_fixed.py" -Force -ErrorAction SilentlyContinue
Remove-Item "ui_fixes.py" -Force -ErrorAction SilentlyContinue
Remove-Item "tempCodeRunnerFile.py" -Force -ErrorAction SilentlyContinue
```

## 🎯 清理後的乾淨目錄結構

```
D-Flare merge/
├── launch_unified_dashboard.py    ← 主啟動器
├── launch_dashboard.bat           ← 備用啟動器
├── requirements.txt
├── unified_ui/
│   ├── app.py                     ← 主應用
│   └── app.py.backup             ← 備份
├── .streamlit/
│   ├── config.toml               ← 已修復的配置
│   └── config.toml.backup        ← 備份
├── docs/                         ← 所有文檔
└── tools/                        ← 工具檔案
```

## 💡 使用建議

清理後，您只需要記住：
- **主要啟動**：`python launch_unified_dashboard.py`
- **備用啟動**：`launch_dashboard.bat`
- **緊急回滾**：`tools/smart_rollback.bat`
- **查看文檔**：`docs/` 目錄

**簡單、乾淨、不會搞混！**