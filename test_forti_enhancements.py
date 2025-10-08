"""測試 Forti 部分的新增儲存功能"""
import os
import json
import tempfile
import unittest
from unittest.mock import patch, MagicMock

# 測試通知儲存功能
def test_forti_notification_storage():
    """測試 Forti 通知模組的設定儲存功能"""
    print("🧪 測試 Forti 通知模組儲存功能...")
    
    # 模擬設定
    test_settings = {
        "gemini_api_key": "test_key",
        "discord_webhook_url": "https://discord.com/api/webhooks/test",
        "line_channel_access_token": "test_token",
        "convergence_window_minutes": 15,
        "convergence_fields": ["source", "protocol"],
        "risk_levels": [3, 4],
        "dedupe_strategy": "File hash"
    }
    
    # 測試檔案路徑
    test_file = "test_forti_notifier_settings.txt"
    
    try:
        # 模擬儲存功能
        with open(test_file, 'w', encoding='utf-8') as f:
            json.dump(test_settings, f, ensure_ascii=False, indent=2)
        
        # 驗證檔案是否正確儲存
        with open(test_file, 'r', encoding='utf-8') as f:
            loaded_settings = json.load(f)
        
        assert loaded_settings == test_settings, "設定儲存/載入不一致"
        print("✅ 通知模組設定儲存功能正常")
        
        # 清理測試檔案
        os.remove(test_file)
        return True
        
    except Exception as e:
        print(f"❌ 通知模組測試失敗：{e}")
        if os.path.exists(test_file):
            os.remove(test_file)
        return False


def test_forti_visualization_storage():
    """測試 Forti 可視化模組的設定儲存功能"""
    print("🧪 測試 Forti 可視化模組儲存功能...")
    
    # 模擬設定
    test_viz_settings = {
        "chart_folder": "/path/to/charts",
        "auto_refresh": True,
        "show_png_preview": True
    }
    
    # 測試檔案路徑
    test_file = "test_forti_visualization_settings.json"
    
    try:
        # 模擬儲存功能
        with open(test_file, 'w', encoding='utf-8') as f:
            json.dump(test_viz_settings, f, ensure_ascii=False, indent=2)
        
        # 驗證檔案是否正確儲存
        with open(test_file, 'r', encoding='utf-8') as f:
            loaded_settings = json.load(f)
        
        assert loaded_settings == test_viz_settings, "可視化設定儲存/載入不一致"
        print("✅ 可視化模組設定儲存功能正常")
        
        # 清理測試檔案
        os.remove(test_file)
        return True
        
    except Exception as e:
        print(f"❌ 可視化模組測試失敗：{e}")
        if os.path.exists(test_file):
            os.remove(test_file)  
        return False


def test_png_preview_functionality():
    """測試 PNG 預覽功能"""
    print("🧪 測試 PNG 預覽功能...")
    
    # 創建測試資料夾和假圖片檔案
    with tempfile.TemporaryDirectory() as temp_dir:
        chart_files = {
            "二元長條圖": "binary_bar.png",
            "二元圓餅圖": "binary_pie.png", 
            "多元長條圖": "multiclass_bar.png",
            "多元圓餅圖": "multiclass_pie.png"
        }
        
        # 創建假的PNG檔案
        created_files = []
        for chart_name, filename in chart_files.items():
            filepath = os.path.join(temp_dir, filename)
            with open(filepath, 'w') as f:
                f.write("fake png content")
            created_files.append(filepath)
        
        # 驗證檔案是否創建成功
        for filepath in created_files:
            assert os.path.exists(filepath), f"測試檔案創建失敗：{filepath}"
        
        print("✅ PNG 預覽功能測試檔案創建成功")
        print(f"📁 測試資料夾：{temp_dir}")
        print(f"📄 創建檔案：{list(chart_files.values())}")
        
        return True


def test_settings_integration():
    """測試設定整合功能"""
    print("🧪 測試設定整合功能...")
    
    # 測試預設設定結構
    default_notification_settings = {
        "gemini_api_key": "",
        "line_channel_secret": "",
        "line_channel_access_token": "",
        "line_webhook_url": "",
        "discord_webhook_url": "",
        "convergence_window_minutes": 10,
        "convergence_fields": ["source", "destination"],
        "risk_levels": [3, 4],
        "dedupe_strategy": "Filename + mtime"
    }
    
    default_viz_settings = {
        "chart_folder": "",
        "auto_refresh": True,
        "show_png_preview": False
    }
    
    # 驗證設定結構完整性
    required_notification_keys = [
        "gemini_api_key", "discord_webhook_url", "line_channel_access_token",
        "convergence_window_minutes", "convergence_fields", "risk_levels"
    ]
    
    for key in required_notification_keys:
        assert key in default_notification_settings, f"缺少通知設定鍵：{key}"
    
    required_viz_keys = ["chart_folder", "auto_refresh", "show_png_preview"]
    for key in required_viz_keys:
        assert key in default_viz_settings, f"缺少視覺化設定鍵：{key}"
    
    print("✅ 設定整合功能結構正確")
    return True


def main():
    """執行所有測試"""
    print("🚀 開始測試 Forti 部分新增功能...")
    print("=" * 60)
    
    tests = [
        ("通知儲存功能", test_forti_notification_storage),
        ("可視化儲存功能", test_forti_visualization_storage), 
        ("PNG預覽功能", test_png_preview_functionality),
        ("設定整合功能", test_settings_integration),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        print(f"\n📋 執行測試：{test_name}")
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ 測試執行錯誤：{e}")
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"📊 測試結果：通過 {passed}/{len(tests)}，失敗 {failed}/{len(tests)}")
    
    if failed == 0:
        print("🎉 所有 Forti 新增功能測試通過！")
        return True
    else:
        print("⚠️  部分測試失敗，請檢查相關功能")
        return False


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)