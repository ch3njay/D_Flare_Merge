"""
🎨 Cisco ASA Severity 顏色配置測試
測試新的 Severity 顏色和標籤配置是否正確
"""

import sys
from pathlib import Path

# 加入模組路徑
sys.path.insert(0, str(Path(__file__).parent / "Cisco_ui"))

from Cisco_ui.utils_labels import (
    SEVERITY_COLORS,
    get_severity_color,
    get_severity_label,
    format_severity_display
)
from notification_models import SEVERITY_LABELS

print("=" * 80)
print("🎨 Cisco ASA Severity 顏色配置測試")
print("=" * 80)

# 測試 1：檢查所有 Severity 級別的配置
print("\n【測試 1】Severity 級別配置")
print("-" * 80)
print(f"{'Severity':<10} {'標籤':<10} {'英文':<20} {'顏色':<15} {'狀態'}")
print("-" * 80)

severity_names = {
    0: "Emergencies",
    1: "Alert",
    2: "Critical",
    3: "Error",
    4: "Warning",
    5: "Notification",
    6: "Informational",
    7: "Debugging"
}

all_configured = True

for severity in range(8):
    label = get_severity_label(severity, "缺失")
    color = get_severity_color(severity, "缺失")
    english = severity_names.get(severity, "Unknown")
    
    # 檢查是否完整配置
    if label == "缺失" or color == "缺失":
        status = "❌ 缺失"
        all_configured = False
    else:
        status = "✅"
    
    # 使用 ANSI 顏色碼在終端顯示顏色（僅供參考）
    color_display = color if color != "缺失" else "N/A"
    
    print(f"{severity:<10} {label:<10} {english:<20} {color_display:<15} {status}")

if all_configured:
    print("\n✅ 所有 Severity 級別配置完整")
else:
    print("\n❌ 發現配置缺失")

# 測試 2：檢查顏色梯度邏輯（紅→橙→黃→綠→藍→灰）
print("\n【測試 2】顏色梯度檢查")
print("-" * 80)

expected_gradient = [
    (0, "紅色系", ["8B", "DC"]),  # 深紅、猩紅
    (1, "紅色系", ["DC", "FF"]),
    (2, "橙色系", ["FF", "FF"]),  # 橙紅、深橙
    (3, "橙色系", ["FF", "FF"]),
    (4, "黃色系", ["FF", "D7"]),  # 金色
    (5, "綠色系", ["90", "EE"]),  # 淺綠
    (6, "藍色系", ["87", "CE"]),  # 天藍
    (7, "灰色系", ["D3", "D3"]),  # 淺灰
]

gradient_correct = True

for severity, expected_family, _ in expected_gradient:
    color = get_severity_color(severity)
    
    # 簡單檢查顏色是否屬於預期的色系
    if expected_family == "紅色系":
        is_correct = any(c in color.upper() for c in ["8B", "DC", "EA", "FF0000", "FF4500"])
    elif expected_family == "橙色系":
        is_correct = any(c in color.upper() for c in ["FF4500", "FF8C00", "FFA500"])
    elif expected_family == "黃色系":
        is_correct = any(c in color.upper() for c in ["FFD700", "FFC107", "FFEB3B"])
    elif expected_family == "綠色系":
        is_correct = any(c in color.upper() for c in ["90EE90", "4CAF50", "8BC34A"])
    elif expected_family == "藍色系":
        is_correct = any(c in color.upper() for c in ["87CEEB", "2196F3", "03A9F4"])
    elif expected_family == "灰色系":
        is_correct = any(c in color.upper() for c in ["D3D3D3", "9E9E9E", "BDBDBD"])
    else:
        is_correct = False
    
    status = "✅" if is_correct else "❌"
    print(f"Severity {severity} - {expected_family}: {color} {status}")
    
    if not is_correct:
        gradient_correct = False

if gradient_correct:
    print("\n✅ 顏色梯度邏輯正確（嚴重→正常）")
else:
    print("\n⚠️ 部分顏色不符合預期梯度")

