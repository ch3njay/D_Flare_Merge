#!/usr/bin/env python3
"""
啟動流程測試套件 - 驗證所有啟動腳本和模組的啟動流程
"""
import sys
import unittest
import warnings
import subprocess
import tempfile
from pathlib import Path
import importlib.util

# 添加項目根目錄到路徑
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


class TestLaunchFlowIntegrity(unittest.TestCase):
    """測試啟動流程完整性"""
    
    def test_launch_unified_dashboard_import(self):
        """測試統一儀表板啟動腳本導入"""
        try:
            launch_script = PROJECT_ROOT / "launch_unified_dashboard.py"
            self.assertTrue(launch_script.exists(), "啟動腳本不存在")
            
            # 使用importlib動態導入以避免直接執行
            spec = importlib.util.spec_from_file_location(
                "launch_unified_dashboard", 
                launch_script
            )
            module = importlib.util.module_from_spec(spec)
            
            # 這裡只測試能否載入，不執行main函數
            self.assertIsNotNone(spec)
            self.assertIsNotNone(module)
            
            print("✅ launch_unified_dashboard.py 可以正常載入")
        except Exception as e:
            self.fail(f"❌ 啟動腳本載入失敗: {e}")
    
    def test_unified_ui_app_startup(self):
        """測試統一UI應用啟動"""
        try:
            from unified_ui.app import main, BRAND_RENDERERS
            
            # 檢查main函數存在
            self.assertIsNotNone(main)
            
            # 檢查是否有可用的品牌渲染器
            self.assertIsInstance(BRAND_RENDERERS, dict)
            
            if len(BRAND_RENDERERS) == 0:
                self.fail("沒有可用的品牌渲染器，無法啟動應用")
            
            print(f"✅ 統一UI應用啟動準備就緒，包含 {len(BRAND_RENDERERS)} 個品牌")
        except Exception as e:
            self.fail(f"❌ 統一UI應用啟動測試失敗: {e}")
    
    def test_cisco_ui_app_startup(self):
        """測試Cisco UI應用啟動"""
        try:
            import Cisco_ui.ui_app as cisco_app
            
            # 檢查Cisco UI應用模組導入
            self.assertIsNotNone(cisco_app)
            
            print("✅ Cisco UI應用啟動準備就緒")
        except Exception as e:
            self.fail(f"❌ Cisco UI應用啟動測試失敗: {e}")
    
    def test_forti_ui_app_startup(self):
        """測試Fortinet UI應用啟動"""
        try:
            import Forti_ui_app_bundle.ui_app as forti_app
            
            # 檢查Fortinet UI應用模組導入
            self.assertIsNotNone(forti_app)
            
            print("✅ Fortinet UI應用啟動準備就緒")
        except Exception as e:
            self.fail(f"❌ Fortinet UI應用啟動測試失敗: {e}")
    
    def test_brand_module_registration(self):
        """測試品牌模組註冊"""
        try:
            from unified_ui.app import BRAND_RENDERERS
            
            available_brands = list(BRAND_RENDERERS.keys())
            
            # 檢查至少有一個品牌註冊
            self.assertGreater(len(available_brands), 0, "沒有品牌註冊")
            
            # 檢查每個註冊的品牌都有對應的渲染函數
            for brand, renderer in BRAND_RENDERERS.items():
                self.assertIsNotNone(renderer, f"{brand} 品牌渲染器為空")
                self.assertTrue(callable(renderer), f"{brand} 品牌渲染器不可調用")
            
            print(f"✅ 品牌模組註冊正常，註冊品牌: {', '.join(available_brands)}")
        except Exception as e:
            self.fail(f"❌ 品牌模組註冊測試失敗: {e}")
    
    def test_theme_controller_startup(self):
        """測試主題控制器啟動"""
        try:
            from unified_ui.theme_controller import THEME_CONFIGS
            
            # 檢查主題配置存在
            self.assertIsInstance(THEME_CONFIGS, dict)
            self.assertGreater(len(THEME_CONFIGS), 0, "沒有主題配置")
            
            # 檢查每個主題配置的完整性
            for theme_name, config in THEME_CONFIGS.items():
                self.assertIsInstance(config, dict, f"{theme_name} 主題配置不是字典")
                self.assertIn("base", config, f"{theme_name} 主題缺少base配置")
            
            print(f"✅ 主題控制器啟動正常，包含 {len(THEME_CONFIGS)} 個主題")
        except Exception as e:
            self.fail(f"❌ 主題控制器啟動測試失敗: {e}")


