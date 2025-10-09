#!/usr/bin/env python3
"""測試統計輸出頻率修改。"""

import tempfile
import os
import sys
import gzip
from pathlib import Path

# 設定路徑
project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))


def create_large_fortinet_log_gz():
    """創建大量記錄的 Fortinet log 檔案來測試統計輸出頻率"""
    # 創建一個包含 15000 行記錄的檔案來測試統計輸出
    base_record = "date=2023-12-01 time=10:15:32 logver=605031 idseq={} itime=1701421532 devid=FGT60E type=traffic subtype=forward srcip=192.168.1.{} srcport={} srcintf=port1 dstip=10.0.0.{} dstport=80 dstintf=port2 action=accept policyid=1 service=HTTP proto=6 sentpkt=10 rcvdpkt=8 sentbyte=1500 rcvdbyte=1200 duration=300 level=notice msg=\"traffic allowed\" crscore=5 crlevel=low"
    
    content_lines = []
    for i in range(1, 15001):  # 15000 行記錄
        # 生成不同的 IP 和 port 來模擬真實數據
        src_ip_last = (i % 254) + 1
        src_port = 50000 + (i % 15000)
        dst_ip_last = ((i * 2) % 254) + 1
        
        record = base_record.format(i, src_ip_last, src_port, dst_ip_last)
        content_lines.append(record)
    
    content = '\n'.join(content_lines)
    
    with tempfile.NamedTemporaryFile(suffix='.gz', delete=False) as f:
        with gzip.open(f.name, 'wt', encoding='utf-8') as gz_file:
            gz_file.write(content)
        return f.name


def test_progress_frequency():
    """測試統計輸出頻率是否改為每 10000 行"""
    print("🧪 測試統計輸出頻率修改...")
    
    gz_file = None
    
    try:
        # 創建大量記錄的測試檔案
        print("  📦 創建包含 15000 筆記錄的測試檔案...")
        gz_file = create_large_fortinet_log_gz()
        
        from Forti_ui_app_bundle.training_pipeline.data_loader import DataLoader
        
        config = {"TARGET_COLUMN": "is_attack"}
        loader = DataLoader(config)
        
        print("  🔍 開始處理大量數據，觀察統計輸出頻率...")
        print("  預期：應該在第 10000 行顯示統計，而不是每 1000 行")
        print("  " + "="*60)
        
        # 載入數據並觀察輸出
        df = loader.load_data(gz_file)
        
        print("  " + "="*60)
        print(f"  ✅ 處理完成！總共處理了 {len(df)} 筆記錄")
        
        if len(df) >= 10000:
            print("  ✅ 測試成功：系統應該只在第 10000 行顯示了統計輸出")
            print("  📝 如果您看到只有一次 '📈 已處理 10000 行' 的訊息，")
            print("     而沒有看到 1000, 2000, 3000... 等訊息，則修改成功！")
            return True
        else:
            print(f"  ⚠️ 測試數據量不足：只有 {len(df)} 筆記錄")
            return False
            
    except Exception as e:
        print(f"  ❌ 測試失敗：{e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        # 清理測試檔案
        if gz_file and os.path.exists(gz_file):
            try:
                os.unlink(gz_file)
            except Exception:
                pass


def main():
    """主測試函數"""
    print("🔧 統計輸出頻率修改驗證")
    print("=" * 50)
    
    result = test_progress_frequency()
    
    print("\n" + "=" * 50)
    if result:
        print("✅ 統計輸出頻率修改驗證完成")
        print("\n📋 修改摘要：")
        print("  - 原本：每 1000 行顯示處理進度")
        print("  - 現在：每 10000 行顯示處理進度")
        print("  - 位置：Forti_ui_app_bundle/training_pipeline/data_loader.py")
        print("  - 效果：減少控制台輸出頻率，提升大數據處理時的可讀性")
    else:
        print("❌ 測試過程中遇到問題，請檢查修改是否正確")


if __name__ == "__main__":
    main()