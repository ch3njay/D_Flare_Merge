# 🎨 Cisco ASA Severity 視覺化配置說明

## ⚠️ 重要提醒：Cisco 與 Forti 的 Severity 相反！

### Cisco ASA Severity 規則
**數字越小 = 越嚴重**（與 Forti 相反）

| Severity | 名稱 | 英文 | 說明 | 顏色 | is_attack |
|----------|------|------|------|------|-----------|
| **0** | 緊急 | Emergencies | 系統不可用（硬體損壞） | 🔴 深紅 `#8B0000` | **過濾** |
| **1** | 警報 | Alert | 需要立即處理 | 🔴 猩紅 `#DC143C` | **1** (攻擊) |
| **2** | 嚴重 | Critical | 嚴重狀況 | 🟠 橙紅 `#FF4500` | **1** (攻擊) |
| **3** | 錯誤 | Error | 錯誤狀況 | 🟠 深橙 `#FF8C00` | **1** (攻擊) |
| **4** | 警告 | Warning | 警告狀況 | 🟡 金色 `#FFD700` | **1** (攻擊) |
| **5** | 通知 | Notification | 正常但重要的狀況 | 🟢 淺綠 `#90EE90` | **0** (正常) |
| **6** | 資訊 | Informational | 資訊性訊息 | 🔵 天藍 `#87CEEB` | **0** (正常) |
| **7** | 除錯 | Debugging | 除錯訊息 | ⚪ 淺灰 `#D3D3D3` | **0** (正常) |

---

## 🆚 與 Forti 的差異對比

| 項目 | Cisco ASA | Forti |
|------|-----------|-------|
| **方向** | 數字越小越嚴重 ⬇️ | 數字越大越嚴重 ⬆️ |
| **最嚴重** | 0 (緊急) | 4 (危險) |
| **最不嚴重** | 7 (除錯) | 1 (低) |
| **攻擊範圍** | 1-4 | 1-4 |
| **顏色趨勢** | 紅 → 橙 → 黃 → 綠 → 藍 → 灰 | 綠 → 藍 → 橙 → 紅 |

### Forti 舊配置（保留供參考）
```python
SEVERITY_COLORS_FORTI = {
    1: "#7bd684",  # 綠色 - 低風險
    2: "#29b6f6",  # 藍色 - 中風險
    3: "#ffb300",  # 橙色 - 高風險
    4: "#ea3b3b",  # 紅色 - 危險
}

SEVERITY_LABELS_FORTI = {
    1: "低",
    2: "中",
    3: "高",
    4: "危險",
}
```

---

## 📊 視覺化配置

### 1. 顏色配置（已更新）

**檔案**：`Cisco_ui/utils_labels.py`

```python
SEVERITY_COLORS = {
    0: "#8B0000",   # 深紅色 - Emergencies（緊急）
    1: "#DC143C",   # 猩紅色 - Alert（警報）
    2: "#FF4500",   # 橙紅色 - Critical（嚴重）
    3: "#FF8C00",   # 深橙色 - Error（錯誤）
    4: "#FFD700",   # 金色 - Warning（警告）
    5: "#90EE90",   # 淺綠色 - Notification（通知）
    6: "#87CEEB",   # 天藍色 - Informational（資訊）
    7: "#D3D3D3",   # 淺灰色 - Debugging（除錯）
}
```

### 2. 標籤配置（已更新）

**檔案**：`notification_models.py`

```python
SEVERITY_LABELS = {
    0: "緊急",      # Emergencies
    1: "警報",      # Alert
    2: "嚴重",      # Critical
    3: "錯誤",      # Error
    4: "警告",      # Warning
    5: "通知",      # Notification
    6: "資訊",      # Informational
    7: "除錯",      # Debugging
}
```

### 3. 輔助函式（新增）

**檔案**：`Cisco_ui/utils_labels.py`

```python
def get_severity_color(severity: int, default: str = "#808080") -> str:
    """取得 Severity 對應的顏色"""
    return SEVERITY_COLORS.get(severity, default)

def get_severity_label(severity: int, default: str = "未知") -> str:
    """取得 Severity 對應的中文標籤"""
    return SEVERITY_LABELS.get(severity, default)

def format_severity_display(severity: int) -> str:
    """格式化 Severity 顯示
    
    Returns:
        例如 "Level 1 (警報)"
    """
    label = get_severity_label(severity)
    return f"Level {severity} ({label})"
```

---

## 🔧 修改的檔案清單

### 1. ✅ `notification_models.py`
- **修改內容**：更新 `SEVERITY_LABELS` 為 0-7 級別
- **變更類型**：完全替換舊的 1-4 配置
- **影響範圍**：所有使用 SEVERITY_LABELS 的模組

### 2. ✅ `Cisco_ui/utils_labels.py`
- **修改內容**：
  - 更新 `SEVERITY_COLORS` 為 0-7 級別
  - 新增顏色梯度（紅→橙→黃→綠→藍→灰）
  - 新增輔助函式
- **變更類型**：完全替換 + 新增函式
- **影響範圍**：UI 視覺化、通知模組

