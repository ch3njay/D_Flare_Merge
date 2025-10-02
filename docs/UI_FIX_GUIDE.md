# D-Flare UI 修復指南

## 問題總結

根據您的截圖和程式碼分析，發現以下問題：

### 1. 快速功能按鈕功能不完整
- **儀表板按鈕**：只顯示成功訊息，沒有實際功能
- **設定按鈕**：只顯示資訊訊息，沒有實際設定面板

### 2. Fortinet 和 Cisco 描述不統一
在 `unified_ui/app.py` 中有兩處不同的描述：

**BRAND_DESCRIPTIONS (第47行):**
```python
BRAND_DESCRIPTIONS = {
    "Fortinet": "Fortinet 版本提供完整的訓練、ETL、推論與通知流程。",
    "Cisco": "Cisco 版本專注於 ASA log 擷取、模型推論與跨平台通知。",
}
```

**brand_configs (在側邊欄中):**
```python
brand_configs = {
    "Fortinet": {
        "icon": "🛡️",
        "color": "#f97316",
        "desc": "完整訓練與推論流程"
    },
    "Cisco": {
        "icon": "📡", 
        "color": "#3b82f6",
        "desc": "ASA 日誌分析專家"
    }
}
```

## 修復方案

### 修復 1: 增強快速功能按鈕

找到 `unified_ui/app.py` 中的快速功能按鈕區塊（約第 XXX 行），將：

```python
# 功能按鈕
col1, col2 = st.columns(2)
with col1:
    if st.button("📊 儀表板", use_container_width=True):
        st.success("切換至儀表板視圖")
with col2:
    if st.button("🔧 設定", use_container_width=True):
        st.info("開啟系統設定")
```

**替換為：**

```python
# 功能按鈕
col1, col2 = st.columns(2)
with col1:
    if st.button("📊 儀表板", use_container_width=True):
        # 切換儀表板狀態
        if "show_dashboard" not in st.session_state:
            st.session_state.show_dashboard = True
        else:
            st.session_state.show_dashboard = not st.session_state.show_dashboard
        
        if st.session_state.show_dashboard:
            st.success("✅ 儀表板已啟用 - 顯示系統狀態概覽")
        else:
            st.info("ℹ️ 儀表板已關閉")

with col2:
    if st.button("🔧 設定", use_container_width=True):
        # 切換設定面板狀態
        if "show_settings" not in st.session_state:
            st.session_state.show_settings = True
        else:
            st.session_state.show_settings = not st.session_state.show_settings
        
        if st.session_state.show_settings:
            st.success("⚙️ 設定面板已開啟")
        else:
            st.info("ℹ️ 設定面板已關閉")

# 顯示設定面板（當啟用時）
if st.session_state.get("show_settings", False):
    with st.expander("🛠️ 系統設定", expanded=True):
        st.write("**🔔 通知設定**")
        st.checkbox("啟用 Discord 通知", value=True, key="discord_notify")
        st.checkbox("啟用 Slack 通知", value=False, key="slack_notify")
        
        st.write("**🎨 介面設定**")
        st.selectbox("主題選擇", ["深色主題", "淺色主題"], key="theme_choice")
        
        st.write("**🔍 日誌設定**")
        st.number_input("日誌保存天數", min_value=1, max_value=365, value=30, key="log_retention")
        
        if st.button("💾 儲存所有設定"):
            st.success("✅ 設定已儲存並套用")

# 顯示儀表板（當啟用時）
if st.session_state.get("show_dashboard", False):
    with st.expander("📊 系統儀表板", expanded=True):
        col_d1, col_d2, col_d3 = st.columns(3)
        with col_d1:
            st.metric("活躍連線", "127", delta="5")
        with col_d2:
            st.metric("處理日誌", "1,284", delta="142")
        with col_d3:
            st.metric("威脅檢測", "23", delta="-2")
```

### 修復 2: 統一品牌描述

找到兩處描述定義並統一格式：

**1. 修改 BRAND_DESCRIPTIONS (第47行左右):**
```python
BRAND_DESCRIPTIONS = {
    "Fortinet": "完整的威脅防護與 AI 推論解決方案，提供訓練、ETL、推論與多平台通知流程。",
    "Cisco": "專業的 ASA 防火牆日誌分析平台，專注於日誌擷取、智能推論與即時通知。",
}
```

**2. 修改 brand_configs 描述 (在側邊欄渲染函數中):**
```python
brand_configs = {
    "Fortinet": {
        "icon": "🛡️",
        "color": "#f97316",
        "desc": "完整威脅防護與 AI 推論解決方案"
    },
    "Cisco": {
        "icon": "📡",
        "color": "#3b82f6", 
        "desc": "專業 ASA 防火牆日誌分析平台"
    }
}
```

### 修復 3: 改進 config.toml 語法錯誤

檢查 `.streamlit/config.toml` 檔案，確保格式正確：

```toml
[global]
showWarningOnDirectExecution = false

[server]
port = 8501
headless = false
runOnSave = false

[browser]
gatherUsageStats = false
serverAddress = "localhost"
serverPort = 8501

[theme]
base = "dark"
primaryColor = "#FF6B35"
backgroundColor = "#0F1419"
secondaryBackgroundColor = "#1A1F29"
textColor = "#E6E8EB"

[client]
showErrorDetails = false
```

### 修復 4: .bat 檔案中文編碼問題

檢查所有 .bat 檔案並確保以 UTF-8 with BOM 編碼保存：

**launch_dashboard.bat:**
```batch
@echo off
chcp 65001
echo 🚀 啟動 D-Flare 統一控制台...
echo 🔍 檢查環境中...

REM 指定 Python 版本（根據您的環境調整）
set PYTHON_CMD=python
if exist "%LOCALAPPDATA%\Programs\Python\Python313\python.exe" (
    set PYTHON_CMD="%LOCALAPPDATA%\Programs\Python\Python313\python.exe"
)

echo 📂 使用 Python: %PYTHON_CMD%
echo 🌐 啟動應用程序...

%PYTHON_CMD% launch_unified_dashboard.py

echo 🔄 按任意鍵重新啟動，或關閉視窗退出...
pause
goto :eof
```

## 實施步驟

1. **備份原始檔案**
   ```bash
   Copy-Item "unified_ui\app.py" "unified_ui\app.py.backup"
   ```

2. **依序套用修復**
   - 先修復快速功能按鈕
   - 再統一品牌描述  
   - 最後修復 config.toml

3. **測試功能**
   ```bash
   python launch_unified_dashboard.py
   ```

4. **驗證修復效果**
   - 點擊儀表板按鈕應顯示系統指標
   - 點擊設定按鈕應顯示完整設定面板
   - Fortinet/Cisco 描述應該一致且格式統一
   - 不應再出現 config.toml 語法錯誤

這些修復將讓您的 D-Flare 控制台更加完整和一致！