#!/usr/bin/env python3
"""簡化的訓練測試，模擬 UI 環境但不使用輸出重定向。"""

import sys
from pathlib import Path

# 模擬 UI 環境的路徑設定
project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))

def test_training_without_redirect():
    """測試不使用輸出重定向的訓練流程。"""
    try:
        from Forti_ui_app_bundle.ui_pages.training_ui import TrainingPipeline
        
        print("✅ 載入 TrainingPipeline")
        pipeline = TrainingPipeline(task_type='binary')
        
        print("🔧 設定 ensemble mode")
        pipeline.config.setdefault("ENSEMBLE_SETTINGS", {})["MODE"] = "fixed"
        
        print("🚀 開始訓練...")
        result = pipeline.run('uploaded_engineered_data.csv')
        
        print("📋 訓練結果:")
        print(f"  - 結果類型: {type(result)}")
        print(f"  - 結果鍵值: {list(result.keys()) if result else 'None'}")
        
        if result and "artifacts_dir" in result:
            artifacts_dir = result["artifacts_dir"]
            print(f"  - Artifacts 目錄: {artifacts_dir}")
            
            # 檢查檔案是否存在
            from pathlib import Path
            artifacts_path = Path(artifacts_dir)
            if artifacts_path.exists():
                print(f"  ✅ 目錄存在")
                models_dir = artifacts_path / "models"
                if models_dir.exists():
                    model_files = list(models_dir.glob("*.joblib"))
                    print(f"  📦 模型檔案: {[f.name for f in model_files]}")
                else:
                    print(f"  ❌ models 目錄不存在")
            else:
                print(f"  ❌ artifacts 目錄不存在")
        else:
            print(f"  ❌ 結果中沒有 artifacts_dir")
            
        return result
        
    except Exception as e:
        print(f"❌ 訓練失敗: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_training_with_redirect():
    """測試使用輸出重定向的訓練流程（模擬 UI 邏輯）。"""
    import io
    import contextlib
    import queue
    import threading
    
    try:
        from Forti_ui_app_bundle.ui_pages.training_ui import TrainingPipeline
        
        print("✅ 載入 TrainingPipeline (重定向測試)")
        pipeline = TrainingPipeline(task_type='binary')
        pipeline.config.setdefault("ENSEMBLE_SETTINGS", {})["MODE"] = "fixed"
        
        result = {"error": None, "output": None}
        log_queue = queue.Queue()
        
        class _QueueStream(io.TextIOBase):
            def write(self, buf: str) -> int:
                log_queue.put(buf)
                return len(buf)
        
        def _run():
            try:
                stream = _QueueStream()
                print("🚀 開始訓練 (重定向模式)...")
                with contextlib.redirect_stdout(stream), contextlib.redirect_stderr(stream):
                    result["output"] = pipeline.run('uploaded_engineered_data.csv')
                print("✅ 訓練完成 (重定向模式)")
            except Exception as exc:
                print(f"❌ 訓練異常: {exc}")
                import traceback
                traceback.print_exc()
                result["error"] = exc
        
        thread = threading.Thread(target=_run)
        thread.start()
        thread.join()
        
        # 檢查日誌
        log_text = ""
        while not log_queue.empty():
            log_text += log_queue.get()
        
        print(f"📝 訓練日誌長度: {len(log_text)} 字符")
        print(f"📋 錯誤: {result['error']}")
        print(f"📋 輸出: {type(result['output'])} - {list(result['output'].keys()) if result['output'] else 'None'}")
        
        return result
        
    except Exception as e:
        print(f"❌ 重定向測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    print("🧪 測試 1: 不使用輸出重定向")
    print("=" * 50)
    result1 = test_training_without_redirect()
    
    print("\n" + "=" * 50)
    print("🧪 測試 2: 使用輸出重定向 (模擬 UI)")
    print("=" * 50)
    result2 = test_training_with_redirect()
    
    print("\n" + "=" * 50)
    print("📊 比較結果:")
    print(f"無重定向: {'成功' if result1 and result1.get('artifacts_dir') else '失敗'}")
    print(f"有重定向: {'成功' if result2 and result2.get('output') and result2['output'].get('artifacts_dir') else '失敗'}")