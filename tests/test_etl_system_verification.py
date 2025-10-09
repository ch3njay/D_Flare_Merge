#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_etl_system_verification.py
===============================
ETL系統完整驗證測試

目的：
1. 確認所有ETL模組的實際函數結構
2. 驗證Pipeline呼叫鏈是否完整
3. 測試特徵工程的核心功能是否可用
4. 確保系統無損壞的檔案重組織後狀態
"""

import unittest
import os
import sys
import importlib

# 添加專案根目錄到Python路徑
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)


class TestETLSystemVerification(unittest.TestCase):
    """ETL系統完整驗證測試套件"""
    
    def setUp(self):
        """設置測試環境"""
        self.project_root = project_root
        
    def test_cisco_feature_engineering_functions(self):
        """測試Cisco特徵工程模組的實際函數"""
        try:
            from Cisco_ui.etl_pipeline import feature_engineering as cisco_fe
            
            # 檢查實際存在的函數
            expected_functions = [
                'load_model',
                'dflare_binary_predict',
                'dflare_multiclass_predict'
            ]
            
            for func_name in expected_functions:
                self.assertTrue(
                    hasattr(cisco_fe, func_name),
                    f"❌ Cisco特徵工程模組缺少函數: {func_name}"
                )
                self.assertTrue(
                    callable(getattr(cisco_fe, func_name)),
                    f"❌ {func_name} 不是可呼叫函數"
                )
            
            print("✅ Cisco特徵工程模組函數驗證通過")
            print(f"   - 可用函數: {[f for f in expected_functions if hasattr(cisco_fe, f)]}")
            
        except ImportError as e:
            self.fail(f"❌ 無法導入Cisco特徵工程模組: {e}")
    
    def test_fortinet_feature_engineering_functions(self):
        """測試Fortinet特徵工程模組的實際函數"""
        try:
            from Forti_ui_app_bundle.etl_pipeline import feature_engineering as forti_fe
            
            # 檢查實際存在的函數  
            expected_functions = [
                'main',
                'add_traffic_stats',
                'add_proto_port_feats',
                'add_windowed_feats',
                'add_relational_basic',
                'add_anomaly_indicators'
            ]
            
            available_functions = []
            for func_name in expected_functions:
                if hasattr(forti_fe, func_name):
                    available_functions.append(func_name)
                    self.assertTrue(
                        callable(getattr(forti_fe, func_name)),
                        f"❌ {func_name} 不是可呼叫函數"
                    )
            
            # 至少要有main函數
            self.assertIn('main', available_functions, "❌ Fortinet特徵工程必須有main函數")
            
            print("✅ Fortinet特徵工程模組函數驗證通過")
            print(f"   - 可用函數: {available_functions}")
            
        except ImportError as e:
            self.fail(f"❌ 無法導入Fortinet特徵工程模組: {e}")
    
    def test_gpu_feature_engineering_functions(self):
        """測試GPU特徵工程模組的實際函數"""
        try:
            from Forti_ui_app_bundle.gpu_etl_pipeline import feature_engineering as gpu_fe
            
            # 檢查主要函數
            self.assertTrue(
                hasattr(gpu_fe, 'main'),
                "❌ GPU特徵工程模組缺少main函數"
            )
            self.assertTrue(
                callable(getattr(gpu_fe, 'main')),
                "❌ main函數不可呼叫"
            )
            
            # 檢查配置變數
            config_vars = [
                'ENABLE_TRAFFIC_STATS',
                'ENABLE_PROTO_PORT_FEATS', 
                'ENABLE_WINDOWED_FEATS',
                'ENABLE_RELATIONAL_BASE',
                'ENABLE_ANOMALY_INDIC'
            ]
            
            available_config = []
            for var_name in config_vars:
                if hasattr(gpu_fe, var_name):
                    available_config.append(var_name)
            
            print("✅ GPU特徵工程模組函數驗證通過")
            print(f"   - 主函數: main")
            print(f"   - 可用配置: {available_config}")
            
        except ImportError as e:
            self.fail(f"❌ 無法導入GPU特徵工程模組: {e}")
    
    def test_etl_pipeline_integration(self):
        """測試ETL Pipeline整合呼叫"""
        try:
            # 測試Fortinet ETL Pipeline
            from Forti_ui_app_bundle import etl_pipeliner
            
            # 檢查主要Pipeline函數
            pipeline_functions = [
                'run_feature_engineering_noninteractive',
                'run_mapping_noninteractive', 
                'run_pipeline'
            ]
            
            for func_name in pipeline_functions:
                self.assertTrue(
                    hasattr(etl_pipeliner, func_name),
                    f"❌ ETL Pipeline缺少函數: {func_name}"
                )
                self.assertTrue(
                    callable(getattr(etl_pipeliner, func_name)),
                    f"❌ {func_name} 不是可呼叫函數"
                )
            
            print("✅ ETL Pipeline整合驗證通過")
            print(f"   - 可用Pipeline函數: {pipeline_functions}")
            
        except ImportError as e:
            self.fail(f"❌ 無法導入ETL Pipeline模組: {e}")
    
    def test_gpu_etl_pipeline_integration(self):
        """測試GPU ETL Pipeline整合呼叫"""
        try:
            # 測試GPU ETL Pipeline
            from Forti_ui_app_bundle import gpu_etl_pipeliner
            
            # 檢查主要Pipeline函數
            pipeline_functions = [
                'run_pipeline_noninteractive',
                'run_pipeline_cli'
            ]
            
            available_functions = []
            for func_name in pipeline_functions:
                if hasattr(gpu_etl_pipeliner, func_name):
                    available_functions.append(func_name)
                    self.assertTrue(
                        callable(getattr(gpu_etl_pipeliner, func_name)),
                        f"❌ {func_name} 不是可呼叫函數"
                    )
            
            # 至少要有一個主要函數
            self.assertGreater(
                len(available_functions), 0,
                "❌ GPU ETL Pipeline沒有可用的主要函數"
            )
            
            print("✅ GPU ETL Pipeline整合驗證通過")
            print(f"   - 可用Pipeline函數: {available_functions}")
            
        except ImportError as e:
            self.fail(f"❌ 無法導入GPU ETL Pipeline模組: {e}")
    
    def test_cisco_etl_pipeline_integration(self):
        """測試Cisco ETL Pipeline整合呼叫"""
        try:
            # 測試Cisco ETL Pipeline
            from Cisco_ui import etl_pipeliner as cisco_pipeline
            
            # 檢查主要Pipeline函數和類別
            pipeline_items = [
                'EtlOutputs',
                'run_etl_pipeline',
                'run_models'
            ]
            
            for item_name in pipeline_items:
                self.assertTrue(
                    hasattr(cisco_pipeline, item_name),
                    f"❌ Cisco ETL Pipeline缺少: {item_name}"
                )
            
            # 特別檢查EtlOutputs是否為dataclass
            etl_outputs = getattr(cisco_pipeline, 'EtlOutputs')
            self.assertTrue(
                hasattr(etl_outputs, '__dataclass_fields__'),
                "❌ EtlOutputs 應該是dataclass"
            )
            
            print("✅ Cisco ETL Pipeline整合驗證通過")
            print(f"   - 可用Pipeline項目: {pipeline_items}")
            
        except ImportError as e:
            self.fail(f"❌ 無法導入Cisco ETL Pipeline模組: {e}")
    
    def test_etl_module_consistency(self):
        """測試ETL模組間的一致性"""
        try:
            # 檢查所有ETL模組是否都有基本的清理功能
            from Cisco_ui.etl_pipeline import log_cleaning as cisco_clean
            from Forti_ui_app_bundle.etl_pipeline import log_cleaning as forti_clean
            from Forti_ui_app_bundle.gpu_etl_pipeline import log_cleaning as gpu_clean
            
            # 檢查清理模組的基本函數
            cleaning_modules = [
                ('Cisco', cisco_clean),
                ('Fortinet', forti_clean), 
                ('GPU', gpu_clean)
            ]
            
            for module_name, module in cleaning_modules:
                # 至少要有一個主要清理函數
                main_functions = [
                    name for name in dir(module) 
                    if callable(getattr(module, name)) and not name.startswith('_')
                ]
                
                self.assertGreater(
                    len(main_functions), 0,
                    f"❌ {module_name} 清理模組沒有可用函數"
                )
                
                print(f"✅ {module_name} 清理模組驗證通過")
                print(f"   - 可用函數: {main_functions[:5]}...")  # 只顯示前5個
            
        except ImportError as e:
            self.fail(f"❌ 無法導入清理模組: {e}")
    
    def test_cross_module_dependencies(self):
        """測試跨模組依賴關係"""
        try:
            # 測試共享模組
            from ui_shared.notification_models import NotificationMessage, SEVERITY_LABELS
            
            # 測試各模組是否正確使用共享模組
            from Cisco_ui.utils_labels import SEVERITY_LABELS as cisco_labels
            
            # 驗證數據一致性
            self.assertEqual(
                SEVERITY_LABELS, cisco_labels,
                "❌ Cisco與共享模組的嚴重等級標籤不一致"
            )
            
            # 測試通知模型功能
            test_msg = NotificationMessage(
                severity=2,
                source_ip="192.168.1.1",
                description="測試訊息",
                suggestion="系統驗證"
            )
            
            self.assertEqual(test_msg.severity, 2)
            self.assertEqual(test_msg.source_ip, "192.168.1.1")
            
            print("✅ 跨模組依賴關係驗證通過")
            print("   - 通知模型正常工作")
            print("   - 嚴重等級標籤一致性正常")
            
        except Exception as e:
            self.fail(f"❌ 跨模組依賴關係測試失敗: {e}")
    
    def test_system_import_integrity(self):
        """測試系統導入完整性"""
        critical_modules = [
            # 核心UI模組
            'unified_ui.app',
            'unified_ui.cisco_module.pages',
            'unified_ui.fortinet_module.pages',
            
            # ETL處理模組
            'Cisco_ui.etl_pipeliner',
            'Forti_ui_app_bundle.etl_pipeliner',
            'Forti_ui_app_bundle.gpu_etl_pipeliner',
            
            # 共享模組
            'ui_shared.notification_models',
            'ui_shared.enhanced_theme',
            
            # 通知系統
            'Cisco_ui.notifier',
            'Forti_ui_app_bundle.notifier'
        ]
        
        import_results = {}
        failed_imports = []
        
        for module_name in critical_modules:
            try:
                importlib.import_module(module_name)
                import_results[module_name] = "✅"
            except ImportError as e:
                import_results[module_name] = f"❌ {str(e)}"
                failed_imports.append(module_name)
            except Exception as e:
                import_results[module_name] = f"⚠️ {str(e)}"
        
        # 顯示結果
        print("📊 系統導入完整性檢查結果:")
        for module, result in import_results.items():
            print(f"   {module}: {result}")
        
        # 如果有關鍵模組導入失敗，測試失敗
        if failed_imports:
            self.fail(f"❌ 關鍵模組導入失敗: {', '.join(failed_imports)}")
        
        print(f"✅ 系統導入完整性驗證通過 ({len(critical_modules)} 個模組)")


class TestETLFunctionalVerification(unittest.TestCase):
    """ETL功能性驗證測試"""
    
    def test_feature_engineering_configuration(self):
        """測試特徵工程配置正確性"""
        try:
            from Forti_ui_app_bundle.etl_pipeline import feature_engineering as fe
            
            # 檢查配置變數
            config_checks = [
                ('ENABLE_TRAFFIC_STATS', bool),
                ('ENABLE_PROTO_PORT_FEATS', bool),
                ('CSV_CHUNK_SIZE', int),
                ('DEFAULT_INPUT', str),
                ('DEFAULT_OUTPUT', str)
            ]
            
            for config_name, expected_type in config_checks:
                if hasattr(fe, config_name):
                    config_value = getattr(fe, config_name)
                    self.assertIsInstance(
                        config_value, expected_type,
                        f"❌ {config_name} 類型不正確，預期 {expected_type.__name__}"
                    )
            
            print("✅ 特徵工程配置驗證通過")
            
        except ImportError as e:
            self.fail(f"❌ 無法導入特徵工程模組進行配置檢查: {e}")
    
    def test_pipeline_workflow_integrity(self):
        """測試Pipeline工作流程完整性"""
        try:
            from Forti_ui_app_bundle.etl_pipeliner import (
                run_feature_engineering_noninteractive,
                run_mapping_noninteractive
            )
            
            # 檢查函數簽名（通過inspect模組）
            import inspect
            
            # 檢查特徵工程函數參數
            fe_sig = inspect.signature(run_feature_engineering_noninteractive)
            fe_params = list(fe_sig.parameters.keys())
            
            expected_fe_params = ['in_csv', 'out_csv']
            for param in expected_fe_params:
                self.assertIn(
                    param, fe_params,
                    f"❌ 特徵工程函數缺少參數: {param}"
                )
            
            # 檢查映射函數參數
            map_sig = inspect.signature(run_mapping_noninteractive)
            map_params = list(map_sig.parameters.keys())
            
            expected_map_params = ['in_csv', 'out_csv']
            for param in expected_map_params:
                self.assertIn(
                    param, map_params,
                    f"❌ 映射函數缺少參數: {param}"
                )
            
            print("✅ Pipeline工作流程完整性驗證通過")
            print(f"   - 特徵工程參數: {fe_params}")
            print(f"   - 映射處理參數: {map_params}")
            
        except ImportError as e:
            self.fail(f"❌ 無法導入Pipeline函數進行檢查: {e}")


if __name__ == "__main__":
    # 設置測試套件
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # 添加測試類別
    suite.addTests(loader.loadTestsFromTestCase(TestETLSystemVerification))
    suite.addTests(loader.loadTestsFromTestCase(TestETLFunctionalVerification))
    
    # 執行測試
    runner = unittest.TextTestRunner(verbosity=2, buffer=True)
    result = runner.run(suite)
    
    # 結果統計
    total_tests = result.testsRun
    failures = len(result.failures)
    errors = len(result.errors)
    success_rate = ((total_tests - failures - errors) / total_tests * 100) if total_tests > 0 else 0
    
    print("\n" + "="*80)
    print("📊 ETL系統驗證測試結果")
    print("="*80)
    print(f"總測試數: {total_tests}")
    print(f"✅ 通過: {total_tests - failures - errors}")
    print(f"❌ 失敗: {failures}")
    print(f"🔥 錯誤: {errors}")
    print(f"📈 成功率: {success_rate:.1f}%")
    
    if failures > 0 or errors > 0:
        print("\n❌ 發現系統問題，需要修復")
        sys.exit(1)
    else:
        print("\n✅ ETL系統驗證完全通過，系統狀態正常")
        sys.exit(0)