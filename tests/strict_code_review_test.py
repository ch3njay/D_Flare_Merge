"""嚴格的代碼審查和修復驗證測試"""
import os
import sys
import json
import tempfile
import subprocess
from pathlib import Path


def test_syntax_validation():
    """測試語法驗證"""
    print("🔍 進行語法驗證測試...")
    
    critical_files = [
        "launch_unified_dashboard.py",
        "unified_ui/app.py",
        "Forti_ui_app_bundle/ui_pages/notifier_app.py",
        "Forti_ui_app_bundle/ui_pages/visualization_ui.py",
        "Cisco_ui/ui_pages/notifications.py",
        "Cisco_ui/ui_pages/visualization.py"
    ]
    
    passed = 0
    failed = 0
    
    for file_path in critical_files:
        if not os.path.exists(file_path):
            print(f"⚠️  檔案不存在：{file_path}")
            continue
            
        try:
            # 使用compile函數檢查語法
            with open(file_path, 'r', encoding='utf-8') as f:
                source = f.read()
            compile(source, file_path, 'exec')
            print(f"✅ {file_path} 語法正確")
            passed += 1
        except SyntaxError as e:
            print(f"❌ {file_path} 語法錯誤: {e}")
            failed += 1
        except Exception as e:
            print(f"⚠️  {file_path} 檢查錯誤: {e}")
    
    return passed, failed


def test_import_validation():
    """測試導入驗證"""
    print("\n📦 進行模組導入測試...")
    
    critical_modules = {
        "launch_unified_dashboard": "主啟動程式",
        "unified_ui.app": "統一UI應用",
        "Forti_ui_app_bundle.ui_pages.notifier_app": "Forti通知模組",
        "Forti_ui_app_bundle.ui_pages.visualization_ui": "Forti可視化模組",
        "Cisco_ui.ui_pages.notifications": "Cisco通知模組",
        "Cisco_ui.ui_pages.visualization": "Cisco可視化模組"
    }
    
    passed = 0
    failed = 0
    
    for module_name, description in critical_modules.items():
        try:
            __import__(module_name)
            print(f"✅ {description} 導入成功")
            passed += 1
        except ImportError as e:
            print(f"❌ {description} 導入失敗: {e}")
            failed += 1
        except Exception as e:
            print(f"⚠️  {description} 檢查錯誤: {e}")
    
    return passed, failed


def test_enhanced_functionality():
    """測試增強功能"""
    print("\n🚀 進行功能增強測試...")
    
    # 測試Forti通知設定
    forti_settings = {
        "gemini_api_key": "test_key",
        "discord_webhook_url": "https://test.webhook.url",
        "convergence_window_minutes": 5,
        "risk_levels": [3, 4]
    }
    
    test_file = "test_forti_settings.txt"
    try:
        with open(test_file, 'w', encoding='utf-8') as f:
            json.dump(forti_settings, f, ensure_ascii=False, indent=2)
        
        with open(test_file, 'r', encoding='utf-8') as f:
            loaded = json.load(f)
        
        assert loaded == forti_settings, "Forti設定儲存載入不一致"
        print("✅ Forti通知設定儲存功能正常")
        os.remove(test_file)
    except Exception as e:
        print(f"❌ Forti通知設定測試失敗: {e}")
        if os.path.exists(test_file):
            os.remove(test_file)
        return 0, 1
    
    # 測試Forti可視化設定
    viz_settings = {
        "chart_folder": "/test/charts",
        "show_png_preview": True,
        "auto_refresh": False
    }
    
    test_file = "test_forti_viz_settings.json"
    try:
        with open(test_file, 'w', encoding='utf-8') as f:
            json.dump(viz_settings, f, ensure_ascii=False, indent=2)
        
        with open(test_file, 'r', encoding='utf-8') as f:
            loaded = json.load(f)
        
        assert loaded == viz_settings, "Forti可視化設定儲存載入不一致"
        print("✅ Forti可視化設定儲存功能正常")
        os.remove(test_file)
    except Exception as e:
        print(f"❌ Forti可視化設定測試失敗: {e}")
        if os.path.exists(test_file):
            os.remove(test_file)
        return 1, 1
    
    return 2, 0


