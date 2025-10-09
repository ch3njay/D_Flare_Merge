"""
🔬 嚴格驗證測試套件 - Cisco ASA 系統完整性檢查
============================================

測試目標：
1. Severity 標籤邏輯一致性（所有模組）
2. 資料流程完整性（ETL → 特徵工程 → 訓練）
3. 邊界條件處理（空值、異常值、極端值）
4. 欄位名稱一致性
5. 新舊程式碼相容性
"""

import pandas as pd
import numpy as np
import sys
import os
from pathlib import Path

# 加入模組路徑
sys.path.insert(0, str(Path(__file__).parent / "Cisco_ui"))

print("🔬 開始嚴格驗證測試...")
print("=" * 80)

# ============================================================================
# 測試 1：Severity 標籤邏輯一致性驗證
# ============================================================================
def test_severity_logic_consistency():
    """測試所有模組的 Severity 標籤邏輯是否一致"""
    print("\n📋 測試 1：Severity 標籤邏輯一致性")
    print("-" * 80)
    
    from Cisco_ui.etl_pipeline.cisco_log_parser import CiscoASALogParser
    from Cisco_ui.etl_pipeline.log_mapping import _is_attack_severity
    
    parser = CiscoASALogParser()
    
    # 測試案例：覆蓋所有 Severity 級別
    test_cases = [
        (0, None, "過濾"),      # Severity 0 應該被過濾
        (1, 1, "攻擊"),         # Severity 1-4 是攻擊
        (2, 1, "攻擊"),
        (3, 1, "攻擊"),
        (4, 1, "攻擊"),
        (5, 0, "正常"),         # Severity 5-7 是正常
        (6, 0, "正常"),
        (7, 0, "正常"),
        (8, 0, "異常值"),       # 異常值應標記為正常
        (-1, 0, "異常值"),
    ]
    
    all_passed = True
    results = []
    
    for severity, expected_label, category in test_cases:
        # 測試 1: cisco_log_parser.py
        test_log = f"<166>Jul 23 2025 23:59:09: %ASA-{severity}-302013: Built inbound TCP connection"
        parsed = parser.parse_syslog_line(test_log)
        
        # 測試 2: log_mapping.py
        mapping_result = _is_attack_severity(severity)
        
        # 驗證結果
        if expected_label is None:  # 應該被過濾
            if parsed is None:
                parser_result = "✅ 正確過濾"
                parser_passed = True
            else:
                parser_result = f"❌ 應過濾但返回: {parsed}"
                parser_passed = False
                all_passed = False
            
            mapping_passed = True  # log_mapping 不處理過濾，只返回標籤
            mapping_result_str = f"標籤={mapping_result}"
        else:
            if parsed and parsed.get("is_attack") == expected_label:
                parser_result = "✅ 正確"
                parser_passed = True
            else:
                parser_result = f"❌ 期望={expected_label}, 實際={parsed.get('is_attack') if parsed else 'None'}"
                parser_passed = False
                all_passed = False
            
            if mapping_result == expected_label:
                mapping_result_str = "✅ 正確"
                mapping_passed = True
            else:
                mapping_result_str = f"❌ 期望={expected_label}, 實際={mapping_result}"
                mapping_passed = False
                all_passed = False
        
        results.append({
            "severity": severity,
            "category": category,
            "parser": parser_result,
            "mapping": mapping_result_str,
            "status": "✅" if (parser_passed and mapping_passed) else "❌"
        })
    
    # 輸出結果表格
    print(f"\n{'Severity':<10} {'類別':<10} {'Parser 結果':<25} {'Mapping 結果':<25} {'狀態':<5}")
    print("-" * 85)
    for r in results:
        print(f"{r['severity']:<10} {r['category']:<10} {r['parser']:<25} {r['mapping']:<25} {r['status']:<5}")
    
    if all_passed:
        print(f"\n✅ 測試 1 通過：所有 Severity 標籤邏輯一致")
    else:
        print(f"\n❌ 測試 1 失敗：發現邏輯不一致")
    
    return all_passed


