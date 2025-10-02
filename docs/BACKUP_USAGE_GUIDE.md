# 🔄 D-Flare 備份檔案使用指南

## 🚨 什麼時候需要使用備份？

### 1. **系統無法啟動**
```
症狀：python launch_unified_dashboard.py 執行失敗
原因：config.toml 修復後出現新問題
```

### 2. **頁面載入錯誤**  
```
症狀：瀏覽器顯示錯誤訊息，頁面無法正常顯示
原因：UI 修復後程式碼有問題
```

### 3. **啟動器失效**
```
症狀：.bat 檔案執行時報錯或卡住
原因：啟動器改進後不相容
```

## 📋 如何使用備份檔案

### 方案 A: 個別回滾（推薦）

#### 🔧 回滾 config.toml（解決啟動問題）
```powershell
# 1. 進入專案目錄
cd "C:\Users\U02020\Desktop\D-Flare merge"

# 2. 檢查備份是否存在
if (Test-Path ".streamlit\config.toml.backup") {
    Write-Host "✅ 找到 config.toml 備份" -ForegroundColor Green
} else {
    Write-Host "❌ 備份檔案不存在" -ForegroundColor Red
}

# 3. 執行回滾
Copy-Item ".streamlit\config.toml.backup" ".streamlit\config.toml" -Force
Write-Host "🔄 已回滾 config.toml 到修復前狀態" -ForegroundColor Yellow

# 4. 測試是否恢復正常
python launch_unified_dashboard.py
```

#### 🎨 回滾 UI 檔案（解決頁面問題）
```powershell
# 1. 進入專案目錄
cd "C:\Users\U02020\Desktop\D-Flare merge"

# 2. 檢查備份
if (Test-Path "unified_ui\app.py.backup") {
    Write-Host "✅ 找到 app.py 備份" -ForegroundColor Green
} else {
    Write-Host "❌ 備份檔案不存在" -ForegroundColor Red
}

# 3. 執行回滾
Copy-Item "unified_ui\app.py.backup" "unified_ui\app.py" -Force
Write-Host "🔄 已回滾 UI 到修復前狀態" -ForegroundColor Yellow

# 4. 重新啟動測試
python launch_unified_dashboard.py
```

#### 🚀 回滾啟動器（解決啟動器問題）
```powershell
# 1. 進入專案目錄  
cd "C:\Users\U02020\Desktop\D-Flare merge"

# 2. 檢查備份
if (Test-Path "launch_dashboard.bat.backup") {
    Write-Host "✅ 找到啟動器備份" -ForegroundColor Green
} else {
    Write-Host "❌ 備份檔案不存在" -ForegroundColor Red
}

# 3. 執行回滾
Copy-Item "launch_dashboard.bat.backup" "launch_dashboard.bat" -Force
Write-Host "🔄 已回滾啟動器到修復前狀態" -ForegroundColor Yellow

# 4. 測試啟動器
.\launch_dashboard.bat
```

### 方案 B: 一鍵完整回滾（緊急情況）

#### 💊 緊急完全回滾腳本
```powershell
# 創建緊急回滾腳本
@"
@echo off
chcp 65001
echo ========================================
echo 🚨 D-Flare 緊急回滾程序
echo ========================================
echo.

echo 🔍 檢查備份檔案...
if not exist ".streamlit\config.toml.backup" (
    echo ❌ config.toml 備份不存在
    goto :error
)
if not exist "unified_ui\app.py.backup" (
    echo ❌ app.py 備份不存在
    goto :error
)
if not exist "launch_dashboard.bat.backup" (
    echo ❌ 啟動器備份不存在
    goto :error
)

echo ✅ 所有備份檔案存在
echo.

echo 🔄 執行回滾...
copy ".streamlit\config.toml.backup" ".streamlit\config.toml" >nul 2>&1
echo ✅ config.toml 已回滾

copy "unified_ui\app.py.backup" "unified_ui\app.py" >nul 2>&1  
echo ✅ app.py 已回滾

copy "launch_dashboard.bat.backup" "launch_dashboard.bat" >nul 2>&1
echo ✅ 啟動器已回滾

echo.
echo 🎉 回滾完成！系統已恢復到修復前狀態
echo 💡 現在可以正常使用 D-Flare 了
echo.

echo 🚀 自動啟動 D-Flare...
python launch_unified_dashboard.py

goto :end

:error
echo ❌ 回滾失敗：找不到必要的備份檔案
echo 💡 請檢查備份檔案是否存在
pause
exit /b 1

:end
echo.
echo 按任意鍵退出...
pause >nul
"@ | Out-File -FilePath "emergency_rollback.bat" -Encoding UTF8
```

## 🎯 實際使用場景與步驟

### 場景 1: 修復後無法啟動
```powershell
# 問題：執行 python launch_unified_dashboard.py 報錯
# 解決：回滾 config.toml

cd "C:\Users\U02020\Desktop\D-Flare merge"
Copy-Item ".streamlit\config.toml.backup" ".streamlit\config.toml" -Force
python launch_unified_dashboard.py
# 結果：恢復到修復前的可用狀態
```

### 場景 2: 網頁顯示錯誤
```powershell
# 問題：瀏覽器顯示 AttributeError 或其他 Python 錯誤
# 解決：回滾 UI 檔案

cd "C:\Users\U02020\Desktop\D-Flare merge"
Copy-Item "unified_ui\app.py.backup" "unified_ui\app.py" -Force
# 重新整理瀏覽器或重啟服務
# 結果：頁面恢復正常顯示
```

### 場景 3: 啟動器異常
```powershell
# 問題：launch_dashboard.bat 執行時報錯
# 解決：回滾啟動器

cd "C:\Users\U02020\Desktop\D-Flare merge"
Copy-Item "launch_dashboard.bat.backup" "launch_dashboard.bat" -Force
.\launch_dashboard.bat
# 結果：啟動器恢復正常功能
```

## ⚠️ 重要注意事項

### 1. **回滾前先停止服務**
```powershell
# 如果 D-Flare 正在運行，先按 Ctrl+C 停止
# 或關閉瀏覽器標籤頁
```

### 2. **確認備份檔案存在**
```powershell
# 使用前先檢查
Test-Path ".streamlit\config.toml.backup"
Test-Path "unified_ui\app.py.backup" 
Test-Path "launch_dashboard.bat.backup"
```

### 3. **回滾後的狀態**
- ✅ 系統可以正常運行
- ⚠️ 但原始的小問題會回來（比如 config.toml 語法錯誤）
- 💡 可以重新嘗試修復，或尋求其他解決方案

## 🛠️ 快速回滾命令總表

| 問題類型 | 快速命令 |
|---------|---------|
| 啟動失敗 | `Copy-Item ".streamlit\config.toml.backup" ".streamlit\config.toml" -Force` |
| 頁面錯誤 | `Copy-Item "unified_ui\app.py.backup" "unified_ui\app.py" -Force` |
| 啟動器問題 | `Copy-Item "launch_dashboard.bat.backup" "launch_dashboard.bat" -Force` |
| 全部回滾 | 執行 `emergency_rollback.bat` |

## 💡 使用備份的最佳實踐

1. **先嘗試單一回滾**：不要一次回滾所有檔案
2. **測試後再繼續**：每次回滾後測試是否解決問題
3. **保留回滾記錄**：記住回滾了什麼，避免重複問題
4. **重新備份**：如果要再次嘗試修復，先做新的備份

這樣您就有了完整的「後悔藥」使用說明書！🎯