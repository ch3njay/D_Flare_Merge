"""測試目標欄位自動偵測功能"""
import pandas as pd
import numpy as np
import os
import sys
from pathlib import Path

# 確保專案根目錄在 Python 路徑中
_PROJECT_ROOT = Path(__file__).resolve().parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from Cisco_ui.training_pipeline.pipeline_main import CiscoTrainingPipeline


def create_test_data_with_standard_label():
    """建立包含標準標籤欄位的測試資料"""
    print("\n" + "="*60)
    print("測試案例 1：標準標籤欄位（is_attack）")
    print("="*60)
    
    # 建立測試資料
    np.random.seed(42)
    n_samples = 1000
    
    data = {
        'feature1': np.random.randn(n_samples),
        'feature2': np.random.randn(n_samples),
        'feature3': np.random.randint(0, 100, n_samples),
        'is_attack': np.random.randint(0, 2, n_samples)  # 標準標籤欄位
    }
    
    df = pd.DataFrame(data)
    csv_path = "test_data_standard.csv"
    df.to_csv(csv_path, index=False)
    
    print(f"✅ 測試資料已建立：{csv_path}")
    print(f"資料形狀：{df.shape}")
    print(f"欄位：{list(df.columns)}")
    
    return csv_path


def create_test_data_with_custom_label():
    """建立包含自訂標籤欄位的測試資料"""
    print("\n" + "="*60)
    print("測試案例 2：自訂標籤欄位（label）")
    print("="*60)
    
    # 建立測試資料
    np.random.seed(42)
    n_samples = 1000
    
    data = {
        'feature1': np.random.randn(n_samples),
        'feature2': np.random.randn(n_samples),
        'feature3': np.random.randint(0, 100, n_samples),
        'label': np.random.randint(0, 2, n_samples)  # 常見標籤欄位名稱
    }
    
    df = pd.DataFrame(data)
    csv_path = "test_data_custom.csv"
    df.to_csv(csv_path, index=False)
    
    print(f"✅ 測試資料已建立：{csv_path}")
    print(f"資料形狀：{df.shape}")
    print(f"欄位：{list(df.columns)}")
    
    return csv_path


def create_test_data_without_obvious_label():
    """建立沒有明顯標籤欄位的測試資料（需要智慧偵測）"""
    print("\n" + "="*60)
    print("測試案例 3：無明顯標籤欄位（智慧偵測）")
    print("="*60)
    
    # 建立測試資料
    np.random.seed(42)
    n_samples = 1000
    
    data = {
        'src_ip': np.random.randint(1, 255, n_samples),
        'dst_ip': np.random.randint(1, 255, n_samples),
        'port': np.random.randint(1, 65535, n_samples),
        'bytes': np.random.randint(0, 10000, n_samples),
        'risk': np.random.randint(0, 3, n_samples)  # 這應該被偵測為目標欄位
    }
    
    df = pd.DataFrame(data)
    csv_path = "test_data_smart_detect.csv"
    df.to_csv(csv_path, index=False)
    
    print(f"✅ 測試資料已建立：{csv_path}")
    print(f"資料形狀：{df.shape}")
    print(f"欄位：{list(df.columns)}")
    print(f"提示：'risk' 欄位應該被自動偵測為目標欄位（唯一值少）")
    
    return csv_path


