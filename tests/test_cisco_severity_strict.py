"""
🔍 Cisco ASA Severity 完整嚴格檢測
===================================
本測試腳本涵蓋所有 Severity 相關的邏輯檢查，確保：
1. 配置正確性
2. 邏輯一致性
3. 沒有遺漏的錯誤
4. 與 Forti 的區別明確
"""

import sys
from pathlib import Path
import re

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
print("🔍 Cisco ASA Severity 完整嚴格檢測")
print("=" * 80)
print()

# ============================================================================
# 第一部分：配置完整性檢查
# ============================================================================
print("【第一部分】配置完整性檢查")
print("-" * 80)

test_results = []

# 測試 1.1: SEVERITY_LABELS 完整性
print("\n測試 1.1: SEVERITY_LABELS 配置完整性")
expected_labels = {
    0: "緊急", 1: "警報", 2: "嚴重", 3: "錯誤",
    4: "警告", 5: "通知", 6: "資訊", 7: "除錯"
}
labels_correct = True
for severity, expected_label in expected_labels.items():
    actual_label = SEVERITY_LABELS.get(severity)
    if actual_label != expected_label:
        print(f"  ❌ Severity {severity}: 預期 '{expected_label}', 實際 '{actual_label}'")
        labels_correct = False

if labels_correct:
    print("  ✅ 所有 SEVERITY_LABELS 正確")
    test_results.append(("SEVERITY_LABELS 完整性", True))
else:
    print("  ❌ SEVERITY_LABELS 有誤")
    test_results.append(("SEVERITY_LABELS 完整性", False))

# 測試 1.2: SEVERITY_COLORS 完整性
print("\n測試 1.2: SEVERITY_COLORS 配置完整性")
expected_colors = {
    0: "#8B0000", 1: "#DC143C", 2: "#FF4500", 3: "#FF8C00",
    4: "#FFD700", 5: "#90EE90", 6: "#87CEEB", 7: "#D3D3D3"
}
colors_correct = True
for severity, expected_color in expected_colors.items():
    actual_color = SEVERITY_COLORS.get(severity)
    if actual_color != expected_color:
        print(f"  ❌ Severity {severity}: 預期 '{expected_color}', 實際 '{actual_color}'")
        colors_correct = False

if colors_correct:
    print("  ✅ 所有 SEVERITY_COLORS 正確")
    test_results.append(("SEVERITY_COLORS 完整性", True))
else:
    print("  ❌ SEVERITY_COLORS 有誤")
    test_results.append(("SEVERITY_COLORS 完整性", False))

# ============================================================================
# 第二部分：檔案邏輯檢查
# ============================================================================
print("\n\n【第二部分】檔案邏輯檢查")
print("-" * 80)

# 測試 2.1: cisco_log_parser.py 邏輯
print("\n測試 2.1: cisco_log_parser.py 的 Severity 處理邏輯")
parser_file = Path(__file__).parent / "Cisco_ui" / "etl_pipeline" / "cisco_log_parser.py"
if parser_file.exists():
    parser_content = parser_file.read_text(encoding="utf-8")
    
    # 檢查是否有 Severity 0 過濾
    has_severity_0_filter = "severity_int == 0" in parser_content and "return None" in parser_content
    print(f"  {'✅' if has_severity_0_filter else '❌'} Severity 0 過濾邏輯")
    
    # 檢查 1-4 標記為攻擊
    has_14_attack = re.search(r'severity_int >= 1 and severity_int <= 4', parser_content)
    print(f"  {'✅' if has_14_attack else '❌'} Severity 1-4 標記為 is_attack=1")
    
    # 檢查 5-7 標記為正常
    has_57_normal = re.search(r'severity_int >= 5', parser_content) and "is_attack" in parser_content
    print(f"  {'✅' if has_57_normal else '❌'} Severity 5-7 標記為 is_attack=0")
    
    parser_logic_correct = has_severity_0_filter and has_14_attack and has_57_normal
    test_results.append(("cisco_log_parser.py 邏輯", parser_logic_correct))
else:
    print("  ❌ 找不到 cisco_log_parser.py")
    test_results.append(("cisco_log_parser.py 邏輯", False))

# 測試 2.2: log_mapping.py 邏輯
print("\n測試 2.2: log_mapping.py 的 is_attack_severity 邏輯")
mapping_file = Path(__file__).parent / "Cisco_ui" / "etl_pipeline" / "log_mapping.py"
if mapping_file.exists():
    mapping_content = mapping_file.read_text(encoding="utf-8")
    
    # 檢查函式存在
    has_function = "_is_attack_severity" in mapping_content
    print(f"  {'✅' if has_function else '❌'} _is_attack_severity 函式存在")
    
    # 檢查邏輯正確（1-4 為攻擊）
    has_correct_logic = re.search(r'severity_int >= 1 and severity_int <= 4.*return 1', mapping_content, re.DOTALL)
    print(f"  {'✅' if has_correct_logic else '❌'} Severity 1-4 返回 1")
    
    # 檢查其他返回 0
    has_else_logic = "return 0" in mapping_content
    print(f"  {'✅' if has_else_logic else '❌'} 其他 Severity 返回 0")
    
    mapping_logic_correct = has_function and has_correct_logic and has_else_logic
    test_results.append(("log_mapping.py 邏輯", mapping_logic_correct))
