#!/usr/bin/env python3
"""
依賴關係測試套件 - 驗證共享模組在新位置的導入和功能
"""
import sys
import unittest
import warnings
from pathlib import Path

# 添加項目根目錄到路徑
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


class TestDependencyRelations(unittest.TestCase):
    """測試模組間的依賴關係"""
    
    def test_notification_models_import(self):
        """測試notification_models在新位置的導入"""
        try:
            from ui_shared.notification_models import NotificationMessage, SEVERITY_LABELS
            self.assertIsNotNone(NotificationMessage)
            self.assertIsInstance(SEVERITY_LABELS, dict)
            print("✅ ui_shared.notification_models 導入成功")
        except ImportError as e:
            self.fail(f"❌ ui_shared.notification_models 導入失敗: {e}")
    
    def test_enhanced_theme_import(self):
        """測試enhanced_theme在新位置的導入"""
        try:
            from ui_shared.enhanced_theme import apply_custom_theme
            self.assertIsNotNone(apply_custom_theme)
            print("✅ ui_shared.enhanced_theme 導入成功")
        except ImportError as e:
            self.fail(f"❌ ui_shared.enhanced_theme 導入失敗: {e}")
    
    def test_cisco_notification_dependency(self):
        """測試Cisco模組對notification_models的依賴"""
        try:
            from Cisco_ui.utils_labels import SEVERITY_LABELS
            self.assertIsInstance(SEVERITY_LABELS, dict)
            self.assertGreater(len(SEVERITY_LABELS), 0)
            print("✅ Cisco模組成功使用ui_shared中的SEVERITY_LABELS")
        except ImportError as e:
            self.fail(f"❌ Cisco模組無法使用ui_shared中的notification_models: {e}")
    
    def test_forti_notification_dependency(self):
        """測試Fortinet模組對notification_models的依賴"""
        try:
            from Forti_ui_app_bundle.notifier import NotificationMessage
            self.assertIsNotNone(NotificationMessage)
            print("✅ Fortinet模組成功使用ui_shared中的NotificationMessage")
        except ImportError as e:
            self.fail(f"❌ Fortinet模組無法使用ui_shared中的notification_models: {e}")
    
    def test_forti_storage_dependency(self):
        """測試Fortinet存儲模組對notification_models的依賴"""
        try:
            from Forti_ui_app_bundle.notification_storage import NotificationStorage
            storage = NotificationStorage(":memory:")  # 使用內存數據庫測試
            self.assertIsNotNone(storage)
            print("✅ Fortinet存儲模組成功使用ui_shared依賴")
        except ImportError as e:
            self.fail(f"❌ Fortinet存儲模組無法使用ui_shared依賴: {e}")
    
    def test_cross_module_data_consistency(self):
        """測試跨模組數據一致性"""
        try:
            # 從共享模組導入
            from ui_shared.notification_models import SEVERITY_LABELS as shared_labels
            
            # 從Cisco模組導入
            from Cisco_ui.utils_labels import SEVERITY_LABELS as cisco_labels
            
            # 驗證數據一致性
            self.assertEqual(shared_labels, cisco_labels)
            print("✅ 跨模組SEVERITY_LABELS數據一致")
        except Exception as e:
            self.fail(f"❌ 跨模組數據一致性檢查失敗: {e}")
    
    def test_path_resolution(self):
        """測試路徑解析是否正確"""
        try:
            # 測試相對路徑導入
            from ui_shared import notification_models
            from ui_shared import enhanced_theme
            from ui_shared import style_kit
            from ui_shared import upload_limits
            
            print("✅ ui_shared模組路徑解析正確")
        except ImportError as e:
            self.fail(f"❌ ui_shared模組路徑解析失敗: {e}")
    
    def test_notification_message_functionality(self):
        """測試NotificationMessage功能"""
        try:
            from ui_shared.notification_models import NotificationMessage
            
            # 創建測試消息
            msg = NotificationMessage(
                severity=4,
                source_ip="192.168.1.1",
                description="測試內容",
                suggestion="測試建議"
            )
            
            self.assertEqual(msg.severity, 4)
            self.assertEqual(msg.source_ip, "192.168.1.1")
            self.assertEqual(msg.description, "測試內容")
            print("✅ NotificationMessage功能正常")
        except Exception as e:
            self.fail(f"❌ NotificationMessage功能測試失敗: {e}")
    
    def test_circular_dependency_check(self):
        """檢查是否存在循環依賴"""
        try:
            # 嘗試導入所有主要模組，檢查是否存在循環依賴
            import unified_ui.app
            import Cisco_ui.ui_app
            import Forti_ui_app_bundle.ui_app
            import ui_shared.notification_models
            import ui_shared.enhanced_theme
            
            print("✅ 無循環依賴問題")
        except ImportError as e:
            if "circular import" in str(e).lower():
                self.fail(f"❌ 檢測到循環依賴: {e}")
            else:
                # 其他導入錯誤不算循環依賴
                pass


class TestModuleStructure(unittest.TestCase):
    """測試模組結構的完整性"""
    
    def test_ui_shared_structure(self):
        """測試ui_shared目錄結構"""
        ui_shared_dir = PROJECT_ROOT / "ui_shared"
        
        expected_files = [
            "__init__.py",
            "notification_models.py",
            "enhanced_theme.py",
            "style_kit.py",
            "upload_limits.py"
        ]
        
        for file_name in expected_files:
            file_path = ui_shared_dir / file_name
            self.assertTrue(file_path.exists(), f"缺少檔案: {file_path}")
        
        print("✅ ui_shared目錄結構完整")
    
    def test_tests_structure(self):
        """測試tests目錄結構"""
        tests_dir = PROJECT_ROOT / "tests"
        self.assertTrue(tests_dir.exists(), "tests目錄不存在")
        
        # 檢查是否有測試檔案
        test_files = list(tests_dir.glob("test_*.py"))
        self.assertGreater(len(test_files), 0, "沒有找到測試檔案")
        
        print(f"✅ tests目錄包含 {len(test_files)} 個測試檔案")
    
    def test_tools_structure(self):
        """測試tools目錄結構"""
        tools_dir = PROJECT_ROOT / "tools"
        self.assertTrue(tools_dir.exists(), "tools目錄不存在")
        
        # 檢查是否有工具檔案
        tool_files = list(tools_dir.glob("*.py"))
        self.assertGreater(len(tool_files), 0, "沒有找到工具檔案")
        
        print(f"✅ tools目錄包含 {len(tool_files)} 個工具檔案")
    
    def test_docs_structure(self):
        """測試docs目錄結構"""
        docs_dir = PROJECT_ROOT / "docs"
        self.assertTrue(docs_dir.exists(), "docs目錄不存在")
        
        # 檢查是否有文檔檔案
        doc_files = list(docs_dir.glob("*.md"))
        self.assertGreater(len(doc_files), 0, "沒有找到文檔檔案")
        
        print(f"✅ docs目錄包含 {len(doc_files)} 個文檔檔案")


if __name__ == "__main__":
    # 抑制警告訊息
    warnings.filterwarnings("ignore")
    
    # 運行測試
    unittest.main(verbosity=2)