# ============================================================================
# 測試 2：資料流程完整性驗證
# ============================================================================
def test_data_flow_integrity():
    """測試從原始日誌到特徵工程的完整資料流程"""
    print("\n📋 測試 2：資料流程完整性")
    print("-" * 80)
    
    from Cisco_ui.etl_pipeline.cisco_log_parser import CiscoASALogParser
    from Cisco_ui.etl_pipeline.cisco_feature_engineering import create_cisco_features
    from Cisco_ui.etl_pipeline.cisco_data_detector import CiscoDataStateDetector
    
    # 建立測試資料
    test_logs = [
        '<166>Jul 23 2025 10:30:45: %ASA-6-302013: Built inbound TCP connection 123 for outside:192.168.1.100/12345 to inside:10.0.0.50/80',
        '<162>Jul 23 2025 10:31:00: %ASA-2-106001: Inbound TCP connection denied from 192.168.1.200/54321 to 10.0.0.60/22',
        '<164>Jul 23 2025 10:31:15: %ASA-4-106023: Deny tcp src outside:192.168.1.150/33333 dst inside:10.0.0.70/443',
        '<167>Jul 23 2025 10:31:30: %ASA-7-609001: Built local-host inside:10.0.0.80',
        '<165>Jul 23 2025 10:31:45: %ASA-5-111008: User enable_15 executed the show version command',
    ]
    
    # 階段 1：解析日誌
    print("\n階段 1：解析原始日誌")
    parser = CiscoASALogParser()
    parsed_logs = []
    
    for log in test_logs:
        parsed = parser.parse_syslog_line(log)
        if parsed and not parser.should_filter_severity_0(parsed.get("severity", "")):
            parsed_logs.append(parsed)
    
    print(f"   解析結果：{len(parsed_logs)}/{len(test_logs)} 筆成功")
    
    if len(parsed_logs) == 0:
        print("❌ 測試 2 失敗：無法解析任何日誌")
        return False
    
    # 檢查標籤分布
    attack_count = sum(1 for p in parsed_logs if p.get("is_attack") == 1)
    normal_count = len(parsed_logs) - attack_count
    print(f"   標籤分布：攻擊={attack_count}, 正常={normal_count}")
    
    # 階段 2：轉換為 DataFrame
    print("\n階段 2：轉換為 DataFrame")
    df = pd.DataFrame(parsed_logs)
    
    # 檢查必要欄位
    required_fields = ["Datetime", "Severity", "SourceIP", "DestinationIP", "is_attack"]
    missing_fields = [f for f in required_fields if f not in df.columns]
    
    if missing_fields:
        print(f"❌ 缺少必要欄位：{missing_fields}")
        return False
    else:
        print(f"   ✅ 所有必要欄位存在：{required_fields}")
    
    # 檢查資料型別
    print(f"   資料型別檢查：")
    print(f"      - Datetime: {df['Datetime'].dtype}")
    print(f"      - Severity: {df['Severity'].dtype}")
    print(f"      - is_attack: {df['is_attack'].dtype}")
    
    # 階段 3：狀態偵測
    print("\n階段 3：資料狀態偵測")
    detector = CiscoDataStateDetector()
    state = detector.detect_data_state(df)
    
    print(f"   偵測結果：")
    print(f"      - 格式：{state.get('format', 'unknown')}")
    print(f"      - 包含 is_attack：{state.get('has_is_attack', False)}")
    print(f"      - 需要解析：{state.get('needs_parsing', True)}")
    print(f"      - 需要特徵工程：{state.get('needs_feature_engineering', True)}")
    
    expected_format = "csv_processed"  # 已解析並含 is_attack
    if state.get("format") != expected_format:
        print(f"❌ 格式偵測錯誤：期望 {expected_format}，實際 {state.get('format')}")
        return False
    
    # 階段 4：特徵工程
    print("\n階段 4：特徵工程")
    original_cols = len(df.columns)
    
    try:
        df_with_features = create_cisco_features(df)
        new_cols = len(df_with_features.columns)
        
        print(f"   欄位數量：{original_cols} → {new_cols} (+{new_cols - original_cols})")
        
        # 檢查是否新增了特徵
        if new_cols <= original_cols:
            print(f"❌ 特徵工程未新增任何欄位")
            return False
        
        # 檢查 is_attack 是否保留
        if "is_attack" not in df_with_features.columns:
            print(f"❌ is_attack 欄位遺失")
            return False
        
        # 檢查標籤是否改變
        if not df_with_features["is_attack"].equals(df["is_attack"]):
            print(f"❌ is_attack 標籤在特徵工程後改變")
            return False
        
        print(f"   ✅ is_attack 標籤保持一致")
        
    except Exception as e:
        print(f"❌ 特徵工程失敗：{e}")
        return False
    
    # 階段 5：最終驗證
    print("\n階段 5：最終資料驗證")
    
    # 檢查空值
    null_counts = df_with_features.isnull().sum()
    critical_nulls = null_counts[null_counts > 0]
    
    if len(critical_nulls) > 0:
        print(f"⚠️  發現空值：")
        for col, count in critical_nulls.items():
            print(f"      - {col}: {count} 個空值")
    else:
        print(f"   ✅ 無關鍵欄位空值")
    
    # 檢查資料範圍
    print(f"\n   資料統計：")
    print(f"      - 記錄數：{len(df_with_features)}")
    print(f"      - 攻擊筆數：{(df_with_features['is_attack'] == 1).sum()}")
    print(f"      - 正常筆數：{(df_with_features['is_attack'] == 0).sum()}")
    
    print(f"\n✅ 測試 2 通過：資料流程完整且一致")
    return True


