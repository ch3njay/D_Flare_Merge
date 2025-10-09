# 🎯 Cisco ASA Severity 快速參考卡

## 📊 Severity 對照表

```
Severity | 標籤 | 顏色    | is_attack | 推播 | 說明
---------|------|---------|-----------|------|----------------
   0     | 緊急 | 🔴 深紅 |    N/A    | 過濾 | 硬體問題，應過濾
   1     | 警報 | 🔴 猩紅 |     1     |  ✅  | 需立即處理
   2     | 嚴重 | 🟠 橙紅 |     1     |  ✅  | 嚴重狀況
   3     | 錯誤 | 🟠 深橙 |     1     |  ✅  | 錯誤狀況
   4     | 警告 | 🟡 金色 |     1     |  ✅  | 警告狀況
   5     | 通知 | 🟢 淺綠 |     0     |  ❌  | 正常但重要
   6     | 資訊 | 🔵 天藍 |     0     |  ❌  | 資訊性訊息
   7     | 除錯 | ⚪ 淺灰 |     0     |  ❌  | 除錯訊息
```

## 🔑 關鍵規則

- **方向**: 數字越小越嚴重（0=最嚴重，7=最不嚴重）
- **過濾**: Severity 0 在 parser 階段返回 None
- **推播**: Severity 0-4 觸發推播
- **標記**: Severity 1-4 標記為 is_attack=1

## ⚠️ 與 Forti 的差異

| 項目 | Cisco ASA | Forti |
|------|-----------|-------|
| 範圍 | 0-7 | 1-4 |
| 方向 | 越小越嚴重 | 越大越嚴重 |
| 推播 | 0-4 | 1-3 |

**注意**: 方向完全相反！

## 🛠️ 使用範例

### Python 程式碼
```python
from Cisco_ui.utils_labels import (
    get_severity_color,
    get_severity_label,
    format_severity_display
)

# 取得顏色
color = get_severity_color(2)  # "#FF4500" (橙紅)

# 取得標籤
label = get_severity_label(2)  # "嚴重"

# 格式化顯示
display = format_severity_display(2)  # "Level 2 (嚴重)"
```

### Streamlit UI
```python
import streamlit as st
severity = 2
st.markdown(
    f"<span style='background-color: {get_severity_color(severity)}; "
    f"padding: 4px 8px; color: white;'>"
    f"{get_severity_label(severity)}</span>",
    unsafe_allow_html=True
)
```

### Plotly 圖表
```python
import plotly.express as px
from Cisco_ui.utils_labels import SEVERITY_COLORS

fig = px.bar(df, x="Datetime", y="Count", color="Severity",
             color_discrete_map=SEVERITY_COLORS)
```

## ✅ 測試指令

```bash
# 快速測試（5 個測試）
python test_severity_colors.py

# 完整測試（12 個測試）
python test_cisco_severity_strict.py

# 視覺化展示
python demo_severity_colors.py
```

## 📚 相關文件

- `docs/CISCO_SEVERITY_VISUALIZATION_GUIDE.md` - 完整指南
- `CISCO_SEVERITY_FIX_REPORT.md` - 修正報告
- `CISCO_SEVERITY_CHECKLIST.md` - 檢查清單
- `CISCO_SEVERITY_STRICT_VALIDATION_REPORT.md` - 檢測報告

## 🎯 快速檢查清單

- [ ] SEVERITY_LABELS 包含 0-7
- [ ] SEVERITY_COLORS 包含 8 種顏色
- [ ] cisco_log_parser.py 過濾 Severity 0
- [ ] log_mapping.py 標記 1-4 為攻擊
- [ ] notifier.py 推播 0-4
- [ ] log_monitor.py 判斷 0-4 為高風險

---

**版本**: 1.0 | **更新**: 2025年10月9日 | **狀態**: ✅ 驗證通過
