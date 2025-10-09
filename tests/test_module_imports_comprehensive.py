#!/usr/bin/env python3
"""
全面模組導入測試套件 - 驗證檔案調動後所有模組的導入狀況
"""
import sys
import unittest
import warnings
from pathlib import Path
from typing import Any, Dict, List

# 添加項目根目錄到路徑
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


class TestModuleImports(unittest.TestCase):
    """測試所有核心模組的導入功能"""
    
    def setUp(self):
        """設置測試環境"""
        self.import_results = {}
        self.import_errors = {}
        
    def test_unified_ui_modules(self):
        """測試統一UI相關模組"""
        modules_to_test = [
            "unified_ui.app",
            "unified_ui.theme_controller",
            "unified_ui.cisco_module.pages",
            "unified_ui.fortinet_module.pages",
        ]
        
        for module_name in modules_to_test:
            with self.subTest(module=module_name):
                try:
                    __import__(module_name)
                    self.import_results[module_name] = "SUCCESS"
                except Exception as e:
                    self.import_results[module_name] = "FAILED"
                    self.import_errors[module_name] = str(e)
                    self.fail(f"Failed to import {module_name}: {e}")
    
    def test_cisco_ui_modules(self):
        """測試Cisco UI相關模組"""
        modules_to_test = [
            "Cisco_ui.ui_app",
            "Cisco_ui.etl_pipeliner",
            "Cisco_ui.notifier",
            "Cisco_ui.utils_labels",
        ]
        
        for module_name in modules_to_test:
            with self.subTest(module=module_name):
                try:
                    __import__(module_name)
                    self.import_results[module_name] = "SUCCESS"
                except Exception as e:
                    self.import_results[module_name] = "FAILED"
                    self.import_errors[module_name] = str(e)
                    self.fail(f"Failed to import {module_name}: {e}")
    
    def test_cisco_ui_pages(self):
        """測試Cisco UI頁面模組"""
        modules_to_test = [
            "Cisco_ui.ui_pages.data_cleaning",
            "Cisco_ui.ui_pages.log_monitor",
            "Cisco_ui.ui_pages.model_inference",
            "Cisco_ui.ui_pages.notifications",
            "Cisco_ui.ui_pages.visualization",
        ]
        
        for module_name in modules_to_test:
            with self.subTest(module=module_name):
                try:
                    __import__(module_name)
                    self.import_results[module_name] = "SUCCESS"
                except Exception as e:
                    self.import_results[module_name] = "FAILED"
                    self.import_errors[module_name] = str(e)
                    self.fail(f"Failed to import {module_name}: {e}")
    
    def test_forti_ui_modules(self):
        """測試Fortinet UI相關模組"""
        modules_to_test = [
            "Forti_ui_app_bundle.ui_app",
            "Forti_ui_app_bundle.etl_pipeliner",
            "Forti_ui_app_bundle.gpu_etl_pipeliner",
            "Forti_ui_app_bundle.notifier",
            "Forti_ui_app_bundle.utils_labels",
        ]
        
        for module_name in modules_to_test:
            with self.subTest(module=module_name):
                try:
                    __import__(module_name)
                    self.import_results[module_name] = "SUCCESS"
                except Exception as e:
                    self.import_results[module_name] = "FAILED"
                    self.import_errors[module_name] = str(e)
                    self.fail(f"Failed to import {module_name}: {e}")
    
    def test_forti_ui_pages(self):
        """測試Fortinet UI頁面模組"""
        modules_to_test = [
            "Forti_ui_app_bundle.ui_pages.gpu_etl_ui",
            "Forti_ui_app_bundle.ui_pages.inference_ui",
            "Forti_ui_app_bundle.ui_pages.notifier_app",
            "Forti_ui_app_bundle.ui_pages.training_ui",
            "Forti_ui_app_bundle.ui_pages.visualization_ui",
        ]
        
        for module_name in modules_to_test:
            with self.subTest(module=module_name):
                try:
                    __import__(module_name)
                    self.import_results[module_name] = "SUCCESS"
                except Exception as e:
                    self.import_results[module_name] = "FAILED"
                    self.import_errors[module_name] = str(e)
                    self.fail(f"Failed to import {module_name}: {e}")
    
    def test_shared_modules(self):
        """測試共享模組"""
        modules_to_test = [
            "ui_shared.notification_models",
            "ui_shared.enhanced_theme",
            "ui_shared.style_kit",
            "ui_shared.upload_limits",
        ]
        
        for module_name in modules_to_test:
            with self.subTest(module=module_name):
                try:
                    __import__(module_name)
                    self.import_results[module_name] = "SUCCESS"
                except Exception as e:
                    self.import_results[module_name] = "FAILED"
                    self.import_errors[module_name] = str(e)
                    self.fail(f"Failed to import {module_name}: {e}")
    
    def test_etl_pipeline_modules(self):
        """測試ETL管道模組"""
        etl_modules = [
            "Cisco_ui.etl_pipeline.log_cleaning",
            "Cisco_ui.etl_pipeline.log_mapping",
            "Cisco_ui.etl_pipeline.feature_engineering",
            "Cisco_ui.etl_pipeline.utils",
            "Forti_ui_app_bundle.etl_pipeline.log_cleaning",
            "Forti_ui_app_bundle.etl_pipeline.log_mapping",
            "Forti_ui_app_bundle.etl_pipeline.feature_engineering",
            "Forti_ui_app_bundle.etl_pipeline.utils",
        ]
        
        for module_name in etl_modules:
            with self.subTest(module=module_name):
                try:
                    __import__(module_name)
                    self.import_results[module_name] = "SUCCESS"
                except Exception as e:
                    self.import_results[module_name] = "FAILED"
                    self.import_errors[module_name] = str(e)
                    self.fail(f"Failed to import {module_name}: {e}")
    
    def test_training_pipeline_modules(self):
        """測試訓練管道模組"""
        training_modules = [
            "Cisco_ui.training_pipeline.model_builder",
            "Cisco_ui.training_pipeline.trainer",
            "Cisco_ui.training_pipeline.evaluator",
            "Cisco_ui.training_pipeline.config",
            "Forti_ui_app_bundle.training_pipeline.model_builder",
            "Forti_ui_app_bundle.training_pipeline.trainer",
            "Forti_ui_app_bundle.training_pipeline.evaluator",
            "Forti_ui_app_bundle.training_pipeline.config",
        ]
        
        for module_name in training_modules:
            with self.subTest(module=module_name):
                try:
                    __import__(module_name)
                    self.import_results[module_name] = "SUCCESS"
                except Exception as e:
                    self.import_results[module_name] = "FAILED"
                    self.import_errors[module_name] = str(e)
                    self.fail(f"Failed to import {module_name}: {e}")
    
    def tearDown(self):
        """輸出測試結果摘要"""
        if hasattr(self, '_testMethodName') and self._testMethodName == 'test_training_pipeline_modules':
            print("\n" + "="*80)
            print("模組導入測試結果摘要")
            print("="*80)
            
            success_count = sum(1 for result in self.import_results.values() if result == "SUCCESS")
            total_count = len(self.import_results)
            
            print(f"總計模組數: {total_count}")
            print(f"成功導入: {success_count}")
            print(f"導入失敗: {total_count - success_count}")
            print(f"成功率: {success_count/total_count*100:.1f}%")
            
            if self.import_errors:
                print("\n導入錯誤詳情:")
                for module, error in self.import_errors.items():
                    print(f"  ❌ {module}: {error}")


if __name__ == "__main__":
    # 抑制警告訊息以保持輸出清潔
    warnings.filterwarnings("ignore")
    
    unittest.main(verbosity=2)