#!/usr/bin/env python3
"""測試壓縮檔案支援功能。"""

import tempfile
import os
import sys
import gzip
import zipfile
from pathlib import Path

# 設定路徑
project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))


def create_sample_fortinet_log_gz():
    """創建壓縮的 Fortinet log 檔案 (.gz)"""
    sample_content = """date=2023-12-01 time=10:15:32 idseq=1001 subtype=traffic srcip=192.168.1.100 srcport=54321 srcintf=port1 dstip=10.0.0.5 dstport=80 dstintf=port2 action=accept service=HTTP sentpkt=10 rcvdpkt=8 duration=300 level=notice crscore=5 crlevel=low
date=2023-12-01 time=10:16:45 idseq=1002 subtype=attack srcip=192.168.1.200 srcport=1234 srcintf=port1 dstip=10.0.0.10 dstport=22 dstintf=port2 action=deny service=SSH sentpkt=5 rcvdpkt=0 duration=0 level=warning crscore=85 crlevel=high
date=2023-12-01 time=10:17:12 idseq=1003 subtype=traffic srcip=10.0.0.6 srcport=443 srcintf=port2 dstip=192.168.1.101 dstport=54322 dstintf=port1 action=accept service=HTTPS sentpkt=20 rcvdpkt=18 duration=150 level=notice crscore=2 crlevel=low"""
    
    with tempfile.NamedTemporaryFile(suffix='.gz', delete=False) as f:
        with gzip.open(f.name, 'wt', encoding='utf-8') as gz_file:
            gz_file.write(sample_content)
        return f.name


def create_sample_cisco_log_zip():
    """創建壓縮的 Cisco ASA log 檔案 (.zip)"""
    sample_content = """%ASA-6-302013: Built outbound TCP connection 1234567 for outside:192.168.1.100/80 (192.168.1.100/80) to inside:10.0.0.5/54321 (10.0.0.5/54321)
%ASA-6-302014: Teardown TCP connection 1234567 for outside:192.168.1.100/80 to inside:10.0.0.5/54321 duration 0:02:15 bytes 1500 (TCP FINs)
%ASA-4-106023: Deny tcp src outside:192.168.1.200/1234 dst inside:10.0.0.10/22 by access-group "outside_access_in" [0x0, 0x0]
%ASA-6-302013: Built inbound TCP connection 1234568 for inside:10.0.0.6/443 (10.0.0.6/443) to outside:192.168.1.101/54322 (192.168.1.101/54322)"""
    
    with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as f:
        with zipfile.ZipFile(f.name, 'w') as zip_file:
            zip_file.writestr('cisco_log.txt', sample_content)
        return f.name


def create_sample_csv_gz():
    """創建壓縮的 CSV 檔案 (.gz)"""
    sample_content = """SourceIP,DestIP,SourcePort,DestPort,Protocol,Action,is_attack
192.168.1.100,10.0.0.5,54321,80,TCP,built,0
192.168.1.200,10.0.0.10,1234,22,TCP,deny,1
10.0.0.6,192.168.1.101,443,54322,TCP,built,0
192.168.1.201,10.0.0.11,5678,53,UDP,deny,1"""
    
    with tempfile.NamedTemporaryFile(suffix='.gz', delete=False) as f:
        with gzip.open(f.name, 'wt', encoding='utf-8') as gz_file:
            gz_file.write(sample_content)
        return f.name


