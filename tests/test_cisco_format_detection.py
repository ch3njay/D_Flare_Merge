#!/usr/bin/env python3
"""測試 Cisco 訓練管線的格式自動偵測功能。"""

import tempfile
import os


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


def test_cisco_format_detection():
    """測試 Cisco 格式偵測功能"""
    print("🧪 測試 Cisco 訓練管線的格式自動偵測功能")
    
    # 測試檔案
    cisco_log_file = None
    csv_file = None
    
    try:
        # 創建測試檔案
        cisco_log_file = create_sample_cisco_log()
        csv_file = create_sample_csv()
        
        print(f"📄 Cisco Log 檔案：{cisco_log_file}")
        print(f"📄 CSV 檔案：{csv_file}")
        
        # 導入 Cisco 訓練管線
        from Cisco_ui.training_pipeline.pipeline_main import CiscoTrainingPipeline
        
        # 建立管線實例
        pipeline = CiscoTrainingPipeline(task_type="binary")
        
        # 測試格式偵測
        print("\n🔍 測試格式偵測...")
        
        cisco_format = pipeline._detect_data_format(cisco_log_file)
        csv_format = pipeline._detect_data_format(csv_file)
        
        print(f"Cisco Log 格式偵測結果：{cisco_format}")
        print(f"CSV 格式偵測結果：{csv_format}")
        
        # 驗證結果
        if cisco_format == "cisco_asa_log":
            print("✅ Cisco ASA Log 格式偵測正確")
        else:
            print(f"❌ Cisco ASA Log 格式偵測錯誤，預期 'cisco_asa_log'，實際 '{cisco_format}'")
        
        if csv_format == "csv":
            print("✅ CSV 格式偵測正確")
        else:
            print(f"❌ CSV 格式偵測錯誤，預期 'csv'，實際 '{csv_format}'")
        
        # 測試資料載入（僅 CSV，因為 Cisco ETL 需要完整模組）
        print("\n📊 測試 CSV 資料載入...")
        try:
            df = pipeline._load_csv_with_fallback(csv_file)
            print(f"✅ CSV 載入成功：{len(df)} 筆資料，{len(df.columns)} 欄位")
            print(f"欄位：{list(df.columns)}")
        except Exception as e:
            print(f"❌ CSV 載入失敗：{e}")
        
    except ImportError as e:
        print(f"❌ 無法導入模組：{e}")
        print("請確認您在正確的目錄中執行此測試")
    except Exception as e:
        print(f"❌ 測試失敗：{e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # 清理測試檔案
        for temp_file in [cisco_log_file, csv_file]:
            if temp_file and os.path.exists(temp_file):
                try:
                    os.unlink(temp_file)
                except Exception:
                    pass


if __name__ == "__main__":
    test_cisco_format_detection()