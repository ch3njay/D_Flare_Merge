"""
Cisco ASA 改進功能測試腳本
測試：Severity 標籤規則、資料偵測、特徵工程
"""
import pandas as pd
import sys
from pathlib import Path

# 加入專案路徑
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from Cisco_ui.etl_pipeline.cisco_log_parser import CiscoASALogParser
from Cisco_ui.etl_pipeline.cisco_data_detector import CiscoDataStateDetector
from Cisco_ui.etl_pipeline.cisco_feature_engineering import CiscoASAFeatureEngineer


def test_severity_labeling():
    """測試 Severity 標籤規則"""
    print("\n" + "="*60)
    print("測試 1：Severity 標籤規則")
    print("="*60)
    
    parser = CiscoASALogParser()
    
    test_cases = [
        {"severity": "0", "expected": 0, "note": "emergencies (應過濾)"},
        {"severity": "1", "expected": 1, "note": "alert"},
        {"severity": "2", "expected": 1, "note": "critical"},
        {"severity": "3", "expected": 1, "note": "error"},
        {"severity": "4", "expected": 1, "note": "warning"},
        {"severity": "5", "expected": 0, "note": "notification"},
        {"severity": "6", "expected": 0, "note": "informational"},
        {"severity": "7", "expected": 0, "note": "debugging"},
    ]
    
    passed = 0
    failed = 0
    
    for case in test_cases:
        test_row = {
            "Severity": case["severity"],
            "SyslogID": "302013",
            "SourceIP": "192.168.1.1",
            "DestinationIP": "192.168.1.2",
            "Protocol": "TCP",
        }
        
        result = parser.parse_csv_line(test_row)
        
        if result and result["is_attack"] == case["expected"]:
            print(f"✅ Severity {case['severity']} ({case['note']}): is_attack = {result['is_attack']}")
            passed += 1
        else:
            actual = result["is_attack"] if result else "None"
            print(f"❌ Severity {case['severity']} ({case['note']}): 預期 {case['expected']}, 實際 {actual}")
            failed += 1
        
        # 測試過濾 Severity 0
        if case["severity"] == "0":
            should_filter = parser.should_filter_severity_0(case["severity"])
            if should_filter:
                print(f"   ✅ Severity 0 正確標記為應過濾")
            else:
                print(f"   ❌ Severity 0 未正確標記為應過濾")
    
    print(f"\n📊 測試結果：通過 {passed}/{passed + failed}")
    return failed == 0


def test_syslog_parsing():
    """測試 Syslog 解析"""
    print("\n" + "="*60)
    print("測試 2：Syslog 解析功能")
    print("="*60)
    
    parser = CiscoASALogParser()
    
    # 測試用的 Syslog
    test_log = "<166>Jul 23 2025 23:59:09: %ASA-6-302013: Built inbound TCP connection 1085592 for dmz:192.168.20.120/30117 (192.168.20.120/30117) to inside:192.168.10.100/1126 (192.168.10.100/1126)"
    
    result = parser.parse_syslog_line(test_log)
    
    if result:
        print("✅ 成功解析 Syslog")
        print(f"   Severity: {result['severity']}")
        print(f"   SyslogID: {result['syslog_id']}")
        print(f"   Source IP: {result['source_ip']}")
        print(f"   Source Port: {result['source_port']}")
        print(f"   Destination IP: {result['destination_ip']}")
        print(f"   Destination Port: {result['destination_port']}")
        print(f"   Protocol: {result['protocol']}")
        print(f"   Action: {result['action']}")
        print(f"   is_attack: {result['is_attack']}")
        
        # 驗證關鍵欄位
        checks = [
            (result['severity'] == '6', "Severity"),
            (result['syslog_id'] == '302013', "SyslogID"),
            (result['source_ip'] == '192.168.20.120', "Source IP"),
            (result['source_port'] == '30117', "Source Port"),
            (result['protocol'] == 'TCP', "Protocol"),
            (result['is_attack'] == 0, "is_attack (Severity 6 應為 0)"),
        ]
        
        all_passed = all(check[0] for check in checks)
        for check, name in checks:
            status = "✅" if check else "❌"
            print(f"   {status} {name}")
        
        return all_passed
    else:
        print("❌ 解析失敗")
        return False


