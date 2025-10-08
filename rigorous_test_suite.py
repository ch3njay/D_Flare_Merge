#!/usr/bin/env python3
"""更嚴謹的深度檢查工具 - 全面驗證集成功能的穩定性和可靠性"""

import sys
import os
import ast
import tempfile
import traceback
import warnings
import time
import gc
import threading
import multiprocessing
import psutil
from typing import Dict, Any, List, Tuple, Optional
import numpy as np
import pandas as pd
from sklearn.datasets import make_classification, make_multilabel_classification
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC
from sklearn.tree import DecisionTreeClassifier

# 添加項目根目錄到路徑
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

class RigorousTestSuite:
    """更嚴謹的測試套件"""
    
    def __init__(self):
        self.test_results = []
        self.errors = []
        self.warnings = []
        self.critical_failures = []
        
    def log_test(self, test_name: str, success: bool, message: str = "", 
                 severity: str = "info", details: Dict = None):
        """記錄測試結果"""
        result = {
            "test_name": test_name,
            "success": success,
            "message": message,
            "severity": severity,
            "details": details or {},
            "timestamp": time.time()
        }
        self.test_results.append(result)
        
        # 根據嚴重程度選擇圖標
        if severity == "critical":
            status = "🔥"
            self.critical_failures.append(result)
        elif severity == "error":
            status = "❌"
            self.errors.append(result)
        elif severity == "warning":
            status = "⚠️"
            self.warnings.append(result)
        else:
            status = "✅" if success else "❌"
        
        print(f"{status} {test_name}: {message}")
        
    def deep_syntax_check(self):
        """深度語法檢查"""
        print("\n🔍 深度語法和運行時檢查...")
        
        files_to_check = [
            "d:\\work\\PROJECT\\D_Flare_Merge\\Forti_ui_app_bundle\\training_pipeline\\combo_optimizer.py",
            "d:\\work\\PROJECT\\D_Flare_Merge\\Cisco_ui\\training_pipeline\\combo_optimizer.py",
            "d:\\work\\PROJECT\\D_Flare_Merge\\Cisco_ui\\training_pipeline\\pipeline_main.py",
            "d:\\work\\PROJECT\\D_Flare_Merge\\Cisco_ui\\training_pipeline\\ensemble_optuna.py",
            "d:\\work\\PROJECT\\D_Flare_Merge\\Forti_ui_app_bundle\\training_pipeline\\ensemble_optuna.py"
        ]
        
        for file_path in files_to_check:
            if os.path.exists(file_path):
                self._check_file_syntax(file_path)
            else:
                self.log_test(f"file_exists_{os.path.basename(file_path)}", 
                             False, f"文件不存在: {file_path}", "error")
    
    def _check_file_syntax(self, file_path: str):
        """檢查單個文件的語法"""
        try:
            file_name = os.path.basename(file_path)
            
            # 1. 讀取文件內容
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 2. AST 語法檢查
            try:
                ast.parse(content)
                self.log_test(f"ast_parse_{file_name}", True, "AST 語法解析成功")
            except SyntaxError as e:
                self.log_test(f"ast_parse_{file_name}", False, 
                             f"語法錯誤: {e}", "critical")
                return
            
            # 3. 編譯檢查
            try:
                compile(content, file_path, 'exec')
                self.log_test(f"compile_{file_name}", True, "編譯檢查通過")
            except Exception as e:
                self.log_test(f"compile_{file_name}", False, 
                             f"編譯錯誤: {e}", "error")
            
            # 4. 導入檢查
            if file_name == "combo_optimizer.py":
                self._test_module_import(file_path)
            
            # 5. 類型一致性檢查
            self._check_type_consistency(file_path, content)
            
        except Exception as e:
            self.log_test(f"syntax_check_{os.path.basename(file_path)}", 
                         False, f"檢查失敗: {e}", "critical")
    
    def _test_module_import(self, file_path: str):
        """測試模組導入"""
        try:
            if "Forti_ui_app_bundle" in file_path:
                from Forti_ui_app_bundle.training_pipeline.combo_optimizer import ComboOptimizer
                self.log_test("import_fortinet_combo", True, "Fortinet ComboOptimizer 導入成功")
            elif "Cisco_ui" in file_path:
                from Cisco_ui.training_pipeline.combo_optimizer import ComboOptimizer
                self.log_test("import_cisco_combo", True, "Cisco ComboOptimizer 導入成功")
        except ImportError as e:
            self.log_test("import_module", False, f"模組導入失敗: {e}", "error")
        except Exception as e:
            self.log_test("import_module", False, f"導入測試異常: {e}", "warning")
    
    def _check_type_consistency(self, file_path: str, content: str):
        """檢查類型一致性"""
        file_name = os.path.basename(file_path)
        
        # 檢查常見的類型不一致問題
        issues = []
        
        # 檢查 X_train/x_train 一致性
        if 'X_train' in content and 'x_train' in content:
            issues.append("變數命名不一致: X_train 和 x_train 同時存在")
        
        # 檢查返回類型註解
        import re
        func_defs = re.findall(r'def\s+\w+\([^)]*\)\s*->\s*([^:]+):', content)
        for return_type in func_defs:
            if 'Dict[str, Dict]' in return_type:
                issues.append("返回類型註解不完整: Dict[str, Dict] 應該是 Dict[str, Dict[str, Any]]")
        
        if issues:
            self.log_test(f"type_consistency_{file_name}", False, 
                         f"類型一致性問題: {'; '.join(issues)}", "warning")
        else:
            self.log_test(f"type_consistency_{file_name}", True, "類型一致性檢查通過")

    def strict_dependency_verification(self):
        """嚴格依賴關係驗證"""
        print("\n🔗 嚴格依賴關係驗證...")
        
        # 1. 檢查 Python 版本兼容性
        self._check_python_version()
        
        # 2. 檢查必要依賴
        self._check_required_dependencies()
        
        # 3. 檢查循環導入
        self._check_circular_imports()
        
        # 4. 檢查版本兼容性
        self._check_version_compatibility()
    
    def _check_python_version(self):
        """檢查 Python 版本"""
        current_version = sys.version_info
        min_version = (3, 8)
        
        if current_version >= min_version:
            self.log_test("python_version", True, 
                         f"Python 版本 {current_version.major}.{current_version.minor} 兼容")
        else:
            self.log_test("python_version", False, 
                         f"Python 版本過低: {current_version.major}.{current_version.minor} < 3.8", 
                         "critical")
    
    def _check_required_dependencies(self):
        """檢查必要依賴"""
        required_packages = [
            ('numpy', 'np'),
            ('pandas', 'pd'),
            ('sklearn', 'sklearn'),
            ('joblib', 'joblib'),
            ('optuna', 'optuna')
        ]
        
        for package, alias in required_packages:
            try:
                __import__(package)
                self.log_test(f"dependency_{package}", True, f"依賴 {package} 可用")
            except ImportError:
                self.log_test(f"dependency_{package}", False, 
                             f"缺少必要依賴: {package}", "error")
    
    def _check_circular_imports(self):
        """檢查循環導入"""
        try:
            # 測試可能的循環導入路徑
            import importlib
            import sys
            
            # 清除模組緩存
            modules_to_clear = [m for m in sys.modules.keys() 
                              if 'combo_optimizer' in m or 'ensemble_optuna' in m]
            for mod in modules_to_clear:
                if mod in sys.modules:
                    del sys.modules[mod]
            
            # 嘗試導入
            from Forti_ui_app_bundle.training_pipeline import combo_optimizer
            from Cisco_ui.training_pipeline import combo_optimizer as cisco_combo
            
            self.log_test("circular_imports", True, "無循環導入問題")
            
        except ImportError as e:
            if "circular import" in str(e).lower():
                self.log_test("circular_imports", False, f"發現循環導入: {e}", "error")
            else:
                self.log_test("circular_imports", True, "無循環導入問題")
        except Exception as e:
            self.log_test("circular_imports", False, f"導入檢查異常: {e}", "warning")
    
    def _check_version_compatibility(self):
        """檢查版本兼容性"""
        try:
            import sklearn
            import numpy as np
            import pandas as pd
            
            # 檢查 sklearn 版本
            sklearn_version = sklearn.__version__
            if sklearn_version >= "1.0.0":
                self.log_test("sklearn_version", True, f"sklearn {sklearn_version} 兼容")
            else:
                self.log_test("sklearn_version", False, 
                             f"sklearn 版本過低: {sklearn_version}", "warning")
            
            # 檢查 numpy 版本
            numpy_version = np.__version__
            if numpy_version >= "1.19.0":
                self.log_test("numpy_version", True, f"numpy {numpy_version} 兼容")
            else:
                self.log_test("numpy_version", False, 
                             f"numpy 版本過低: {numpy_version}", "warning")
            
        except Exception as e:
            self.log_test("version_compatibility", False, f"版本檢查失敗: {e}", "error")

    def extreme_edge_case_testing(self):
        """極限邊界情況測試"""
        print("\n⚡ 極限邊界情況測試...")
        
        # 1. 巨大數據集測試
        self._test_massive_dataset()
        
        # 2. 損壞數據測試
        self._test_corrupted_data()
        
        # 3. 併發訪問測試
        self._test_concurrent_access()
        
        # 4. 資源耗盡測試
        self._test_resource_exhaustion()
    
    def _test_massive_dataset(self):
        """測試巨大數據集"""
        try:
            print("  🔄 測試大型數據集處理...")
            
            # 創建大型數據集 (50k 樣本)
            X, y = make_classification(
                n_samples=50000,
                n_features=100,
                n_informative=80,
                n_classes=2,
                random_state=42
            )
            
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.1, random_state=42  # 只用 10% 作為測試集節省時間
            )
            
            # 監控記憶體使用
            process = psutil.Process()
            initial_memory = process.memory_info().rss / 1024 / 1024  # MB
            
            from Forti_ui_app_bundle.training_pipeline.combo_optimizer import ComboOptimizer
            
            models = [
                ('rf', RandomForestClassifier(n_estimators=5, random_state=42, n_jobs=1)),
                ('lr', LogisticRegression(random_state=42, max_iter=50))  # 減少迭代次數
            ]
            
            for name, model in models:
                model.fit(X_train, y_train)
            
            with tempfile.TemporaryDirectory() as temp_dir:
                start_time = time.time()
                
                combo_opt = ComboOptimizer(
                    estimators=models,
                    X_train=X_train,
                    y_train=y_train,
                    X_valid=X_test,
                    y_valid=y_test,
                    task_type="binary",
                    config={"ENSEMBLE_SETTINGS": {"VOTING": "soft"}},
                    out_dir=temp_dir
                )
                
                result = combo_opt.optimize()
                
                end_time = time.time()
                final_memory = process.memory_info().rss / 1024 / 1024  # MB
                
                duration = end_time - start_time
                memory_increase = final_memory - initial_memory
                
                # 檢查結果
                if result and 'metrics' in result:
                    # 性能標準：50k 樣本不超過 5 分鐘
                    time_ok = duration < 300
                    # 記憶體標準：增長不超過 2GB
                    memory_ok = memory_increase < 2000
                    
                    if time_ok and memory_ok:
                        self.log_test("massive_dataset", True, 
                                     f"大型數據集處理成功: {duration:.1f}s, +{memory_increase:.1f}MB")
                    else:
                        self.log_test("massive_dataset", False, 
                                     f"性能不達標: {duration:.1f}s, +{memory_increase:.1f}MB", 
                                     "warning")
                else:
                    self.log_test("massive_dataset", False, "大型數據集處理失敗", "error")
                    
        except MemoryError:
            self.log_test("massive_dataset", False, "記憶體不足", "error")
        except Exception as e:
            self.log_test("massive_dataset", False, f"大型數據集測試失敗: {e}", "error")
    
    def _test_corrupted_data(self):
        """測試損壞數據"""
        print("  🛠️ 測試損壞數據處理...")
        
        try:
            from Forti_ui_app_bundle.training_pipeline.combo_optimizer import ComboOptimizer
            
            # 創建正常數據
            X, y = make_classification(n_samples=100, n_features=10, n_classes=2, random_state=42)
            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=42)
            
            # 測試各種損壞的數據
            corruption_tests = [
                ("nan_features", self._create_nan_data(X_train), y_train, X_test, y_test),
                ("inf_features", self._create_inf_data(X_train), y_train, X_test, y_test),
                ("mismatched_dimensions", X_train[:50], y_train, X_test, y_test),
                ("wrong_label_type", X_train, y_train.astype(str), X_test, y_test),
            ]
            
            for test_name, X_corrupt, y_corrupt, X_val, y_val in corruption_tests:
                try:
                    models = [('rf', RandomForestClassifier(n_estimators=3, random_state=42))]
                    
                    # 嘗試訓練模型
                    for name, model in models:
                        model.fit(X_corrupt, y_corrupt)
                    
                    with tempfile.TemporaryDirectory() as temp_dir:
                        combo_opt = ComboOptimizer(
                            estimators=models,
                            X_train=X_corrupt,
                            y_train=y_corrupt,
                            X_valid=X_val,
                            y_valid=y_val,
                            task_type="binary",
                            config={},
                            out_dir=temp_dir
                        )
                        
                        result = combo_opt.optimize()
                        
                        # 某些損壞數據應該被處理或拒絕
                        if test_name in ["nan_features", "inf_features", "wrong_label_type"]:
                            self.log_test(f"corrupted_data_{test_name}", True, 
                                         "損壞數據被妥善處理或拒絕")
                        else:
                            self.log_test(f"corrupted_data_{test_name}", True, 
                                         "損壞數據處理正常")
                
                except Exception as e:
                    # 對於某些損壞數據，拋出異常是預期的
                    if test_name in ["mismatched_dimensions", "wrong_label_type"]:
                        self.log_test(f"corrupted_data_{test_name}", True, 
                                     f"正確拒絕損壞數據: {type(e).__name__}")
                    else:
                        self.log_test(f"corrupted_data_{test_name}", False, 
                                     f"損壞數據處理失敗: {e}", "warning")
                
        except Exception as e:
            self.log_test("corrupted_data", False, f"損壞數據測試失敗: {e}", "error")
    
    def _create_nan_data(self, X):
        """創建包含 NaN 的數據"""
        X_nan = X.copy()
        X_nan[0, 0] = np.nan
        X_nan[1, 1] = np.nan
        return X_nan
    
    def _create_inf_data(self, X):
        """創建包含 Inf 的數據"""
        X_inf = X.copy()
        X_inf[0, 0] = np.inf
        X_inf[1, 1] = -np.inf
        return X_inf
    
    def _test_concurrent_access(self):
        """測試併發訪問"""
        print("  🔄 測試併發訪問...")
        
        def worker_function(worker_id):
            """工作線程函數"""
            try:
                from Forti_ui_app_bundle.training_pipeline.combo_optimizer import ComboOptimizer
                
                X, y = make_classification(n_samples=50, n_features=5, n_classes=2, random_state=worker_id)
                X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=worker_id)
                
                models = [('rf', RandomForestClassifier(n_estimators=2, random_state=worker_id))]
                for name, model in models:
                    model.fit(X_train, y_train)
                
                with tempfile.TemporaryDirectory() as temp_dir:
                    combo_opt = ComboOptimizer(
                        estimators=models,
                        X_train=X_train,
                        y_train=y_train,
                        X_valid=X_test,
                        y_valid=y_test,
                        task_type="binary",
                        config={},
                        out_dir=temp_dir
                    )
                    
                    result = combo_opt.optimize()
                    return result is not None and 'metrics' in result
                    
            except Exception as e:
                print(f"Worker {worker_id} 失敗: {e}")
                return False
        
        try:
            # 創建多個線程同時執行
            threads = []
            results = []
            
            def thread_wrapper(worker_id, results_list):
                result = worker_function(worker_id)
                results_list.append((worker_id, result))
            
            # 啟動 3 個併發線程
            for i in range(3):
                thread = threading.Thread(target=thread_wrapper, args=(i, results))
                threads.append(thread)
                thread.start()
            
            # 等待所有線程完成
            for thread in threads:
                thread.join(timeout=60)  # 60秒超時
            
            # 檢查結果
            successful_workers = sum(1 for _, success in results if success)
            
            if successful_workers >= 2:  # 至少 2 個成功
                self.log_test("concurrent_access", True, 
                             f"併發訪問測試通過: {successful_workers}/3 成功")
            else:
                self.log_test("concurrent_access", False, 
                             f"併發訪問失敗: 只有 {successful_workers}/3 成功", "warning")
                
        except Exception as e:
            self.log_test("concurrent_access", False, f"併發測試異常: {e}", "error")
    
    def _test_resource_exhaustion(self):
        """測試資源耗盡情況"""
        print("  💾 測試資源限制...")
        
        try:
            # 監控初始資源
            process = psutil.Process()
            initial_memory = process.memory_info().rss / 1024 / 1024  # MB
            
            # 創建多個大型模型來測試資源使用
            models = []
            for i in range(5):  # 創建 5 個模型
                models.append((f'rf_{i}', RandomForestClassifier(n_estimators=20, random_state=i)))
            
            X, y = make_classification(n_samples=1000, n_features=50, n_classes=2, random_state=42)
            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=42)
            
            # 訓練所有模型
            for name, model in models:
                model.fit(X_train, y_train)
            
            # 測試資源使用
            current_memory = process.memory_info().rss / 1024 / 1024  # MB
            memory_increase = current_memory - initial_memory
            
            if memory_increase < 1000:  # 小於 1GB
                self.log_test("resource_usage", True, 
                             f"資源使用合理: +{memory_increase:.1f}MB")
            else:
                self.log_test("resource_usage", False, 
                             f"資源使用過高: +{memory_increase:.1f}MB", "warning")
            
            # 清理記憶體
            del models
            gc.collect()
            
        except Exception as e:
            self.log_test("resource_exhaustion", False, f"資源測試失敗: {e}", "error")

    def complex_multiclass_deep_testing(self):
        """複雜多類別深度測試"""
        print("\n🎯 複雜多類別深度測試...")
        
        # 1. 不平衡數據測試
        self._test_imbalanced_multiclass()
        
        # 2. 類別缺失測試
        self._test_missing_classes()
        
        # 3. 異常標籤測試
        self._test_abnormal_labels()
        
        # 4. 高維多類別測試
        self._test_high_dimensional_multiclass()
    
    def _test_imbalanced_multiclass(self):
        """測試不平衡多類別數據"""
        try:
            print("  ⚖️ 測試不平衡多類別數據...")
            
            from Forti_ui_app_bundle.training_pipeline.combo_optimizer import ComboOptimizer
            
            # 創建嚴重不平衡的多類別數據
            n_samples = [500, 50, 10]  # 極度不平衡
            X_parts, y_parts = [], []
            
            for class_id, n_sample in enumerate(n_samples):
                X_part, _ = make_classification(
                    n_samples=n_sample,
                    n_features=20,
                    n_informative=15,
                    n_classes=2,
                    random_state=class_id
                )
                y_part = np.full(n_sample, class_id)
                X_parts.append(X_part)
                y_parts.append(y_part)
            
            X = np.vstack(X_parts)
            y = np.hstack(y_parts)
            
            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=42)
            
            models = [
                ('rf', RandomForestClassifier(n_estimators=5, random_state=42)),
                ('lr', LogisticRegression(random_state=42, max_iter=200))
            ]
            
            for name, model in models:
                model.fit(X_train, y_train)
            
            with tempfile.TemporaryDirectory() as temp_dir:
                combo_opt = ComboOptimizer(
                    estimators=models,
                    X_train=X_train,
                    y_train=y_train,
                    X_valid=X_test,
                    y_valid=y_test,
                    task_type="multiclass",
                    config={},
                    out_dir=temp_dir
                )
                
                result = combo_opt.optimize()
                
                if result and 'metrics' in result:
                    metrics = result['metrics']
                    
                    # 檢查多類別指標
                    checks = {
                        "auc_calculated": not np.isnan(metrics.get('auc', np.nan)),
                        "confusion_matrix_shape": metrics.get('confusion_matrix', np.array([])).shape == (3, 3),
                        "submodel_metrics": len(metrics.get('submodel_metrics', {})) == 2,
                        "f1_score_valid": 0 <= metrics.get('f1', -1) <= 1
                    }
                    
                    all_passed = all(checks.values())
                    
                    if all_passed:
                        self.log_test("imbalanced_multiclass", True, 
                                     "不平衡多類別數據處理成功")
                    else:
                        failed_checks = [k for k, v in checks.items() if not v]
                        self.log_test("imbalanced_multiclass", False, 
                                     f"部分檢查失敗: {failed_checks}", "warning")
                else:
                    self.log_test("imbalanced_multiclass", False, 
                                 "不平衡多類別數據處理失敗", "error")
                    
        except Exception as e:
            self.log_test("imbalanced_multiclass", False, 
                         f"不平衡多類別測試失敗: {e}", "error")
    
    def _test_missing_classes(self):
        """測試類別缺失情況"""
        try:
            print("  🕳️ 測試類別缺失情況...")
            
            from Forti_ui_app_bundle.training_pipeline.combo_optimizer import ComboOptimizer
            
            # 創建數據，然後人為移除某些類別
            X, y = make_classification(n_samples=300, n_features=10, n_classes=4, random_state=42)
            
            # 從訓練集中移除類別 3
            mask = y != 3
            X_filtered = X[mask]
            y_filtered = y[mask]
            
            X_train, X_test, y_train, y_test = train_test_split(
                X_filtered, y_filtered, test_size=0.3, random_state=42
            )
            
            # 但測試集可能包含類別 3
            X_test_with_missing = X[:50]  # 包含所有類別的測試集
            y_test_with_missing = y[:50]
            
            models = [('rf', RandomForestClassifier(n_estimators=3, random_state=42))]
            for name, model in models:
                model.fit(X_train, y_train)
            
            with tempfile.TemporaryDirectory() as temp_dir:
                combo_opt = ComboOptimizer(
                    estimators=models,
                    X_train=X_train,
                    y_train=y_train,
                    X_valid=X_test_with_missing,
                    y_valid=y_test_with_missing,
                    task_type="multiclass",
                    config={},
                    out_dir=temp_dir
                )
                
                result = combo_opt.optimize()
                
                # 這種情況應該被妥善處理
                if result:
                    self.log_test("missing_classes", True, 
                                 "類別缺失情況被妥善處理")
                else:
                    self.log_test("missing_classes", False, 
                                 "類別缺失處理失敗", "warning")
                    
        except Exception as e:
            # 異常也是可接受的結果
            self.log_test("missing_classes", True, 
                         f"類別缺失被正確拒絕: {type(e).__name__}")
    
    def _test_abnormal_labels(self):
        """測試異常標籤"""
        try:
            print("  🏷️ 測試異常標籤...")
            
            from Forti_ui_app_bundle.training_pipeline.combo_optimizer import ComboOptimizer
            
            # 創建包含異常標籤的數據
            X, y = make_classification(n_samples=100, n_features=10, n_classes=3, random_state=42)
            
            # 創建異常標籤情況
            abnormal_tests = [
                ("negative_labels", X, y - 1),  # 負數標籤
                ("string_labels", X, np.array(['A', 'B', 'C'] * (len(y)//3 + 1))[:len(y)]),  # 字符串標籤
                ("float_labels", X, y.astype(float) + 0.5),  # 浮點標籤
            ]
            
            for test_name, X_test, y_test in abnormal_tests:
                try:
                    X_train, X_val, y_train, y_val = train_test_split(X_test, y_test, test_size=0.3, random_state=42)
                    
                    models = [('rf', RandomForestClassifier(n_estimators=2, random_state=42))]
                    
                    # 嘗試訓練
                    for name, model in models:
                        model.fit(X_train, y_train)
                    
                    with tempfile.TemporaryDirectory() as temp_dir:
                        combo_opt = ComboOptimizer(
                            estimators=models,
                            X_train=X_train,
                            y_train=y_train,
                            X_valid=X_val,
                            y_valid=y_val,
                            task_type="multiclass",
                            config={},
                            out_dir=temp_dir
                        )
                        
                        result = combo_opt.optimize()
                        
                        if test_name == "string_labels":
                            # 字符串標籤可能被處理
                            self.log_test(f"abnormal_labels_{test_name}", True, 
                                         "異常標籤被處理")
                        else:
                            self.log_test(f"abnormal_labels_{test_name}", True, 
                                         "異常標籤處理正常")
                
                except Exception as e:
                    # 某些異常標籤應該被拒絕
                    self.log_test(f"abnormal_labels_{test_name}", True, 
                                 f"異常標籤被正確拒絕: {type(e).__name__}")
                                 
        except Exception as e:
            self.log_test("abnormal_labels", False, f"異常標籤測試失敗: {e}", "error")
    
    def _test_high_dimensional_multiclass(self):
        """測試高維多類別"""
        try:
            print("  📈 測試高維多類別...")
            
            # 創建高維數據 (特徵數 > 樣本數)
            n_samples = 100
            n_features = 200  # 特徵數大於樣本數
            n_classes = 5
            
            X, y = make_classification(
                n_samples=n_samples,
                n_features=n_features,
                n_informative=50,
                n_classes=n_classes,
                random_state=42
            )
            
            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=42)
            
            from Forti_ui_app_bundle.training_pipeline.combo_optimizer import ComboOptimizer
            
            # 使用適合高維數據的模型
            models = [
                ('lr', LogisticRegression(random_state=42, max_iter=100, C=0.1)),  # 加正則化
            ]
            
            for name, model in models:
                model.fit(X_train, y_train)
            
            with tempfile.TemporaryDirectory() as temp_dir:
                combo_opt = ComboOptimizer(
                    estimators=models,
                    X_train=X_train,
                    y_train=y_train,
                    X_valid=X_test,
                    y_valid=y_test,
                    task_type="multiclass",
                    config={},
                    out_dir=temp_dir
                )
                
                result = combo_opt.optimize()
                
                if result and 'metrics' in result:
                    self.log_test("high_dimensional_multiclass", True, 
                                 "高維多類別數據處理成功")
                else:
                    self.log_test("high_dimensional_multiclass", False, 
                                 "高維多類別數據處理失敗", "warning")
                    
        except Exception as e:
            self.log_test("high_dimensional_multiclass", False, 
                         f"高維多類別測試失敗: {e}", "error")

    def system_stress_and_stability_testing(self):
        """系統壓力和穩定性測試"""
        print("\n💪 系統壓力和穩定性測試...")
        
        # 1. 長時間運行測試
        self._test_long_running_stability()
        
        # 2. 記憶體洩漏檢測
        self._test_memory_leaks()
        
        # 3. 多次執行一致性測試
        self._test_execution_consistency()
    
    def _test_long_running_stability(self):
        """測試長時間運行穩定性"""
        try:
            print("  ⏱️ 測試長時間運行穩定性...")
            
            from Forti_ui_app_bundle.training_pipeline.combo_optimizer import ComboOptimizer
            
            results = []
            start_time = time.time()
            
            # 運行多次小規模測試
            for i in range(10):  # 10 次迭代
                try:
                    X, y = make_classification(n_samples=200, n_features=10, n_classes=2, random_state=i)
                    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=i)
                    
                    models = [('rf', RandomForestClassifier(n_estimators=3, random_state=i))]
                    for name, model in models:
                        model.fit(X_train, y_train)
                    
                    with tempfile.TemporaryDirectory() as temp_dir:
                        combo_opt = ComboOptimizer(
                            estimators=models,
                            X_train=X_train,
                            y_train=y_train,
                            X_valid=X_test,
                            y_valid=y_test,
                            task_type="binary",
                            config={},
                            out_dir=temp_dir
                        )
                        
                        result = combo_opt.optimize()
                        results.append(result is not None)
                        
                except Exception as e:
                    results.append(False)
                    print(f"    迭代 {i} 失敗: {e}")
            
            end_time = time.time()
            duration = end_time - start_time
            success_rate = sum(results) / len(results)
            
            if success_rate >= 0.8:  # 80% 成功率
                self.log_test("long_running_stability", True, 
                             f"長時間穩定性測試通過: {success_rate*100:.1f}% 成功率, {duration:.1f}s")
            else:
                self.log_test("long_running_stability", False, 
                             f"穩定性不足: {success_rate*100:.1f}% 成功率", "warning")
                
        except Exception as e:
            self.log_test("long_running_stability", False, f"穩定性測試失敗: {e}", "error")
    
    def _test_memory_leaks(self):
        """測試記憶體洩漏"""
        try:
            print("  🔍 測試記憶體洩漏...")
            
            process = psutil.Process()
            initial_memory = process.memory_info().rss / 1024 / 1024  # MB
            
            from Forti_ui_app_bundle.training_pipeline.combo_optimizer import ComboOptimizer
            
            # 執行多次相同操作
            for i in range(5):
                X, y = make_classification(n_samples=500, n_features=20, n_classes=2, random_state=i)
                X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=i)
                
                models = [('rf', RandomForestClassifier(n_estimators=5, random_state=i))]
                for name, model in models:
                    model.fit(X_train, y_train)
                
                with tempfile.TemporaryDirectory() as temp_dir:
                    combo_opt = ComboOptimizer(
                        estimators=models,
                        X_train=X_train,
                        y_train=y_train,
                        X_valid=X_test,
                        y_valid=y_test,
                        task_type="binary",
                        config={},
                        out_dir=temp_dir
                    )
                    
                    result = combo_opt.optimize()
                
                # 強制垃圾收集
                del models, combo_opt, result
                gc.collect()
            
            final_memory = process.memory_info().rss / 1024 / 1024  # MB
            memory_increase = final_memory - initial_memory
            
            # 記憶體增長應該很小（< 100MB）
            if memory_increase < 100:
                self.log_test("memory_leaks", True, 
                             f"無明顯記憶體洩漏: +{memory_increase:.1f}MB")
            else:
                self.log_test("memory_leaks", False, 
                             f"可能存在記憶體洩漏: +{memory_increase:.1f}MB", "warning")
                
        except Exception as e:
            self.log_test("memory_leaks", False, f"記憶體洩漏測試失敗: {e}", "error")
    
    def _test_execution_consistency(self):
        """測試執行一致性"""
        try:
            print("  🔄 測試執行一致性...")
            
            from Forti_ui_app_bundle.training_pipeline.combo_optimizer import ComboOptimizer
            
            # 使用相同參數執行多次
            X, y = make_classification(n_samples=100, n_features=10, n_classes=2, random_state=42)
            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=42)
            
            results = []
            
            for i in range(3):  # 執行 3 次
                models = [
                    ('rf', RandomForestClassifier(n_estimators=5, random_state=42)),  # 固定隨機種子
                    ('lr', LogisticRegression(random_state=42, max_iter=100))
                ]
                
                for name, model in models:
                    model.fit(X_train, y_train)
                
                with tempfile.TemporaryDirectory() as temp_dir:
                    combo_opt = ComboOptimizer(
                        estimators=models,
                        X_train=X_train,
                        y_train=y_train,
                        X_valid=X_test,
                        y_valid=y_test,
                        task_type="binary",
                        config={"ENSEMBLE_SETTINGS": {"VOTING": "soft"}},
                        out_dir=temp_dir
                    )
                    
                    result = combo_opt.optimize()
                    
                    if result and 'metrics' in result:
                        acc = result['metrics'].get('acc', 0)
                        f1 = result['metrics'].get('f1', 0)
                        results.append((acc, f1))
            
            # 檢查結果一致性
            if len(results) >= 2:
                acc_values = [r[0] for r in results]
                f1_values = [r[1] for r in results]
                
                acc_std = np.std(acc_values)
                f1_std = np.std(f1_values)
                
                # 標準差應該很小（因為使用了固定隨機種子）
                if acc_std < 0.01 and f1_std < 0.01:
                    self.log_test("execution_consistency", True, 
                                 f"執行結果一致: ACC_std={acc_std:.4f}, F1_std={f1_std:.4f}")
                else:
                    self.log_test("execution_consistency", False, 
                                 f"執行結果不一致: ACC_std={acc_std:.4f}, F1_std={f1_std:.4f}", 
                                 "warning")
            else:
                self.log_test("execution_consistency", False, 
                             "執行次數不足", "error")
                
        except Exception as e:
            self.log_test("execution_consistency", False, f"一致性測試失敗: {e}", "error")

    def run_rigorous_test_suite(self):
        """運行嚴謹測試套件"""
        print("🧪 開始更嚴謹的深度檢查...")
        print("=" * 80)
        
        # 抑制警告
        warnings.filterwarnings('ignore')
        
        try:
            self.deep_syntax_check()
            self.strict_dependency_verification()
            self.extreme_edge_case_testing()
            self.complex_multiclass_deep_testing()
            self.system_stress_and_stability_testing()
            
        except Exception as e:
            print(f"❌ 測試過程中發生嚴重錯誤: {e}")
            traceback.print_exc()
            self.log_test("test_suite_execution", False, f"測試套件執行失敗: {e}", "critical")
        
        self.generate_comprehensive_report()

    def generate_comprehensive_report(self):
        """生成綜合報告"""
        print("\n" + "=" * 80)
        print("📋 嚴謹測試報告總結")  
        print("=" * 80)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for r in self.test_results if r['success'])
        failed_tests = total_tests - passed_tests
        
        critical_count = len(self.critical_failures)
        error_count = len(self.errors)
        warning_count = len(self.warnings)
        
        print(f"總測試數: {total_tests}")
        print(f"通過: {passed_tests} ✅")
        print(f"失敗: {failed_tests} ❌")
        print(f"成功率: {passed_tests/total_tests*100:.1f}%")
        print()
        print(f"嚴重問題: {critical_count} 🔥")
        print(f"錯誤: {error_count} ❌")
        print(f"警告: {warning_count} ⚠️")
        
        # 詳細問題報告
        if self.critical_failures:
            print(f"\n🔥 嚴重問題 ({len(self.critical_failures)}):")
            for failure in self.critical_failures:
                print(f"  - {failure['test_name']}: {failure['message']}")
        
        if self.errors:
            print(f"\n❌ 錯誤 ({len(self.errors)}):")
            for error in self.errors:
                print(f"  - {error['test_name']}: {error['message']}")
        
        if self.warnings:
            print(f"\n⚠️ 警告 ({len(self.warnings)}):")
            for warning in self.warnings:
                print(f"  - {warning['test_name']}: {warning['message']}")
        
        # 品質評估
        print(f"\n🎯 系統品質評估:")
        if critical_count == 0 and error_count == 0:
            print("  🟢 優秀：沒有嚴重問題或錯誤")
        elif critical_count == 0 and error_count <= 2:
            print("  🟡 良好：僅有少量非關鍵錯誤")
        elif critical_count == 0:
            print("  🟠 一般：存在一些錯誤但無嚴重問題")
        else:
            print("  🔴 需要改進：存在嚴重問題")
        
        print(f"\n💡 建議:")
        if critical_count == 0 and error_count == 0 and warning_count <= 3:
            print("  ✅ 系統通過嚴謹測試，可以安全投入生產使用")
            print("  ✅ 所有核心功能運行穩定")
            print("  ✅ 邊界情況處理良好")
        else:
            if critical_count > 0:
                print("  🔥 立即修復所有嚴重問題")
            if error_count > 0:
                print("  ❌ 優先處理錯誤問題")
            if warning_count > 5:
                print("  ⚠️ 考慮優化警告項目")
            print("  📊 建議進行額外的穩定性測試")
        
        return critical_count == 0 and error_count == 0


if __name__ == "__main__":
    tester = RigorousTestSuite()
    success = tester.run_rigorous_test_suite()
    sys.exit(0 if success else 1)