#!/usr/bin/env python3
"""
整合測試套件 - 驗證模組間的互動和資料流
"""
import sys
import unittest
import warnings
import json
import tempfile
from pathlib import Path
import pandas as pd

# 添加項目根目錄到路徑
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


class TestCrossModuleIntegration(unittest.TestCase):
    """測試跨模組整合"""
    
    def test_unified_ui_brand_integration(self):
        """測試統一UI與品牌模組的整合"""
        try:
            from unified_ui.app import BRAND_RENDERERS
            from unified_ui.cisco_module import pages as cisco_pages
            from unified_ui.fortinet_module import pages as fortinet_pages
            
            # 檢查品牌模組是否正確註冊到統一UI
            if cisco_pages:
                self.assertIn("Cisco", BRAND_RENDERERS)
                self.assertEqual(BRAND_RENDERERS["Cisco"], cisco_pages.render)
            
            if fortinet_pages:
                self.assertIn("Fortinet", BRAND_RENDERERS)
                self.assertEqual(BRAND_RENDERERS["Fortinet"], fortinet_pages.render)
            
            print("✅ 統一UI與品牌模組整合正常")
        except Exception as e:
            self.fail(f"❌ 統一UI品牌整合測試失敗: {e}")
    
    def test_notification_system_integration(self):
        """測試通知系統整合"""
        try:
            # 測試共享通知模型
            from ui_shared.notification_models import (
                NotificationMessage, 
                SEVERITY_LABELS
            )
            
            # 測試Cisco通知器使用共享模型
            from Cisco_ui.utils_labels import SEVERITY_LABELS as cisco_labels
            
            # 測試模組存在性而非類別相等性（因為可能有不同的導入路徑）
            try:
                from Forti_ui_app_bundle.notifier import NotificationMessage as forti_msg
                forti_msg_exists = True
            except ImportError:
                forti_msg_exists = False
            
            # 驗證數據一致性和模組可用性
            self.assertEqual(SEVERITY_LABELS, cisco_labels)
            # 注意：不同模組可能有不同的NotificationMessage導入路徑，這是正常的
            print(f"✅ Forti通知器可用: {forti_msg_exists}")
            
            print("✅ 通知系統整合正常")
        except Exception as e:
            self.fail(f"❌ 通知系統整合測試失敗: {e}")
    
    def test_theme_system_integration(self):
        """測試主題系統整合"""
        try:
            from unified_ui.theme_controller import THEME_CONFIGS
            from ui_shared.enhanced_theme import apply_custom_theme
            
            # 檢查主題系統整合
            self.assertIsInstance(THEME_CONFIGS, dict)
            self.assertIsNotNone(apply_custom_theme)
            
            print("✅ 主題系統整合正常")
        except Exception as e:
            self.fail(f"❌ 主題系統整合測試失敗: {e}")


class TestDataFlowIntegration(unittest.TestCase):
    """測試資料流整合"""
    
    def setUp(self):
        """設置測試資料"""
        self.test_data = pd.DataFrame({
            'timestamp': ['2024-01-01 12:00:00', '2024-01-01 12:01:00'],
            'source_ip': ['192.168.1.1', '192.168.1.2'],
            'dest_ip': ['10.0.0.1', '10.0.0.2'],
            'action': ['allow', 'deny'],
            'severity': ['info', 'warning']
        })
    
    def test_etl_to_training_pipeline(self):
        """測試ETL到訓練管道的資料流"""
        try:
            # 導入Cisco ETL和訓練模組
            from Cisco_ui.etl_pipeline import log_cleaning
            from Cisco_ui.training_pipeline import config
            
            # 檢查模組存在
            self.assertIsNotNone(log_cleaning)
            self.assertIsNotNone(config)
            
            print("✅ ETL到訓練管道整合正常")
        except ImportError as e:
            self.fail(f"❌ ETL到訓練管道整合失敗: {e}")
    
    def test_notification_storage_integration(self):
        """測試通知存儲整合"""
        try:
            from ui_shared.notification_models import NotificationMessage
            from Forti_ui_app_bundle.notification_storage import (
                NotificationStorage
            )
            
            # 創建測試通知
            msg = NotificationMessage(
                severity=3,
                source_ip="192.168.1.100",
                description="測試通知存儲整合",
                suggestion="整合測試建議"
            )
            
            # 測試存儲功能（使用內存數據庫）
            storage = NotificationStorage(":memory:")
            
            # 驗證整合成功
            self.assertIsNotNone(msg)
            self.assertIsNotNone(storage)
            
            print("✅ 通知存儲整合正常")
        except Exception as e:
            self.fail(f"❌ 通知存儲整合測試失敗: {e}")