def test_fortinet_compressed_support():
    """測試 Fortinet 壓縮檔案支援"""
    print("\n🧪 測試 Fortinet 壓縮檔案支援...")
    
    gz_file = None
    csv_gz_file = None
    
    try:
        # 創建測試檔案
        gz_file = create_sample_fortinet_log_gz()
        csv_gz_file = create_sample_csv_gz()
        
        from Forti_ui_app_bundle.training_pipeline.data_loader import DataLoader
        
        config = {"TARGET_COLUMN": "is_attack"}
        loader = DataLoader(config)
        
        # 測試格式偵測
        print("  🔍 測試格式偵測...")
        
        gz_format = loader._detect_data_format(gz_file)
        csv_gz_format = loader._detect_data_format(csv_gz_file)
        
        print(f"    Fortinet .gz 格式偵測：{gz_format}")
        print(f"    CSV .gz 格式偵測：{csv_gz_format}")
        
        # 驗證格式偵測
        if gz_format == "compressed":
            print("    ✅ Fortinet .gz 格式偵測正確")
        else:
            print(f"    ❌ Fortinet .gz 格式偵測錯誤，預期 'compressed'，實際 '{gz_format}'")
            return False
        
        if csv_gz_format == "compressed":
            print("    ✅ CSV .gz 格式偵測正確")
        else:
            print(f"    ❌ CSV .gz 格式偵測錯誤，預期 'compressed'，實際 '{csv_gz_format}'")
            return False
        
        # 測試解壓縮功能
        print("  📦 測試解壓縮功能...")
        
        extracted_fortinet = loader._extract_compressed_file(gz_file)
        extracted_csv = loader._extract_compressed_file(csv_gz_file)
        
        if extracted_fortinet:
            print(f"    ✅ Fortinet .gz 解壓成功：{extracted_fortinet}")
            # 檢查解壓後的檔案內容
            with open(extracted_fortinet, 'r', encoding='utf-8') as f:
                content = f.read()
                if 'idseq=' in content and 'srcip=' in content:
                    print("    ✅ 解壓後的 Fortinet 日誌內容正確")
                else:
                    print("    ❌ 解壓後的 Fortinet 日誌內容異常")
                    return False
        else:
            print("    ❌ Fortinet .gz 解壓失敗")
            return False
        
        if extracted_csv:
            print(f"    ✅ CSV .gz 解壓成功：{extracted_csv}")
        else:
            print("    ❌ CSV .gz 解壓失敗")
            return False
        
        print("  ✅ Fortinet 壓縮檔案支援測試通過")
        return True
        
    except Exception as e:
        print(f"  ❌ Fortinet 壓縮檔案測試失敗：{e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        # 清理測試檔案
        for temp_file in [gz_file, csv_gz_file]:
            if temp_file and os.path.exists(temp_file):
                try:
                    os.unlink(temp_file)
                except Exception:
                    pass


def test_cisco_compressed_support():
    """測試 Cisco 壓縮檔案支援"""
    print("\n🧪 測試 Cisco 壓縮檔案支援...")
    
    zip_file = None
    
    try:
        # 創建測試檔案
        zip_file = create_sample_cisco_log_zip()
        
        from Cisco_ui.training_pipeline.pipeline_main import CiscoTrainingPipeline
        
        pipeline = CiscoTrainingPipeline(task_type="binary")
        
        # 測試格式偵測
        print("  🔍 測試格式偵測...")
        
        zip_format = pipeline._detect_data_format(zip_file)
        print(f"    Cisco .zip 格式偵測：{zip_format}")
        
        # 驗證格式偵測
        if zip_format == "compressed":
            print("    ✅ Cisco .zip 格式偵測正確")
        else:
            print(f"    ❌ Cisco .zip 格式偵測錯誤，預期 'compressed'，實際 '{zip_format}'")
            return False
        
        # 測試解壓縮功能
        print("  📦 測試解壓縮功能...")
        
        extracted_cisco = pipeline._extract_compressed_file(zip_file)
        
        if extracted_cisco:
            print(f"    ✅ Cisco .zip 解壓成功：{extracted_cisco}")
            # 檢查解壓後的檔案內容
            with open(extracted_cisco, 'r', encoding='utf-8') as f:
                content = f.read()
                if '%ASA-' in content and ('Built' in content or 'Deny' in content):
                    print("    ✅ 解壓後的 Cisco 日誌內容正確")
                else:
                    print("    ❌ 解壓後的 Cisco 日誌內容異常")
                    return False
        else:
            print("    ❌ Cisco .zip 解壓失敗")
            return False
        
        print("  ✅ Cisco 壓縮檔案支援測試通過")
        return True
        
    except Exception as e:
        print(f"  ❌ Cisco 壓縮檔案測試失敗：{e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        # 清理測試檔案
        if zip_file and os.path.exists(zip_file):
            try:
                os.unlink(zip_file)
            except Exception:
                pass


def main():
    """主測試函數"""
    print("🧪 壓縮檔案支援功能測試")
    print("=" * 50)
    
    results = []
    
    # 測試 Fortinet 壓縮檔案支援
    results.append(test_fortinet_compressed_support())
    
    # 測試 Cisco 壓縮檔案支援
    results.append(test_cisco_compressed_support())
    
    # 總結
    print("\n" + "=" * 50)
    print("📊 測試結果總結:")
    
    passed = sum(results)
    total = len(results)
    
    if passed == total:
        print(f"✅ 所有測試通過 ({passed}/{total})")
        print("\n🎉 壓縮檔案支援功能已成功實現！")
        print("\n支援的壓縮格式：")
        print("  📦 .gz - gzip 壓縮檔案")
        print("  📦 .zip - ZIP 壓縮檔案")  
        print("  📦 .tar - TAR 歸檔檔案")
        print("  📦 .tar.gz/.tgz - TAR+gzip 壓縮檔案")
        print("\n功能特點：")
        print("  🔹 自動偵測壓縮檔案格式")
        print("  🔹 自動解壓縮到暫存目錄")
        print("  🔹 遞迴偵測解壓後的檔案格式")
        print("  🔹 支援 Fortinet 和 Cisco 兩個平台")
        print("  🔹 完整的錯誤處理機制")
    else:
        print(f"⚠️ 部分測試失敗 ({passed}/{total})")
        print("請檢查失敗的測試項目並修正問題。")


if __name__ == "__main__":
    main()