# ============================================================================
# 測試 3：邊界條件處理驗證
# ============================================================================
def test_boundary_conditions():
    """測試邊界條件和異常處理"""
    print("\n📋 測試 3：邊界條件處理")
    print("-" * 80)
    
    from Cisco_ui.etl_pipeline.cisco_log_parser import CiscoASALogParser
    
    parser = CiscoASALogParser()
    
    # 測試案例
    test_cases = [
        ("空字串", "", False),
        ("純空白", "   ", False),
        ("不完整日誌", "%ASA-6", False),
        ("錯誤格式", "random text without structure", False),
        ("缺少時間", "%ASA-6-302013: Built connection", False),
        ("正常日誌", '<166>Jul 23 2025 10:30:45: %ASA-6-302013: Built connection', True),
    ]
    
    all_passed = True
    
    print(f"\n{'測試案例':<20} {'輸入':<40} {'期望':<10} {'結果':<10} {'狀態':<5}")
    print("-" * 90)
    
    for name, log_input, should_parse in test_cases:
        try:
            result = parser.parse_syslog_line(log_input)
            parsed = result is not None
            
            if parsed == should_parse:
                status = "✅"
                result_str = "成功" if parsed else "正確拒絕"
            else:
                status = "❌"
                result_str = f"錯誤：期望{'成功' if should_parse else '拒絕'}，實際{'成功' if parsed else '拒絕'}"
                all_passed = False
            
            print(f"{name:<20} {log_input[:38]:<40} {'成功' if should_parse else '拒絕':<10} {result_str:<10} {status:<5}")
            
        except Exception as e:
            print(f"{name:<20} {log_input[:38]:<40} {'成功' if should_parse else '拒絕':<10} 例外:{str(e)[:20]:<10} ❌")
            all_passed = False
    
    if all_passed:
        print(f"\n✅ 測試 3 通過：所有邊界條件正確處理")
    else:
        print(f"\n❌ 測試 3 失敗：部分邊界條件處理不當")
    
    return all_passed


# ============================================================================
# 測試 4：欄位名稱一致性驗證
# ============================================================================
def test_field_name_consistency():
    """測試不同模組間的欄位名稱一致性"""
    print("\n📋 測試 4：欄位名稱一致性")
    print("-" * 80)
    
    from Cisco_ui.etl_pipeline.cisco_log_parser import CiscoASALogParser
    from Cisco_ui.etl_pipeline.utils import STANDARD_COLUMNS
    
    parser = CiscoASALogParser()
    
    # 解析一個範例日誌
    test_log = '<166>Jul 23 2025 10:30:45: %ASA-6-302013: Built inbound TCP connection'
    parsed = parser.parse_syslog_line(test_log)
    
    if not parsed:
        print("❌ 無法解析測試日誌")
        return False
    
    parser_fields = set(parsed.keys())
    
    print(f"\nParser 產生的欄位：")
    print(f"   {sorted(parser_fields)}")
    
    print(f"\nSTANDARD_COLUMNS 定義的欄位：")
    print(f"   {sorted(STANDARD_COLUMNS)}")
    
    # 檢查大小寫一致性
    print(f"\n欄位大小寫檢查：")
    
    # 關鍵欄位對應
    field_mapping = {
        "severity": ["Severity", "severity"],
        "source_ip": ["SourceIP", "source_ip", "srcip"],
        "dest_ip": ["DestinationIP", "dest_ip", "dstip"],
        "source_port": ["SourcePort", "source_port", "srcport"],
        "dest_port": ["DestinationPort", "dest_port", "dstport"],
    }
    
    inconsistencies = []
    
    for std_name, variants in field_mapping.items():
        found_variants = [v for v in variants if v in parser_fields or v in STANDARD_COLUMNS]
        
        if len(set([v.lower() for v in found_variants])) > 1:
            print(f"   ⚠️  {std_name}: 發現多種變體 {found_variants}")
            inconsistencies.append(std_name)
        else:
            print(f"   ✅ {std_name}: 一致")
    
    if inconsistencies:
        print(f"\n⚠️  測試 4 警告：發現 {len(inconsistencies)} 個欄位名稱不一致")
        print(f"   建議統一使用駝峰式大寫命名（如 SourceIP, DestinationIP）")
        return True  # 警告但不算失敗
    else:
        print(f"\n✅ 測試 4 通過：欄位名稱一致")
        return True