class TestModuleInitialization(unittest.TestCase):
    """測試模組初始化"""
    
    def test_ui_shared_initialization(self):
        """測試ui_shared模組初始化"""
        try:
            import ui_shared
            
            # 檢查__init__.py是否存在
            init_file = PROJECT_ROOT / "ui_shared" / "__init__.py"
            self.assertTrue(init_file.exists(), "ui_shared/__init__.py 不存在")
            
            print("✅ ui_shared模組初始化正常")
        except Exception as e:
            self.fail(f"❌ ui_shared模組初始化失敗: {e}")
    
    def test_unified_ui_initialization(self):
        """測試unified_ui模組初始化"""
        try:
            import unified_ui
            
            # 檢查__init__.py是否存在
            init_file = PROJECT_ROOT / "unified_ui" / "__init__.py"
            self.assertTrue(init_file.exists(), "unified_ui/__init__.py 不存在")
            
            print("✅ unified_ui模組初始化正常")
        except Exception as e:
            self.fail(f"❌ unified_ui模組初始化失敗: {e}")
    
    def test_cisco_ui_initialization(self):
        """測試Cisco_ui模組初始化"""
        try:
            import Cisco_ui
            
            # 檢查__init__.py是否存在
            init_file = PROJECT_ROOT / "Cisco_ui" / "__init__.py"
            self.assertTrue(init_file.exists(), "Cisco_ui/__init__.py 不存在")
            
            print("✅ Cisco_ui模組初始化正常")
        except Exception as e:
            self.fail(f"❌ Cisco_ui模組初始化失敗: {e}")
    
    def test_forti_ui_initialization(self):
        """測試Forti_ui_app_bundle模組初始化"""
        try:
            import Forti_ui_app_bundle
            
            print("✅ Forti_ui_app_bundle模組初始化正常")
        except Exception as e:
            self.fail(f"❌ Forti_ui_app_bundle模組初始化失敗: {e}")


class TestScriptExecutability(unittest.TestCase):
    """測試腳本可執行性"""
    
    def test_launch_script_syntax(self):
        """測試啟動腳本語法"""
        try:
            launch_script = PROJECT_ROOT / "launch_unified_dashboard.py"
            
            # 使用Python語法檢查
            result = subprocess.run(
                [sys.executable, "-m", "py_compile", str(launch_script)],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode != 0:
                self.fail(f"啟動腳本語法錯誤: {result.stderr}")
            
            print("✅ 啟動腳本語法正確")
        except subprocess.TimeoutExpired:
            self.fail("啟動腳本語法檢查超時")
        except Exception as e:
            self.fail(f"❌ 啟動腳本語法檢查失敗: {e}")
    
    def test_unified_ui_app_syntax(self):
        """測試統一UI應用語法"""
        try:
            app_script = PROJECT_ROOT / "unified_ui" / "app.py"
            
            result = subprocess.run(
                [sys.executable, "-m", "py_compile", str(app_script)],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode != 0:
                self.fail(f"統一UI應用語法錯誤: {result.stderr}")
            
            print("✅ 統一UI應用語法正確")
        except subprocess.TimeoutExpired:
            self.fail("統一UI應用語法檢查超時")
        except Exception as e:
            self.fail(f"❌ 統一UI應用語法檢查失敗: {e}")


class TestEnvironmentCompatibility(unittest.TestCase):
    """測試環境兼容性"""
    
    def test_python_version_compatibility(self):
        """測試Python版本兼容性"""
        # 檢查Python版本
        version_info = sys.version_info
        
        # 至少需要Python 3.8
        self.assertGreaterEqual(version_info.major, 3, "需要Python 3.x")
        self.assertGreaterEqual(version_info.minor, 8, "需要Python 3.8或更高版本")
        
        print(f"✅ Python版本兼容 ({version_info.major}.{version_info.minor})")
    
    def test_required_packages_availability(self):
        """測試必需套件可用性"""
        required_packages = [
            'streamlit',
            'pandas',
            'numpy'
        ]
        
        missing_packages = []
        
        for package in required_packages:
            try:
                __import__(package)
            except ImportError:
                missing_packages.append(package)
        
        if missing_packages:
            self.fail(f"缺少必需套件: {', '.join(missing_packages)}")
        
        print(f"✅ 所有必需套件都可用: {', '.join(required_packages)}")
    
    def test_streamlit_configuration(self):
        """測試Streamlit配置"""
        try:
            streamlit_config = PROJECT_ROOT / ".streamlit"
            
            if streamlit_config.exists():
                print("✅ Streamlit配置目錄存在")
            else:
                print("⚠️  Streamlit配置目錄不存在（可選）")
        except Exception as e:
            self.fail(f"❌ Streamlit配置測試失敗: {e}")


if __name__ == "__main__":
    # 抑制警告訊息
    warnings.filterwarnings("ignore")
    
    # 運行測試
    unittest.main(verbosity=2)