else:
    print("  ❌ 找不到 log_mapping.py")
    test_results.append(("log_mapping.py 邏輯", False))

# 測試 2.3: notifier.py 過濾邏輯
print("\n測試 2.3: notifier.py 的推播過濾邏輯")
notifier_file = Path(__file__).parent / "Cisco_ui" / "notifier.py"
if notifier_file.exists():
    notifier_content = notifier_file.read_text(encoding="utf-8")
    
    # 檢查過濾條件是否為 0-4
    has_04_filter = re.search(r'isin\(\[0,\s*1,\s*2,\s*3,\s*4\]\)', notifier_content)
    print(f"  {'✅' if has_04_filter else '❌'} 推播過濾條件為 Severity 0-4")
    
    # 檢查沒有舊的 1-3 過濾
    has_old_filter = re.search(r'isin\(\[1,\s*2,\s*3\]\)', notifier_content)
    print(f"  {'✅' if not has_old_filter else '❌'} 沒有舊的 Severity 1-3 過濾")
    
    notifier_logic_correct = has_04_filter and not has_old_filter
    test_results.append(("notifier.py 過濾邏輯", notifier_logic_correct))
else:
    print("  ❌ 找不到 notifier.py")
    test_results.append(("notifier.py 過濾邏輯", False))

# 測試 2.4: log_monitor.py 高風險判斷
print("\n測試 2.4: log_monitor.py 的高風險判斷邏輯")
monitor_file = Path(__file__).parent / "Cisco_ui" / "ui_pages" / "log_monitor.py"
if monitor_file.exists():
    monitor_content = monitor_file.read_text(encoding="utf-8")
    
    # 檢查是否使用 0-4 判斷
    has_04_check = re.search(r'isin\(\["0",\s*"1",\s*"2",\s*"3",\s*"4"\]\)', monitor_content)
    print(f"  {'✅' if has_04_check else '❌'} 高風險判斷使用 Severity 0-4")
    
    # 檢查沒有舊的 1-3 判斷
    has_old_check = re.search(r'isin\(\["1",\s*"2",\s*"3"\]\)', monitor_content)
    print(f"  {'✅' if not has_old_check else '❌'} 沒有舊的 Severity 1-3 判斷")
    
    monitor_logic_correct = has_04_check and not has_old_check
    test_results.append(("log_monitor.py 高風險判斷", monitor_logic_correct))
else:
    print("  ❌ 找不到 log_monitor.py")
    test_results.append(("log_monitor.py 高風險判斷", False))

# ============================================================================
# 第三部分：輔助函式檢查
# ============================================================================
print("\n\n【第三部分】輔助函式檢查")
print("-" * 80)

# 測試 3.1: get_severity_color 函式
print("\n測試 3.1: get_severity_color 函式")
color_test_cases = [
    (0, "#8B0000"),
    (4, "#FFD700"),
    (7, "#D3D3D3"),
    (99, "#808080")  # 預設值
]
color_function_correct = True
for severity, expected_color in color_test_cases:
    actual_color = get_severity_color(severity)
    if actual_color != expected_color:
        print(f"  ❌ Severity {severity}: 預期 '{expected_color}', 實際 '{actual_color}'")
        color_function_correct = False

if color_function_correct:
    print("  ✅ get_severity_color 函式正確")
    test_results.append(("get_severity_color 函式", True))
else:
    print("  ❌ get_severity_color 函式有誤")
    test_results.append(("get_severity_color 函式", False))

# 測試 3.2: get_severity_label 函式
print("\n測試 3.2: get_severity_label 函式")
label_test_cases = [
    (0, "緊急"),
    (4, "警告"),
    (7, "除錯"),
    (99, "未知")  # 預設值
]
label_function_correct = True
for severity, expected_label in label_test_cases:
    actual_label = get_severity_label(severity)
    if actual_label != expected_label:
        print(f"  ❌ Severity {severity}: 預期 '{expected_label}', 實際 '{actual_label}'")
        label_function_correct = False

if label_function_correct:
    print("  ✅ get_severity_label 函式正確")
    test_results.append(("get_severity_label 函式", True))
else:
    print("  ❌ get_severity_label 函式有誤")
    test_results.append(("get_severity_label 函式", False))

# 測試 3.3: format_severity_display 函式
print("\n測試 3.3: format_severity_display 函式")
format_test_cases = [
    (0, "Level 0 (緊急)"),
    (4, "Level 4 (警告)"),
    (7, "Level 7 (除錯)"),
]
format_function_correct = True
for severity, expected_format in format_test_cases:
    actual_format = format_severity_display(severity)
    if actual_format != expected_format:
        print(f"  ❌ Severity {severity}: 預期 '{expected_format}', 實際 '{actual_format}'")
        format_function_correct = False