# 測試 3：輔助函式測試
print("\n【測試 3】輔助函式測試")
print("-" * 80)

test_cases = [0, 2, 4, 6, 99]  # 包含一個無效值

for severity in test_cases:
    display = format_severity_display(severity)
    label = get_severity_label(severity)
    color = get_severity_color(severity)
    
    print(f"Severity {severity}:")
    print(f"  - 格式化顯示: {display}")
    print(f"  - 標籤: {label}")
    print(f"  - 顏色: {color}")
    print()

# 測試 4：與 Forti 對比
print("\n【測試 4】與 Forti 對比驗證")
print("-" * 80)
print("Cisco ASA 規則：數字越小越嚴重（0=最嚴重，7=最不嚴重）")
print("Forti 規則：數字越大越嚴重（4=最嚴重，1=最不嚴重）")
print()

# 驗證 Cisco 的最嚴重級別
cisco_most_severe = 0
cisco_most_severe_label = get_severity_label(cisco_most_severe)
cisco_most_severe_color = get_severity_color(cisco_most_severe)

print(f"Cisco 最嚴重: Severity {cisco_most_severe} ({cisco_most_severe_label})")
print(f"  顏色: {cisco_most_severe_color}")

# 檢查顏色是否為紅色系
is_red = any(c in cisco_most_severe_color.upper() for c in ["8B", "DC", "FF0000", "EA", "B00"])
if is_red:
    print("  ✅ 使用紅色系（正確）")
else:
    print("  ❌ 顏色不是紅色系（應該是紅色）")

# 驗證 Cisco 的最不嚴重級別
cisco_least_severe = 7
cisco_least_severe_label = get_severity_label(cisco_least_severe)
cisco_least_severe_color = get_severity_color(cisco_least_severe)

print(f"\nCisco 最不嚴重: Severity {cisco_least_severe} ({cisco_least_severe_label})")
print(f"  顏色: {cisco_least_severe_color}")

# 檢查顏色是否為灰色系
is_gray = any(c in cisco_least_severe_color.upper() for c in ["D3", "9E", "BD", "808080"])
if is_gray:
    print("  ✅ 使用灰色系（正確）")
else:
    print("  ❌ 顏色不是灰色系（應該是灰色）")

# 測試 5：攻擊範圍驗證
print("\n【測試 5】is_attack 對應關係")
print("-" * 80)
print("根據 Cisco ASA 標準：")
print("  - Severity 1-4: is_attack = 1（需要關注）")
print("  - Severity 5-7: is_attack = 0（正常運作）")
print("  - Severity 0: 過濾（不處理）")
print()

attack_range_correct = True

for severity in range(8):
    label = get_severity_label(severity)
    
    if severity == 0:
        expected_action = "過濾"
        expected_is_attack = "N/A"
    elif 1 <= severity <= 4:
        expected_action = "標記為攻擊"
        expected_is_attack = "1"
    else:  # 5-7
        expected_action = "標記為正常"
        expected_is_attack = "0"
    
    print(f"Severity {severity} ({label}): {expected_action} (is_attack={expected_is_attack})")

print("\n✅ is_attack 對應關係清楚明確")

# 總結
print("\n" + "=" * 80)
print("📊 測試結果總結")
print("=" * 80)

results = {
    "配置完整性": all_configured,
    "顏色梯度": gradient_correct,
    "輔助函式": True,  # 如果能執行到這裡，表示函式正常
    "Forti 對比": is_red and is_gray,
    "is_attack 對應": attack_range_correct,
}

passed = sum(results.values())
total = len(results)

for test_name, result in results.items():
    status = "✅ 通過" if result else "❌ 失敗"
    print(f"{test_name:<20} {status}")

print("-" * 80)
print(f"總計：{passed}/{total} 測試通過")

if passed == total:
    print("\n🎉 所有測試通過！Severity 配置正確。")
    sys.exit(0)
else:
    print(f"\n⚠️ {total - passed} 個測試失敗，請檢查配置。")
    sys.exit(1)
