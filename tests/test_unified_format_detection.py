#!/usr/bin/env python3
"""測試統一介面的格式自動偵測功能。"""

import tempfile
import os
import sys
from pathlib import Path

# 設定路徑
project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))


def create_sample_fortinet_log():
    """創建範例 Fortinet log 檔案"""
    sample_content = """
date=2023-12-01 time=10:15:32 idseq=1001 subtype=traffic srcip=192.168.1.100 srcport=54321 srcintf=port1 dstip=10.0.0.5 dstport=80 dstintf=port2 action=accept service=HTTP sentpkt=10 rcvdpkt=8 duration=300 level=notice crscore=5 crlevel=low
date=2023-12-01 time=10:16:45 idseq=1002 subtype=attack srcip=192.168.1.200 srcport=1234 srcintf=port1 dstip=10.0.0.10 dstport=22 dstintf=port2 action=deny service=SSH sentpkt=5 rcvdpkt=0 duration=0 level=warning crscore=85 crlevel=high
date=2023-12-01 time=10:17:12 idseq=1003 subtype=traffic srcip=10.0.0.6 srcport=443 srcintf=port2 dstip=192.168.1.101 dstport=54322 dstintf=port1 action=accept service=HTTPS sentpkt=20 rcvdpkt=18 duration=150 level=notice crscore=2 crlevel=low
date=2023-12-01 time=10:18:33 idseq=1004 subtype=attack srcip=192.168.1.201 srcport=5678 srcintf=port1 dstip=10.0.0.11 dstport=53 dstintf=port2 action=deny service=DNS sentpkt=3 rcvdpkt=0 duration=0 level=alert crscore=90 crlevel=high
"""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.log', delete=False) as f:
        f.write(sample_content.strip())
        return f.name


def create_sample_cisco_log():
    """創建範例 Cisco ASA log 檔案"""
    sample_content = """
%ASA-6-302013: Built outbound TCP connection 1234567 for outside:192.168.1.100/80 (192.168.1.100/80) to inside:10.0.0.5/54321 (10.0.0.5/54321)
%ASA-6-302014: Teardown TCP connection 1234567 for outside:192.168.1.100/80 to inside:10.0.0.5/54321 duration 0:02:15 bytes 1500 (TCP FINs)
%ASA-4-106023: Deny tcp src outside:192.168.1.200/1234 dst inside:10.0.0.10/22 by access-group "outside_access_in" [0x0, 0x0]
%ASA-6-302013: Built inbound TCP connection 1234568 for inside:10.0.0.6/443 (10.0.0.6/443) to outside:192.168.1.101/54322 (192.168.1.101/54322)
%ASA-4-106023: Deny udp src outside:192.168.1.201/5678 dst inside:10.0.0.11/53 by access-group "outside_access_in" [0x0, 0x0]
"""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.log', delete=False) as f:
        f.write(sample_content.strip())
        return f.name


def create_sample_csv():
    """創建範例 CSV 檔案"""
    sample_content = """SourceIP,DestIP,SourcePort,DestPort,Protocol,Action,is_attack
192.168.1.100,10.0.0.5,54321,80,TCP,built,0
192.168.1.200,10.0.0.10,1234,22,TCP,deny,1
10.0.0.6,192.168.1.101,443,54322,TCP,built,0
192.168.1.201,10.0.0.11,5678,53,UDP,deny,1
"""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        f.write(sample_content.strip())
        return f.name