def test_pipeline_with_auto_detection(csv_path, test_name):
    """測試自動偵測功能"""
    print(f"\n🧪 執行測試：{test_name}")
    print("-" * 60)
    
    try:
        # 建立訓練管線（不指定 target_column）
        pipeline = CiscoTrainingPipeline(
            task_type="binary",
            config={
                "test_size": 0.2,
                "random_state": 42,
                "output_dir": "./test_artifacts"
            },
            target_column=None  # 不指定，讓系統自動偵測
        )
        
        # 載入資料並測試目標欄位偵測
        df = pd.read_csv(csv_path)
        detected_target = pipeline._determine_target_column(df)
        
        if detected_target:
            print(f"✅ 成功偵測到目標欄位：{detected_target}")
            print(f"   唯一值數量：{df[detected_target].nunique()}")
            print(f"   值分佈：{df[detected_target].value_counts().to_dict()}")
            return True
        else:
            print(f"❌ 未能偵測到目標欄位")
            return False
            
    except Exception as e:
        print(f"❌ 測試失敗：{str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_pipeline_with_manual_specification(csv_path, target_col, test_name):
    """測試手動指定目標欄位"""
    print(f"\n🧪 執行測試：{test_name}")
    print("-" * 60)
    
    try:
        # 建立訓練管線（手動指定 target_column）
        pipeline = CiscoTrainingPipeline(
            task_type="binary",
            config={
                "test_size": 0.2,
                "random_state": 42,
                "output_dir": "./test_artifacts"
            },
            target_column=target_col
        )
        
        # 載入資料並測試目標欄位偵測
        df = pd.read_csv(csv_path)
        detected_target = pipeline._determine_target_column(df)
        
        if detected_target == target_col:
            print(f"✅ 成功使用指定的目標欄位：{detected_target}")
            return True
        else:
            print(f"❌ 目標欄位不符：期望 {target_col}，得到 {detected_target}")
            return False
            
    except Exception as e:
        print(f"❌ 測試失敗：{str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_full_training_pipeline(csv_path, target_col, test_name):
    """測試完整訓練流程"""
    print(f"\n🧪 執行完整訓練測試：{test_name}")
    print("-" * 60)
    
    try:
        # 建立訓練管線
        pipeline = CiscoTrainingPipeline(
            task_type="binary",
            config={
                "test_size": 0.2,
                "random_state": 42,
                "output_dir": "./test_artifacts"
            },
            target_column=target_col
        )
        
        # 執行訓練（只載入資料和準備特徵，不實際訓練模型）
        df = pd.read_csv(csv_path)
        X, y = pipeline._prepare_features(df)
        
        print(f"✅ 特徵準備成功")
        print(f"   特徵數量：{X.shape[1]}")
        print(f"   樣本數量：{X.shape[0]}")
        print(f"   標籤分佈：\n{y.value_counts()}")
        
        return True
        
    except Exception as e:
        print(f"❌ 測試失敗：{str(e)}")
        import traceback
        traceback.print_exc()
        return False


def cleanup_test_files():
    """清理測試檔案"""
    test_files = [
        "test_data_standard.csv",
        "test_data_custom.csv",
        "test_data_smart_detect.csv"
    ]
    
    for file in test_files:
        if os.path.exists(file):
            os.remove(file)
            print(f"🗑️ 已刪除測試檔案：{file}")


def main():
    """執行所有測試"""
    print("\n" + "="*60)
    print("🧪 目標欄位自動偵測功能測試")
    print("="*60)
    
    results = []
    
    # 測試 1：標準標籤欄位
    csv1 = create_test_data_with_standard_label()
    results.append(test_pipeline_with_auto_detection(
        csv1, 
        "自動偵測標準標籤（is_attack）"
    ))
    results.append(test_full_training_pipeline(
        csv1,
        None,
        "完整訓練流程（is_attack）"
    ))
    
    # 測試 2：自訂標籤欄位
    csv2 = create_test_data_with_custom_label()
    results.append(test_pipeline_with_auto_detection(
        csv2,
        "自動偵測常見標籤（label）"
    ))
    results.append(test_pipeline_with_manual_specification(
        csv2,
        "label",
        "手動指定目標欄位（label）"
    ))
    
    # 測試 3：智慧偵測
    csv3 = create_test_data_without_obvious_label()
    results.append(test_pipeline_with_auto_detection(
        csv3,
        "智慧偵測目標欄位（risk）"
    ))
    results.append(test_pipeline_with_manual_specification(
        csv3,
        "risk",
        "手動指定目標欄位（risk）"
    ))
    
    # 測試摘要
    print("\n" + "="*60)
    print("📊 測試摘要")
    print("="*60)
    
    total_tests = len(results)
    passed_tests = sum(results)
    
    print(f"總測試數：{total_tests}")
    print(f"通過：{passed_tests} ✅")
    print(f"失敗：{total_tests - passed_tests} ❌")
    print(f"成功率：{passed_tests/total_tests*100:.1f}%")
    
    # 詢問是否清理測試檔案
    print("\n" + "="*60)
    cleanup = input("是否清理測試檔案？(y/n): ")
    if cleanup.lower() == 'y':
        cleanup_test_files()
    
    print("\n✅ 測試完成！")


if __name__ == "__main__":
    main()