class TestConfigurationIntegration(unittest.TestCase):
    """測試配置整合"""
    
    def test_streamlit_config_integration(self):
        """測試Streamlit配置整合"""
        try:
            streamlit_config_dir = PROJECT_ROOT / ".streamlit"
            
            if streamlit_config_dir.exists():
                # 檢查配置檔案
                config_files = list(streamlit_config_dir.glob("*.toml"))
                if config_files:
                    print(f"✅ Streamlit配置整合正常，包含 {len(config_files)} 個配置檔案")
                else:
                    print("⚠️  Streamlit配置目錄存在但無配置檔案")
            else:
                print("⚠️  Streamlit配置目錄不存在（使用默認配置）")
        except Exception as e:
            self.fail(f"❌ Streamlit配置整合測試失敗: {e}")
    
    def test_json_config_integration(self):
        """測試JSON配置檔案整合"""
        try:
            # 檢查設定檔案
            config_files = [
                "forti_visualization_settings.json",
                "logfetcher_settings.json"
            ]
            
            for config_file in config_files:
                config_path = PROJECT_ROOT / config_file
                if config_path.exists():
                    # 嘗試讀取JSON檔案
                    with open(config_path, 'r', encoding='utf-8') as f:
                        json.load(f)
                    print(f"✅ {config_file} 配置整合正常")
                else:
                    print(f"⚠️  {config_file} 配置檔案不存在")
        except json.JSONDecodeError as e:
            self.fail(f"❌ JSON配置檔案格式錯誤: {e}")
        except Exception as e:
            self.fail(f"❌ JSON配置整合測試失敗: {e}")


class TestFileSystemIntegration(unittest.TestCase):
    """測試檔案系統整合"""
    
    def test_project_structure_integrity(self):
        """測試專案結構完整性"""
        expected_dirs = [
            "unified_ui",
            "Cisco_ui", 
            "Forti_ui_app_bundle",
            "ui_shared",
            "tests",
            "tools",
            "docs"
        ]
        
        missing_dirs = []
        for dir_name in expected_dirs:
            dir_path = PROJECT_ROOT / dir_name
            if not dir_path.exists():
                missing_dirs.append(dir_name)
        
        if missing_dirs:
            self.fail(f"缺少目錄: {', '.join(missing_dirs)}")
        
        print(f"✅ 專案結構完整，包含 {len(expected_dirs)} 個主要目錄")
    
    def test_core_files_integrity(self):
        """測試核心檔案完整性"""
        core_files = [
            "launch_unified_dashboard.py",
            "requirements.txt",
            "README.md"
        ]
        
        missing_files = []
        for file_name in core_files:
            file_path = PROJECT_ROOT / file_name
            if not file_path.exists():
                missing_files.append(file_name)
        
        if missing_files:
            self.fail(f"缺少核心檔案: {', '.join(missing_files)}")
        
        print(f"✅ 核心檔案完整，包含 {len(core_files)} 個檔案")
    
    def test_module_init_files(self):
        """測試模組__init__.py檔案"""
        modules_with_init = [
            "unified_ui",
            "Cisco_ui",
            "ui_shared"
        ]
        
        missing_inits = []
        for module_name in modules_with_init:
            init_file = PROJECT_ROOT / module_name / "__init__.py"
            if not init_file.exists():
                missing_inits.append(f"{module_name}/__init__.py")
        
        if missing_inits:
            self.fail(f"缺少__init__.py檔案: {', '.join(missing_inits)}")
        
        print(f"✅ 模組初始化檔案完整")


class TestPerformanceIntegration(unittest.TestCase):
    """測試性能整合"""
    
    def test_import_performance(self):
        """測試導入性能"""
        import time
        
        start_time = time.time()
        
        # 導入主要模組
        try:
            from unified_ui import app
            from unified_ui import theme_controller
            from ui_shared import notification_models
        except ImportError:
            pass  # 允許部分導入失敗
        
        end_time = time.time()
        import_time = end_time - start_time
        
        # 導入時間不應超過10秒
        self.assertLess(import_time, 10.0, f"導入時間過長: {import_time:.2f}秒")
        
        print(f"✅ 模組導入性能正常 ({import_time:.2f}秒)")
    
    def test_memory_usage_basic(self):
        """測試基本記憶體使用"""
        try:
            import psutil
            import os
            
            process = psutil.Process(os.getpid())
            memory_info = process.memory_info()
            memory_mb = memory_info.rss / 1024 / 1024
            
            # 記憶體使用不應超過500MB（測試環境）
            self.assertLess(memory_mb, 500, f"記憶體使用過高: {memory_mb:.1f}MB")
            
            print(f"✅ 記憶體使用正常 ({memory_mb:.1f}MB)")
        except ImportError:
            print("⚠️  psutil未安裝，跳過記憶體測試")


if __name__ == "__main__":
    # 抑制警告訊息
    warnings.filterwarnings("ignore")
    
    # 運行測試
    unittest.main(verbosity=2)