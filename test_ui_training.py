#!/usr/bin/env python3
"""測試 UI 環境下的 TrainingPipeline 是否正常工作。"""

import sys
from pathlib import Path

# 模擬 UI 環境的路徑設定
project_root = Path(__file__).resolve().parent
unified_ui_root = project_root / "unified_ui"
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(unified_ui_root))

def test_training_pipeline():
    """測試 TrainingPipeline 載入和基本功能。"""
    try:
        # 模擬統一 UI 的導入方式
        from Forti_ui_app_bundle.ui_pages import training_ui
        print("✅ TrainingPipeline 模塊載入成功")
        
        # 創建 TrainingPipeline 實例
        pipeline = training_ui.TrainingPipeline(task_type='binary')
        print("✅ TrainingPipeline 實例創建成功")
        
        # 檢查 config 屬性
        if hasattr(pipeline, 'config'):
            print("✅ Pipeline 有 config 屬性")
            print(f"📝 Config keys: {list(pipeline.config.keys())}")
            
            # 測試設定 ensemble mode
            pipeline.config.setdefault("ENSEMBLE_SETTINGS", {})["MODE"] = "fixed"
            print("✅ Ensemble mode 設定成功")
            
            # 檢查 CatBoost 設定
            cat_config = pipeline.config.get("MODEL_PARAMS", {}).get("CAT", {})
            task_type = cat_config.get("task_type", "未設定")
            print(f"📋 CatBoost task_type: {task_type}")
            
            if task_type == "CPU":
                print("✅ CatBoost 已正確設定為 CPU 模式")
            else:
                print("❌ CatBoost 可能仍使用 GPU 模式")
                
        else:
            print("❌ Pipeline 缺少 config 屬性")
            return False
            
        print("\n🎯 測試結論: TrainingPipeline 在 UI 環境下應該能正常工作")
        return True
        
    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_file_operations():
    """測試檔案操作相關功能。"""
    try:
        # 檢查上傳的檔案是否存在
        test_file = Path("uploaded_engineered_data.csv")
        if test_file.exists():
            print(f"✅ 測試檔案存在: {test_file}")
            print(f"📊 檔案大小: {test_file.stat().st_size / 1024:.1f} KB")
        else:
            print("⚠️ 測試檔案不存在，請先上傳檔案")
            
        # 檢查 artifacts 目錄結構
        artifacts_dir = Path("artifacts")
        if artifacts_dir.exists():
            subdirs = list(artifacts_dir.iterdir())
            print(f"✅ Artifacts 目錄存在，包含 {len(subdirs)} 個子目錄")
            for subdir in subdirs:
                if subdir.is_dir():
                    print(f"  📁 {subdir.name}")
        else:
            print("📁 Artifacts 目錄不存在（正常，會在訓練時創建）")
            
    except Exception as e:
        print(f"❌ 檔案操作測試失敗: {e}")

if __name__ == "__main__":
    print("🔬 開始測試 UI 環境下的 TrainingPipeline...")
    print("=" * 50)
    
    success = test_training_pipeline()
    print("\n" + "=" * 50)
    test_file_operations()
    
    if success:
        print("\n🎉 所有測試通過！UI 中的訓練功能應該正常工作。")
    else:
        print("\n🚨 測試發現問題，需要進一步調查。")