if format_function_correct:
    print("  ✅ format_severity_display 函式正確")
    test_results.append(("format_severity_display 函式", True))
else:
    print("  ❌ format_severity_display 函式有誤")
    test_results.append(("format_severity_display 函式", False))

# ============================================================================
# 第四部分：邊界條件檢查
# ============================================================================
print("\n\n【第四部分】邊界條件檢查")
print("-" * 80)

# 測試 4.1: 邊界值測試
print("\n測試 4.1: 邊界值測試")
boundary_tests = [
    # (severity, expected_label, expected_is_attack)
    (0, "緊急", "過濾"),
    (1, "警報", "攻擊"),
    (4, "警告", "攻擊"),
    (5, "通知", "正常"),
    (7, "除錯", "正常"),
]

boundary_correct = True
for severity, expected_label, expected_category in boundary_tests:
    label = get_severity_label(severity)
    
    # 判斷類別
    if severity == 0:
        category = "過濾"
    elif 1 <= severity <= 4:
        category = "攻擊"
    else:
        category = "正常"
    
    if label != expected_label or category != expected_category:
        print(f"  ❌ Severity {severity}: 標籤='{label}' (預期'{expected_label}'), 類別='{category}' (預期'{expected_category}')")
        boundary_correct = False

if boundary_correct:
    print("  ✅ 所有邊界值測試通過")
    test_results.append(("邊界條件測試", True))
else:
    print("  ❌ 邊界值測試有誤")
    test_results.append(("邊界條件測試", False))

# ============================================================================
# 第五部分：與 Forti 對比檢查
# ============================================================================
print("\n\n【第五部分】與 Forti 對比檢查")
print("-" * 80)

print("\n測試 5.1: Cisco ASA vs Forti 方向驗證")
print("  Cisco ASA:")
print("    - 範圍: 0-7")
print("    - 方向: 數字越小越嚴重")
print("    - 最嚴重: 0 (緊急)")
print("    - 最不嚴重: 7 (除錯)")
print("    - 推播範圍: 0-4")
print()
print("  Forti:")
print("    - 範圍: 1-4")
print("    - 方向: 數字越大越嚴重")
print("    - 最嚴重: 4")
print("    - 最不嚴重: 1")
print("    - 推播範圍: 1-3")
print()

# 驗證最嚴重級別使用紅色
cisco_most_severe_color = get_severity_color(0)
is_red = cisco_most_severe_color in ["#8B0000", "#DC143C", "#FF0000"]
print(f"  {'✅' if is_red else '❌'} Cisco 最嚴重 (Severity 0) 使用紅色系: {cisco_most_severe_color}")

# 驗證最不嚴重級別使用灰色
cisco_least_severe_color = get_severity_color(7)
is_gray = cisco_least_severe_color in ["#D3D3D3", "#9E9E9E", "#808080"]
print(f"  {'✅' if is_gray else '❌'} Cisco 最不嚴重 (Severity 7) 使用灰色系: {cisco_least_severe_color}")

forti_comparison_correct = is_red and is_gray
test_results.append(("Cisco vs Forti 對比", forti_comparison_correct))

# ============================================================================
# 第六部分：文件完整性檢查
# ============================================================================
print("\n\n【第六部分】文件完整性檢查")
print("-" * 80)

# 檢查重要文件是否存在
important_docs = [
    "docs/CISCO_SEVERITY_VISUALIZATION_GUIDE.md",
    "CISCO_SEVERITY_FIX_REPORT.md",
    "CISCO_SEVERITY_CHECKLIST.md",
]

docs_complete = True
for doc in important_docs:
    doc_path = Path(__file__).parent / doc
    exists = doc_path.exists()
    print(f"  {'✅' if exists else '❌'} {doc}")
    if not exists:
        docs_complete = False

test_results.append(("文件完整性", docs_complete))

# ============================================================================
# 總結報告
# ============================================================================
print("\n\n" + "=" * 80)
print("📊 嚴格檢測總結報告")
print("=" * 80)

passed = sum(1 for _, result in test_results if result)
total = len(test_results)

print(f"\n總計: {passed}/{total} 測試通過\n")

for test_name, result in test_results:
    status = "✅ 通過" if result else "❌ 失敗"
    print(f"  {test_name:<30} {status}")

print("\n" + "=" * 80)

if passed == total:
    print("\n🎉 所有嚴格檢測通過！系統配置完全正確。")
    print("\n建議下一步:")
    print("  1. 執行完整的 UI 測試")
    print("  2. 測試實際的日誌解析")
    print("  3. 驗證推播功能")
    sys.exit(0)
else:
    print(f"\n⚠️ {total - passed} 個檢測失敗，請檢查相關配置。")
    print("\n失敗項目:")
    for test_name, result in test_results:
        if not result:
            print(f"  - {test_name}")
    sys.exit(1)
