"""
🎨 Cisco ASA Severity 視覺化顏色展示
展示新的 Severity 顏色配置和輔助函式使用方式
"""

import sys
from pathlib import Path

# 加入模組路徑
sys.path.insert(0, str(Path(__file__).parent / "Cisco_ui"))

from Cisco_ui.utils_labels import (
    SEVERITY_COLORS,
    SEVERITY_LABELS,
    get_severity_color,
    get_severity_label,
    format_severity_display
)

def print_color_block(color: str, label: str, severity: int) -> None:
    """在終端顯示顏色區塊（使用 ANSI 逃脫序列）"""
    # 將 Hex 顏色轉換為 RGB
    r = int(color[1:3], 16)
    g = int(color[3:5], 16)
    b = int(color[5:7], 16)
    
    # ANSI 24-bit 真彩色
    bg = f"\033[48;2;{r};{g};{b}m"
    reset = "\033[0m"
    
    # 判斷使用黑色或白色文字（根據亮度）
    brightness = (r * 299 + g * 587 + b * 114) / 1000
    fg = "\033[30m" if brightness > 128 else "\033[97m"
    
    print(f"{bg}{fg}  Severity {severity} - {label}  {reset} {color}")

print("=" * 70)
print("🎨 Cisco ASA Severity 顏色配置展示")
print("=" * 70)
print()

# 顯示顏色梯度
print("【顏色梯度】從嚴重到正常")
print("-" * 70)

for severity in range(8):
    color = get_severity_color(severity)
    label = get_severity_label(severity)
    print_color_block(color, label, severity)

print()
print("-" * 70)
print()

# 顯示使用範例
print("【使用範例】")
print("-" * 70)
print()

# 範例 1：在 Streamlit 中使用
print("1️⃣ Streamlit UI 顯示")
print()
print("```python")
print("import streamlit as st")
print("from Cisco_ui.utils_labels import get_severity_color, get_severity_label")
print()
print("severity = 2  # 嚴重")
print('st.markdown(')
print('    f"<span style=\\"background-color: {get_severity_color(severity)}; "')
print('    f"padding: 4px 8px; border-radius: 4px; color: white;\\">"')
print('    f"{get_severity_label(severity)}</span>",')
print('    unsafe_allow_html=True')
print(')')
print("```")
print()

# 範例 2：在 Plotly 圖表中使用
print("2️⃣ Plotly 圖表配色")
print()
print("```python")
print("import plotly.express as px")
print("from Cisco_ui.utils_labels import SEVERITY_COLORS")
print()
print("fig = px.bar(")
print("    df,")
print('    x="Datetime",')
print('    y="Count",')
print('    color="Severity",')
print("    color_discrete_map=SEVERITY_COLORS")
print(")")
print("```")
print()

# 範例 3：在通知訊息中使用
print("3️⃣ 通知訊息格式化")
print()
print("```python")
print("from Cisco_ui.utils_labels import format_severity_display")
print()
print("severity = 1  # 警報")
print('message = f"檢測到高風險事件：{format_severity_display(severity)}"')
print('# 輸出: 檢測到高風險事件：Level 1 (警報)')
print("```")
print()

# 顯示 Cisco vs Forti 對比
print("【Cisco ASA vs Forti 對比】")
print("-" * 70)
print()

comparison = [
    ("規則", "Cisco ASA", "Forti"),
    ("範圍", "0-7", "1-4"),
    ("方向", "數字越小越嚴重", "數字越大越嚴重"),
    ("最嚴重", "0 (緊急)", "4 (最嚴重)"),
    ("最不嚴重", "7 (除錯)", "1 (最不嚴重)"),
    ("推播範圍", "0-4", "1-3"),
    ("顏色梯度", "紅→橙→黃→綠→藍→灰", "紅→橙→黃→綠"),
]

for label, cisco, forti in comparison:
    print(f"{label:<15} | {cisco:<25} | {forti}")

print()
print("-" * 70)
print()

# 顯示完整對照表
print("【完整對照表】")
print("-" * 70)
print()

print(f"{'Severity':<10} {'標籤':<10} {'英文':<18} {'顏色':<10} {'is_attack':<12} {'推播'}")
print("-" * 70)

severity_info = [
    (0, "Emergencies", "N/A", "過濾"),
    (1, "Alert", "1", "✅"),
    (2, "Critical", "1", "✅"),
    (3, "Error", "1", "✅"),
    (4, "Warning", "1", "✅"),
    (5, "Notification", "0", "❌"),
    (6, "Informational", "0", "❌"),
    (7, "Debugging", "0", "❌"),
]

for severity, english, is_attack, push in severity_info:
    label = get_severity_label(severity)
    color = get_severity_color(severity)
    print(f"{severity:<10} {label:<10} {english:<18} {color:<10} {is_attack:<12} {push}")

print()
print("=" * 70)
print("✅ 視覺化配置展示完成")
print()
print("📝 相關文件:")
print("  - docs/CISCO_SEVERITY_VISUALIZATION_GUIDE.md")
print("  - CISCO_SEVERITY_FIX_REPORT.md")
print("  - CISCO_SEVERITY_CHECKLIST.md")
print()
print("🧪 執行測試:")
print("  python test_severity_colors.py")
print()
print("=" * 70)