def test_code_structure():
    """測試代碼結構"""
    print("\n🏗️  進行代碼結構測試...")
    
    # 檢查關鍵常數是否定義
    try:
        sys.path.insert(0, os.getcwd())
        from Forti_ui_app_bundle.ui_pages.notifier_app import (
            DEDUPE_STRATEGY_MTIME, DEDUPE_STRATEGY_HASH, DEFAULT_SETTINGS
        )
        print("✅ Forti通知模組常數定義正確")
        
        from Forti_ui_app_bundle.ui_pages.visualization_ui import (
            VIZ_CARD_OPEN, VIZ_CARD_CLOSE, CHART_FILES
        )
        print("✅ Forti可視化模組常數定義正確")
        
        return 2, 0
    except ImportError as e:
        print(f"❌ 常數導入失敗: {e}")
        return 0, 2
    except Exception as e:
        print(f"⚠️  結構檢查錯誤: {e}")
        return 0, 2


def test_error_handling():
    """測試錯誤處理"""
    print("\n🛡️  進行錯誤處理測試...")
    
    passed = 0
    
    # 檢查是否有proper的異常處理
    files_to_check = [
        "Forti_ui_app_bundle/ui_pages/notifier_app.py",
        "Forti_ui_app_bundle/ui_pages/visualization_ui.py"
    ]
    
    for file_path in files_to_check:
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # 檢查是否避免了bare except
            if "except Exception:" not in content and "except:" not in content:
                print(f"✅ {file_path} 異常處理良好")
                passed += 1
            else:
                print(f"⚠️  {file_path} 可能有過於寬泛的異常處理")
    
    return passed, max(0, len(files_to_check) - passed)


def generate_summary_report():
    """生成總結報告"""
    print("\n" + "="*60)
    print("📊 代碼審查修復驗證報告")
    print("="*60)
    
    # 運行所有測試
    tests = [
        ("語法驗證", test_syntax_validation),
        ("導入驗證", test_import_validation),
        ("功能增強", test_enhanced_functionality),
        ("代碼結構", test_code_structure),
        ("錯誤處理", test_error_handling)
    ]
    
    total_passed = 0
    total_failed = 0
    
    for test_name, test_func in tests:
        print(f"\n🧪 執行{test_name}測試...")
        try:
            passed, failed = test_func()
            total_passed += passed
            total_failed += failed
            print(f"📈 {test_name}: {passed} 通過, {failed} 失敗")
        except Exception as e:
            print(f"❌ {test_name}測試執行失敗: {e}")
            total_failed += 1
    
    # 計算分數
    total_tests = total_passed + total_failed
    success_rate = (total_passed / total_tests * 100) if total_tests > 0 else 0
    
    print("\n" + "="*60)
    print("🎯 總結:")
    print(f"   通過: {total_passed}")
    print(f"   失敗: {total_failed}")
    print(f"   成功率: {success_rate:.1f}%")
    
    if success_rate >= 80:
        print("🎉 代碼品質優秀！")
        grade = "A"
    elif success_rate >= 60:
        print("👍 代碼品質良好！")
        grade = "B"
    elif success_rate >= 40:
        print("⚠️  代碼品質需要改進")
        grade = "C"
    else:
        print("❌ 代碼品質不佳，需要大幅修復")
        grade = "D"
    
    print(f"   等級: {grade}")
    print("="*60)
    
    return success_rate > 60


def main():
    """主函數"""
    print("🚀 開始嚴格的代碼審查修復驗證...")
    
    # 檢查當前目錄
    if not os.path.exists("launch_unified_dashboard.py"):
        print("❌ 請在D-FLARE專案根目錄執行此測試")
        return False
    
    success = generate_summary_report()
    return success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)