def test_data_detection():
    """測試資料狀態偵測"""
    print("\n" + "="*60)
    print("測試 3：資料狀態偵測")
    print("="*60)
    
    detector = CiscoDataStateDetector()
    
    # 測試案例 1：原始 CSV
    print("\n📋 測試案例 A：原始 CSV 格式")
    df_raw = pd.DataFrame({
        "Severity": ["6", "4", "5"],
        "SyslogID": ["302013", "302014", "302015"],
        "SourceIP": ["192.168.1.1", "192.168.1.2", "192.168.1.3"],
        "DestinationIP": ["192.168.2.1", "192.168.2.2", "192.168.2.3"],
        "raw_log": ["log1", "log2", "log3"]
    })
    
    result1 = detector.detect_data_state(df_raw)
    
    # 測試案例 2：已處理資料
    print("\n📋 測試案例 B：已處理資料（有 is_attack）")
    df_processed = pd.DataFrame({
        "severity": ["6", "4", "5"],
        "syslog_id": ["302013", "302014", "302015"],
        "source_ip": ["192.168.1.1", "192.168.1.2", "192.168.1.3"],
        "destination_ip": ["192.168.2.1", "192.168.2.2", "192.168.2.3"],
        "is_attack": [0, 1, 0]
    })
    
    result2 = detector.detect_data_state(df_processed)
    
    # 測試案例 3：有特徵的資料
    print("\n📋 測試案例 C：包含特徵工程的資料")
    df_features = df_processed.copy()
    df_features["hour"] = [10, 11, 12]
    df_features["src_conn_count_1min"] = [5, 3, 7]
    
    result3 = detector.detect_data_state(df_features)
    
    # 驗證結果
    checks = [
        (result1["format"] == "csv_raw", "案例A: 偵測為原始 CSV"),
        (result1["needs_parsing"], "案例A: 需要解析"),
        (result2["format"] == "csv_processed", "案例B: 偵測為已處理"),
        (result2["has_is_attack"], "案例B: 有 is_attack"),
        (result3["format"] == "csv_with_features", "案例C: 偵測為有特徵"),
        (result3["has_features"], "案例C: 有特徵欄位"),
    ]
    
    all_passed = all(check[0] for check in checks)
    print("\n📊 驗證結果：")
    for check, name in checks:
        status = "✅" if check else "❌"
        print(f"   {status} {name}")
    
    return all_passed


def test_feature_engineering():
    """測試特徵工程"""
    print("\n" + "="*60)
    print("測試 4：特徵工程功能")
    print("="*60)
    
    # 建立測試資料
    test_data = pd.DataFrame({
        "datetime": pd.date_range("2025-07-23 10:00:00", periods=5, freq="1min"),
        "severity": ["6", "4", "5", "3", "6"],
        "syslog_id": ["302013", "302014", "302013", "302015", "302013"],
        "source_ip": ["192.168.1.1", "192.168.1.1", "192.168.1.2", "192.168.1.1", "192.168.1.2"],
        "source_port": [30117, 30118, 30119, 30120, 30121],
        "destination_ip": ["192.168.2.1", "192.168.2.2", "192.168.2.1", "192.168.2.3", "192.168.2.2"],
        "destination_port": [80, 443, 80, 22, 443],
        "protocol": ["TCP", "TCP", "UDP", "TCP", "UDP"],
        "action": ["built", "deny", "built", "deny", "built"],
        "bytes": [1024, 2048, 512, 4096, 1024],
        "duration": [10, 5, 15, 20, 8],
        "is_attack": [0, 1, 0, 1, 0]
    })
    
    print(f"📊 原始資料：{len(test_data)} 筆, {len(test_data.columns)} 個欄位")
    
    # 執行特徵工程
    engineer = CiscoASAFeatureEngineer()
    df_features = engineer.create_all_features(test_data)
    
    print(f"✅ 特徵工程後：{len(df_features)} 筆, {len(df_features.columns)} 個欄位")
    
    # 檢查關鍵特徵是否存在
    expected_features = [
        "hour", "day_of_week", "is_business_hour",
        "src_is_privileged_port", "dst_is_privileged_port",
        "src_is_private", "dst_is_private", "connection_direction",
        "severity_numeric", "severity_category",
        "syslogid_numeric", "syslogid_category",
    ]
    
    missing_features = [f for f in expected_features if f not in df_features.columns]
    
    if not missing_features:
        print("✅ 所有關鍵特徵都已建立")
        
        # 顯示部分特徵值
        print("\n📋 部分特徵值範例：")
        sample_features = ["hour", "src_is_private", "dst_is_common_port", "severity_category"]
        for feat in sample_features:
            if feat in df_features.columns:
                print(f"   {feat}: {df_features[feat].tolist()}")
        
        return True
    else:
        print(f"❌ 缺少以下特徵：{missing_features}")
        return False


def main():
    """執行所有測試"""
    print("\n" + "="*60)
    print("🧪 Cisco ASA 改進功能測試")
    print("="*60)
    
    tests = [
        ("Severity 標籤規則", test_severity_labeling),
        ("Syslog 解析", test_syslog_parsing),
        ("資料狀態偵測", test_data_detection),
        ("特徵工程", test_feature_engineering),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            passed = test_func()
            results.append((name, passed))
        except Exception as e:
            print(f"\n❌ 測試 '{name}' 發生錯誤：{e}")
            import traceback
            traceback.print_exc()
            results.append((name, False))
    
    # 總結
    print("\n" + "="*60)
    print("📊 測試總結")
    print("="*60)
    
    for name, passed in results:
        status = "✅ 通過" if passed else "❌ 失敗"
        print(f"{status}: {name}")
    
    total = len(results)
    passed_count = sum(1 for _, p in results if p)
    
    print(f"\n總計：{passed_count}/{total} 個測試通過")
    
    if passed_count == total:
        print("\n🎉 所有測試通過！")
    else:
        print(f"\n⚠️ 有 {total - passed_count} 個測試失敗")
    
    input("\n按任意鍵結束...")


if __name__ == "__main__":
    main()