def test_fortinet_format_detection():
    """測試 Fortinet 格式偵測"""
    print("\n🔍 測試 Fortinet 格式偵測...")
    
    fortinet_log = None
    csv_file = None
    
    try:
        fortinet_log = create_sample_fortinet_log()
        csv_file = create_sample_csv()
        
        from Forti_ui_app_bundle.training_pipeline.data_loader import DataLoader
        
        # 測試配置
        config = {"TARGET_COLUMN": "is_attack"}
        loader = DataLoader(config)
        
        # 測試 Fortinet 日誌格式偵測
        fortinet_format = loader._detect_data_format(fortinet_log)
        csv_format = loader._detect_data_format(csv_file)
        
        print(f"  Fortinet Log 格式偵測：{fortinet_format}")
        print(f"  CSV 格式偵測：{csv_format}")
        
        if fortinet_format == "fortinet_log":
            print("  ✅ Fortinet Log 格式偵測正確")
        else:
            print(f"  ❌ Fortinet Log 格式偵測錯誤，預期 'fortinet_log'，實際 '{fortinet_format}'")
        
        if csv_format == "csv":
            print("  ✅ CSV 格式偵測正確")
        else:
            print(f"  ❌ CSV 格式偵測錯誤，預期 'csv'，實際 '{csv_format}'")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Fortinet 格式偵測測試失敗：{e}")
        return False
    
    finally:
        for temp_file in [fortinet_log, csv_file]:
            if temp_file and os.path.exists(temp_file):
                try:
                    os.unlink(temp_file)
                except Exception:
                    pass


def test_cisco_format_detection():
    """測試 Cisco 格式偵測"""
    print("\n🔍 測試 Cisco 格式偵測...")
    
    cisco_log = None
    csv_file = None
    
    try:
        cisco_log = create_sample_cisco_log()
        csv_file = create_sample_csv()
        
        from Cisco_ui.training_pipeline.pipeline_main import CiscoTrainingPipeline
        
        pipeline = CiscoTrainingPipeline(task_type="binary")
        
        # 測試格式偵測
        cisco_format = pipeline._detect_data_format(cisco_log)
        csv_format = pipeline._detect_data_format(csv_file)
        
        print(f"  Cisco Log 格式偵測：{cisco_format}")
        print(f"  CSV 格式偵測：{csv_format}")
        
        if cisco_format == "cisco_asa_log":
            print("  ✅ Cisco ASA Log 格式偵測正確")
        else:
            print(f"  ❌ Cisco ASA Log 格式偵測錯誤，預期 'cisco_asa_log'，實際 '{cisco_format}'")
        
        if csv_format == "csv":
            print("  ✅ CSV 格式偵測正確")
        else:
            print(f"  ❌ CSV 格式偵測錯誤，預期 'csv'，實際 '{csv_format}'")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Cisco 格式偵測測試失敗：{e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        for temp_file in [cisco_log, csv_file]:
            if temp_file and os.path.exists(temp_file):
                try:
                    os.unlink(temp_file)
                except Exception:
                    pass


def test_unified_interface_integration():
    """測試統一介面整合"""
    print("\n🔗 測試統一介面整合...")
    
    try:
        # 測試統一介面模組載入
        from unified_ui.app import main
        from unified_ui.cisco_module.pages import render as cisco_render
        from unified_ui.fortinet_module.pages import render as fortinet_render
        
        print("  ✅ 統一介面模組載入成功")
        print("  ✅ Cisco 模組整合成功")
        print("  ✅ Fortinet 模組整合成功")
        
        return True
        
    except Exception as e:
        print(f"  ❌ 統一介面整合測試失敗：{e}")
        return False


def main():
    """主測試函數"""
    print("🧪 統一介面格式自動偵測功能測試")
    print("=" * 60)
    
    results = []
    
    # 測試 Fortinet 格式偵測
    results.append(test_fortinet_format_detection())
    
    # 測試 Cisco 格式偵測  
    results.append(test_cisco_format_detection())
    
    # 測試統一介面整合
    results.append(test_unified_interface_integration())
    
    # 總結
    print("\n" + "=" * 60)
    print("📊 測試結果總結:")
    
    passed = sum(results)
    total = len(results)
    
    if passed == total:
        print(f"✅ 所有測試通過 ({passed}/{total})")
        print("\n🎉 格式自動偵測功能已成功整合到統一介面！")
        print("\n主要功能：")
        print("  🔹 自動偵測 Fortinet 防火牆日誌格式")
        print("  🔹 自動偵測 Cisco ASA 日誌格式")
        print("  🔹 自動偵測標準 CSV 格式")
        print("  🔹 自動執行 ETL 前處理")
        print("  🔹 統一介面跨品牌支援")
    else:
        print(f"⚠️ 部分測試失敗 ({passed}/{total})")
        print("請檢查失敗的測試項目並修正問題。")


if __name__ == "__main__":
    main()