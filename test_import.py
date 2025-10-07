#!/usr/bin/env python3
# 測試 TrainingPipeline 導入

print("測試 TrainingPipeline 導入...")

try:
    from Forti_ui_app_bundle.training_pipeline.pipeline_main import TrainingPipeline
    print("✓ 成功導入 TrainingPipeline")
    
    # 測試初始化
    pipeline = TrainingPipeline(
        task_type="binary",
        optuna_enabled=False,
        optimize_base=False,
        optimize_ensemble=False,
        use_tuned_for_training=False,
    )
    print("✓ 成功建立 TrainingPipeline 實例")
    print(f"✓ Config 鍵值: {list(pipeline.config.keys())}")
    
except ImportError as e:
    print(f"✗ 導入失敗: {e}")
    import traceback
    traceback.print_exc()
except Exception as e:
    print(f"✗ 其他錯誤: {e}")
    import traceback
    traceback.print_exc()