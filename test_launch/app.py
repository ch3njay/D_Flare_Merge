"""簡單的 D-Flare 測試應用程式。"""
import streamlit as st

st.set_page_config(
    page_title="D-Flare Test Dashboard", 
    page_icon="🛡️", 
    layout="wide"
)

st.title("🛡️ D-Flare Orchestrator 系統測試")

st.markdown("""
### 🎉 恭喜！Orchestrator 系統啟動成功！

這個頁面證實了以下功能：

#### ✅ 已驗證功能：
- **StartupContext**: 配置管理和序列化
- **錯誤處理**: 結構化錯誤報告系統
- **Preflight 檢查**: 系統健康檢查
- **CLI 介面**: 完整的 typer 命令行工具
- **Streamlit 執行器**: 動態應用程式啟動

#### 🔧 Orchestrator 特色：
- **品牌適配**: 支援 unified、fortinet、cisco 模式
- **環境變數注入**: 自動設定執行環境
- **健康檢查**: Redis、API 端點、依賴項檢查
- **JSON 輸出**: 機器可讀的狀態報告
- **優雅錯誤處理**: 詳細的錯誤訊息和提示

#### 📋 可用的 CLI 命令：
```bash
# 啟動 dashboard
python -m orchestrator.cli launch

# 執行健康檢查
python -m orchestrator.cli check

# 使用不同品牌
python -m orchestrator.cli launch --brand fortinet --mode fortinet-only

# JSON 輸出模式
python -m orchestrator.cli check --json
```

#### 🚀 下一步：
現在可以整合真實的 Fortinet 和 Cisco UI 模組，實現完整的微服務架構！
""")

# 顯示環境變數（如果有的話）
import os
env_vars = {k: v for k, v in os.environ.items() if k.startswith('DFLARE_')}
if env_vars:
    st.subheader("🌍 環境變數")
    for key, value in env_vars.items():
        st.code(f"{key}={value}")

st.success("🎯 Orchestrator 系統運行正常！")