### 3. ✅ `Cisco_ui/ui_pages/log_monitor.py`
- **修改內容**：更新高風險判斷條件
- **舊邏輯**：`Severity in [1, 2, 3]` 為高風險（Forti 風格）
- **新邏輯**：`Severity in [0, 1, 2, 3, 4]` 為高風險（Cisco ASA 風格）
- **影響範圍**：自動推播觸發條件

### 4. ⏳ 需檢查的其他檔案
- `Cisco_ui/ui_pages/etl_ui.py` - ETL 介面說明文字
- `Cisco_ui/ui_pages/visualization.py` - 圖表顯示
- `Cisco_ui/notifier.py` - 通知模組

---

## 💡 使用範例

### 在 Streamlit UI 中使用

```python
import streamlit as st
from Cisco_ui.utils_labels import (
    get_severity_color, 
    get_severity_label, 
    format_severity_display
)

# 顯示帶顏色的 Severity
severity = 2
color = get_severity_color(severity)
label = format_severity_display(severity)

st.markdown(
    f'<span style="color:{color}; font-weight:bold;">{label}</span>',
    unsafe_allow_html=True
)
# 輸出：Level 2 (嚴重) 【橙紅色】
```

### 在圖表中使用

```python
import plotly.graph_objects as go
from Cisco_ui.utils_labels import SEVERITY_COLORS, SEVERITY_LABELS

# 建立 Severity 分布長條圖
fig = go.Figure(data=[
    go.Bar(
        x=list(SEVERITY_LABELS.keys()),
        y=severity_counts,
        marker_color=[SEVERITY_COLORS[i] for i in range(8)],
        text=[SEVERITY_LABELS[i] for i in range(8)],
        textposition='auto',
    )
])

fig.update_layout(
    title="Cisco ASA Severity 分布（數字越小越嚴重）",
    xaxis_title="Severity Level",
    yaxis_title="事件數量",
)
```

---

## 🎨 視覺化設計原則

### 1. 顏色梯度設計
```
嚴重 ──────────────────────────────────────> 正常
🔴 深紅 → 🔴 猩紅 → 🟠 橙紅 → 🟠 深橙 → 🟡 金色 → 🟢 淺綠 → 🔵 天藍 → ⚪ 淺灰
Level 0    Level 1    Level 2    Level 3    Level 4    Level 5    Level 6    Level 7
```

### 2. 顏色選擇理由

| Severity | 顏色 | 選擇理由 |
|----------|------|---------|
| 0-1 | 紅色系 | 最嚴重，需立即處理 |
| 2-3 | 橙色系 | 嚴重，需要關注 |
| 4 | 黃色 | 警告，可能需要處理 |
| 5 | 綠色 | 正常但重要 |
| 6 | 藍色 | 資訊性，不需處理 |
| 7 | 灰色 | 除錯，可忽略 |

### 3. UI 顯示建議

#### 表格顯示
```python
# 在表格中顯示帶顏色的 Severity
df_styled = df.style.apply(
    lambda x: [
        f'background-color: {get_severity_color(val)}' 
        if col == 'Severity' else '' 
        for val, col in zip(x, x.index)
    ],
    axis=1
)
```

#### 儀表板顯示
```python
# 顯示最嚴重的事件
critical_events = df[df['Severity'] <= 2]  # 0, 1, 2 級
st.error(f"🚨 偵測到 {len(critical_events)} 個嚴重事件！")

# 顯示警告事件
warning_events = df[df['Severity'].isin([3, 4])]  # 3, 4 級
st.warning(f"⚠️ 偵測到 {len(warning_events)} 個警告事件")

# 資訊事件
info_events = df[df['Severity'] >= 5]  # 5, 6, 7 級
st.info(f"ℹ️ {len(info_events)} 個資訊事件")
```

---

## ✅ 驗證清單

### 已完成項目
- [x] 更新 `SEVERITY_LABELS` (0-7)
- [x] 更新 `SEVERITY_COLORS` (0-7)
- [x] 新增輔助函式
- [x] 修正 `log_monitor.py` 高風險判斷
- [x] 建立完整文件

### 待確認項目
- [ ] 檢查所有 UI 頁面中的 Severity 顯示
- [ ] 確認圖表生成邏輯
- [ ] 測試通知模組的 Severity 處理
- [ ] 驗證推播觸發條件

---

## 📞 注意事項

### 1. ⚠️ 與使用者溝通
在 UI 中加入明確的提示，說明 Cisco ASA 的 Severity 規則：
```python
st.info("""
📌 **Cisco ASA Severity 說明**
- Cisco ASA 的 Severity 與 Forti 相反
- **數字越小越嚴重**（0=最嚴重，7=最不嚴重）
- Level 0-4：需要關注的安全事件
- Level 5-7：正常運作訊息
""")
```

### 2. ⚠️ 後向相容性
如果系統中仍有 Forti 資料，建議：
- 保留舊的 `SEVERITY_COLORS_FORTI` 供參考
- 在資料處理時自動識別格式
- 提供格式轉換工具

### 3. ⚠️ 測試建議
```python
# 測試所有 Severity 級別的顯示
for severity in range(8):
    color = get_severity_color(severity)
    label = format_severity_display(severity)
    print(f"Severity {severity}: {label} - {color}")
```

---

**文件建立時間**：2025-10-09  
**版本**：1.0  
**狀態**：✅ 已更新  
**下次檢查**：視覺化頁面測試後