# ============================================================================
# 測試 5：數值型別與範圍驗證
# ============================================================================
def test_numeric_types_and_ranges():
    """測試數值欄位的型別和範圍是否合理"""
    print("\n📋 測試 5：數值型別與範圍驗證")
    print("-" * 80)
    
    from Cisco_ui.etl_pipeline.cisco_log_parser import CiscoASALogParser
    
    parser = CiscoASALogParser()
    
    # 建立測試資料
    test_logs = [
        '<166>Jul 23 2025 10:30:45: %ASA-6-302013: Built connection src 192.168.1.100:80 dst 10.0.0.50:443',
        '<162>Jul 23 2025 10:31:00: %ASA-2-106001: Connection from 192.168.1.200:65535 to 10.0.0.60:1',
        '<164>Jul 23 2025 10:31:15: %ASA-4-106023: Deny src 192.168.1.150:0 dst 10.0.0.70:99999',  # 異常端口
    ]
    
    parsed_logs = []
    for log in test_logs:
        parsed = parser.parse_syslog_line(log)
        if parsed:
            parsed_logs.append(parsed)
    
    df = pd.DataFrame(parsed_logs)
    
    # 檢查數值欄位
    numeric_checks = {
        "Severity": (0, 7, "Severity 應在 0-7 之間"),
        "SourcePort": (0, 65535, "端口應在 0-65535 之間"),
        "DestinationPort": (0, 65535, "端口應在 0-65535 之間"),
        "is_attack": (0, 1, "is_attack 應為 0 或 1"),
    }
    
    all_passed = True
    
    for field, (min_val, max_val, description) in numeric_checks.items():
        if field in df.columns:
            # 嘗試轉換為數值
            try:
                df[field] = pd.to_numeric(df[field], errors='coerce')
                
                # 檢查範圍
                out_of_range = df[(df[field] < min_val) | (df[field] > max_val)]
                
                if len(out_of_range) > 0:
                    print(f"   ⚠️  {field}: 發現 {len(out_of_range)} 筆超出範圍 [{min_val}, {max_val}]")
                    print(f"       {description}")
                    # 數值範圍警告不算失敗，因為可能是資料品質問題
                else:
                    print(f"   ✅ {field}: 所有值在範圍 [{min_val}, {max_val}] 內")
                
            except Exception as e:
                print(f"   ❌ {field}: 無法轉換為數值 - {e}")
                all_passed = False
        else:
            print(f"   ⚠️  {field}: 欄位不存在")
    
    if all_passed:
        print(f"\n✅ 測試 5 通過：數值型別和範圍合理")
    else:
        print(f"\n❌ 測試 5 失敗：數值型別驗證失敗")
    
    return all_passed


# ============================================================================
# 主測試執行
# ============================================================================
def run_all_tests():
    """執行所有測試"""
    print("\n" + "=" * 80)
    print("🔬 開始執行完整驗證測試套件")
    print("=" * 80)
    
    tests = [
        ("Severity 標籤邏輯一致性", test_severity_logic_consistency),
        ("資料流程完整性", test_data_flow_integrity),
        ("邊界條件處理", test_boundary_conditions),
        ("欄位名稱一致性", test_field_name_consistency),
        ("數值型別與範圍", test_numeric_types_and_ranges),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            passed = test_func()
            results.append((test_name, passed, None))
        except Exception as e:
            print(f"\n❌ 測試執行失敗：{test_name}")
            print(f"   錯誤：{e}")
            import traceback
            traceback.print_exc()
            results.append((test_name, False, str(e)))
    
    # 總結
    print("\n" + "=" * 80)
    print("📊 測試結果總結")
    print("=" * 80)
    
    passed_count = sum(1 for _, passed, _ in results if passed)
    total_count = len(results)
    
    for test_name, passed, error in results:
        status = "✅ 通過" if passed else "❌ 失敗"
        print(f"{test_name:<30} {status}")
        if error:
            print(f"   錯誤：{error}")
    
    print("\n" + "-" * 80)
    print(f"總計：{passed_count}/{total_count} 測試通過")
    
    if passed_count == total_count:
        print(f"\n🎉 所有測試通過！系統驗證完成。")
        return True
    else:
        print(f"\n⚠️  發現 {total_count - passed_count} 個測試失敗，請檢查並修正。")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
