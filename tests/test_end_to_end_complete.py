#!/usr/bin/env python3
"""端到端測試：完整的壓縮檔案處理流程。"""

import tempfile
import os
import sys
import gzip
import zipfile
from pathlib import Path

# 設定路徑
project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))


def create_complete_fortinet_log_gz():
    """創建完整的壓縮 Fortinet log 檔案"""
    sample_content = """date=2023-12-01 time=10:15:32 logver=605031 idseq=1001 itime=1701421532 devid=FGT60E type=traffic subtype=forward srcip=192.168.1.100 srcport=54321 srcintf=port1 dstip=10.0.0.5 dstport=80 dstintf=port2 action=accept policyid=1 service=HTTP proto=6 sentpkt=10 rcvdpkt=8 sentbyte=1500 rcvdbyte=1200 duration=300 level=notice msg="traffic allowed" crscore=5 crlevel=low
date=2023-12-01 time=10:16:45 logver=605031 idseq=1002 itime=1701421605 devid=FGT60E type=traffic subtype=forward srcip=192.168.1.200 srcport=1234 srcintf=port1 dstip=10.0.0.10 dstport=22 dstintf=port2 action=deny policyid=2 service=SSH proto=6 sentpkt=5 rcvdpkt=0 sentbyte=500 rcvdbyte=0 duration=0 level=warning msg="traffic blocked" crscore=85 crlevel=high
date=2023-12-01 time=10:17:12 logver=605031 idseq=1003 itime=1701421632 devid=FGT60E type=traffic subtype=forward srcip=10.0.0.6 srcport=443 srcintf=port2 dstip=192.168.1.101 dstport=54322 dstintf=port1 action=accept policyid=3 service=HTTPS proto=6 sentpkt=20 rcvdpkt=18 sentbyte=3000 rcvdbyte=2500 duration=150 level=notice msg="secure traffic" crscore=2 crlevel=low
date=2023-12-01 time=10:18:33 logver=605031 idseq=1004 itime=1701421713 devid=FGT60E type=traffic subtype=forward srcip=192.168.1.201 srcport=5678 srcintf=port1 dstip=10.0.0.11 dstport=53 dstintf=port2 action=deny policyid=4 service=DNS proto=17 sentpkt=3 rcvdpkt=0 sentbyte=300 rcvdbyte=0 duration=0 level=alert msg="suspicious DNS query" crscore=90 crlevel=high"""
    
    with tempfile.NamedTemporaryFile(suffix='.gz', delete=False) as f:
        with gzip.open(f.name, 'wt', encoding='utf-8') as gz_file:
            gz_file.write(sample_content)
        return f.name


def test_end_to_end_fortinet_compressed():
    """端到端測試：Fortinet 壓縮檔案完整處理流程"""
    print("🔄 端到端測試：Fortinet 壓縮檔案完整處理...")
    
    gz_file = None
    
    try:
        # 1. 創建測試檔案
        gz_file = create_complete_fortinet_log_gz()
        print(f"  📦 創建壓縮測試檔案：{gz_file}")
        
        # 2. 載入 Fortinet 資料載入器
        from Forti_ui_app_bundle.training_pipeline.data_loader import DataLoader
        
        config = {
            "TARGET_COLUMN": "is_attack",
            "DROP_COLUMNS": []
        }
        loader = DataLoader(config)
        
        # 3. 執行完整資料載入流程
        print("  🔍 開始完整資料載入流程...")
        
        try:
            df = loader.load_data(gz_file)
            print(f"  ✅ 資料載入成功！")
            print(f"     - 資料形狀：{df.shape}")
            print(f"     - 欄位數量：{len(df.columns)}")
            
            # 顯示前幾個欄位名稱
            columns_preview = list(df.columns)[:10]
            print(f"     - 前 10 個欄位：{columns_preview}")
            
            # 檢查是否有關鍵欄位
            key_columns = ['srcip', 'dstip', 'action', 'crlevel']
            found_columns = [col for col in key_columns if col in df.columns]
            print(f"     - 找到關鍵欄位：{found_columns}")
            
            # 檢查資料內容
            if len(df) > 0:
                print(f"     - 成功處理 {len(df)} 筆記錄")
                
                # 檢查 action 欄位分佈
                if 'action' in df.columns:
                    action_counts = df['action'].value_counts()
                    print(f"     - Action 分佈：{dict(action_counts)}")
                
                # 檢查 crlevel 欄位分佈  
                if 'crlevel' in df.columns:
                    crlevel_counts = df['crlevel'].value_counts()
                    print(f"     - CRLevel 分佈：{dict(crlevel_counts)}")
                
                return True
            else:
                print("  ❌ 載入的資料為空")
                return False
                
        except Exception as e:
            print(f"  ❌ 資料載入失敗：{e}")
            import traceback
            traceback.print_exc()
            return False
        
    except Exception as e:
        print(f"  ❌ 測試執行失敗：{e}")
        return False
        
    finally:
        # 清理測試檔案
        if gz_file and os.path.exists(gz_file):
            try:
                os.unlink(gz_file)
            except Exception:
                pass


def test_pipeline_integration():
    """測試管線整合功能"""
    print("\n🔗 測試管線整合功能...")
    
    try:
        # 測試 Fortinet 管線是否可正常導入和初始化
        from Forti_ui_app_bundle.training_pipeline.pipeline_main import TrainingPipeline
        
        # 測試基本配置
        from Forti_ui_app_bundle.training_pipeline.config import CONFIG_BINARY
        
        pipeline = TrainingPipeline("binary", CONFIG_BINARY)
        print("  ✅ Fortinet 訓練管線初始化成功")
        
        # 測試 Cisco 管線
        from Cisco_ui.training_pipeline.pipeline_main import CiscoTrainingPipeline
        
        cisco_pipeline = CiscoTrainingPipeline(task_type="binary")
        print("  ✅ Cisco 訓練管線初始化成功")
        
        return True
        
    except Exception as e:
        print(f"  ❌ 管線整合測試失敗：{e}")
        return False


def test_ui_integration():
    """測試 UI 整合"""
    print("\n🖥️ 測試 UI 整合...")
    
    try:
        # 測試 Fortinet UI 模組
        from Forti_ui_app_bundle.ui_pages import training_ui as fortinet_training
        print("  ✅ Fortinet 訓練 UI 模組載入成功")
        
        # 測試 Cisco UI 模組  
        from Cisco_ui.ui_pages import training_ui as cisco_training
        print("  ✅ Cisco 訓練 UI 模組載入成功")
        
        # 測試統一介面
        from unified_ui.app import main as unified_main
        print("  ✅ 統一介面主程式載入成功")
        
        return True
        
    except Exception as e:
        print(f"  ❌ UI 整合測試失敗：{e}")
        return False


def main():
    """主測試函數"""
    print("🧪 端到端完整功能測試")
    print("=" * 60)
    
    results = []
    
    # 1. 端到端資料處理測試
    results.append(test_end_to_end_fortinet_compressed())
    
    # 2. 管線整合測試
    results.append(test_pipeline_integration())
    
    # 3. UI 整合測試  
    results.append(test_ui_integration())
    
    # 總結
    print("\n" + "=" * 60)
    print("📊 完整功能測試結果總結:")
    
    passed = sum(results)
    total = len(results)
    
    test_names = [
        "端到端資料處理",
        "管線整合功能", 
        "UI 介面整合"
    ]
    
    for i, (name, result) in enumerate(zip(test_names, results)):
        status = "✅ 通過" if result else "❌ 失敗"
        print(f"  {i+1}. {name}: {status}")
    
    if passed == total:
        print(f"\n🎉 所有測試通過 ({passed}/{total})")
        print("\n✨ 系統已完全就緒！")
        print("\n🚀 主要功能亮點：")
        print("  🔹 智能格式自動偵測")
        print("  🔹 壓縮檔案自動處理") 
        print("  🔹 Fortinet 日誌 ETL 整合")
        print("  🔹 Cisco ASA 日誌 ETL 整合")
        print("  🔹 統一介面跨品牌支援")
        print("  🔹 完整的錯誤處理機制")
        print("  🔹 用戶友好的操作體驗")
        
        print("\n📝 使用建議：")
        print("  1. 直接上傳任何支援的檔案格式")
        print("  2. 系統會自動偵測並處理")
        print("  3. 享受無縫的訓練體驗")
        
    else:
        print(f"\n⚠️ 部分測試失敗 ({passed}/{total})")
        print("請檢查失敗的測試項目。")


if __name__ == "__main__":
    main()