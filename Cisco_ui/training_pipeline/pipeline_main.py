"""Cisco ASA Training Pipeline - 整合訓練流程主程式。"""
from __future__ import annotations

import json
import os
import re
import time
import joblib
from typing import Any, Dict, Tuple
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    classification_report,
    confusion_matrix,
    accuracy_score
)

# 導入 Cisco 訓練模組
from .model_builder import ModelBuilder
from .evaluator import Evaluator
from .combo_optimizer import ComboOptimizer


class CiscoTrainingPipeline:
    """Cisco ASA 機器學習訓練管線"""
    
    def __init__(
        self,
        task_type: str = "binary",
        config: Dict[str, Any] | None = None,
    ):
        """
        初始化訓練管線
        
        Args:
            task_type: 訓練任務類型 ("binary" 或 "multiclass")
            config: 自訂配置字典
        """
        self.task_type = task_type
        self.config = config or {}
        
        # 設定預設值
        self.config.setdefault("test_size", 0.2)
        self.config.setdefault("random_state", 42)
        self.config.setdefault("output_dir", "./artifacts")
        
        # 初始化模組
        self.model_builder = ModelBuilder()
        self.evaluator = Evaluator()
        
        # 輸出目錄
        self.out_dir = None
        
    def _prepare_artifacts_dir(self) -> str:
        """建立輸出目錄"""
        root = self.config.get("output_dir", "./artifacts")
        ts = time.strftime("%Y%m%d_%H%M%S")
        out_dir = os.path.join(root, ts)
        os.makedirs(os.path.join(out_dir, "models"), exist_ok=True)
        os.makedirs(os.path.join(out_dir, "reports"), exist_ok=True)
        return out_dir
    
    def _load_data(self, csv_path: str) -> pd.DataFrame:
        """載入訓練資料 - 支持格式自動偵測"""
        print(f"📂 載入資料：{csv_path}")
        
        # 偵測資料格式
        data_format = self._detect_data_format(csv_path)
        print(f"🔍 偵測到資料格式：{data_format}")
        
        if data_format == "compressed":
            print("📦 偵測到壓縮檔案，先解壓縮...")
            extracted_file = self._extract_compressed_file(csv_path)
            if extracted_file:
                # 遞迴檢測解壓後的檔案格式
                return self._load_data(extracted_file)
            else:
                print("❌ 壓縮檔案解壓失敗，嘗試直接解析...")
                df = self._load_csv_with_fallback(csv_path)
        elif data_format == "cisco_asa_log":
            print("🔄 偵測到 Cisco ASA Log 格式，執行 ETL 前處理...")
            df = self._process_cisco_logs(csv_path)
        elif data_format == "csv":
            df = self._load_csv_with_fallback(csv_path)
        else:
            print(f"⚠️ 未知格式 {data_format}，嘗試使用 CSV 解析...")
            df = self._load_csv_with_fallback(csv_path)
        
        # 基本 ETL 轉換
        df = self._apply_basic_etl_transforms(df)
        
        print(f"✅ 資料筆數：{len(df)} rows, {len(df.columns)} columns")
        return df
    
    def _detect_data_format(self, file_path: str) -> str:
        """偵測輸入檔案的資料格式，支援壓縮檔案"""
        import os
        
        # 檢查是否為壓縮檔案
        file_extension = os.path.splitext(file_path)[1].lower()
        if file_extension in ['.gz', '.zip', '.7z', '.rar', '.tar', '.bz2']:
            return "compressed"
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                sample_lines = [f.readline().strip() for _ in range(10)]
            
            # 移除空行
            sample_lines = [line for line in sample_lines if line]
            if not sample_lines:
                return "empty"
            
            # 檢查是否為 Cisco ASA log 格式
            cisco_patterns = [
                r'%ASA-\d+-\d+:',           # ASA syslog 格式
                r'Connection\s+\w+',        # Connection built/teardown
                r'Deny\s+\w+',              # Deny 規則
                r'Built\s+\w+',             # Built connection
                r'Teardown\s+\w+',          # Teardown connection
            ]
            
            cisco_matches = 0
            for line in sample_lines:
                for pattern in cisco_patterns:
                    if re.search(pattern, line):
                        cisco_matches += 1
                        break
            
            # 如果超過30%的行匹配 Cisco 模式
            if cisco_matches / len(sample_lines) > 0.3:
                return "cisco_asa_log"
            
            # 檢查是否為標準 CSV（有逗號且第一行像標題）
            first_line = sample_lines[0]
            if ',' in first_line and not first_line.startswith('%'):
                # 嘗試解析 CSV 標題
                potential_headers = [h.strip() for h in first_line.split(',')]
                if (len(potential_headers) >= 3 and 
                    all(h.isalnum() or '_' in h for h in potential_headers[:3])):
                    return "csv"
            
            return "unknown"
            
        except Exception as e:
            print(f"⚠️ 格式偵測失敗：{e}")
            return "unknown"
    
    def _extract_compressed_file(self, file_path: str) -> str | None:
        """解壓縮檔案並返回解壓後的檔案路徑"""
        import os
        import tempfile
        import zipfile
        import gzip
        import tarfile
        import shutil
        
        file_extension = os.path.splitext(file_path)[1].lower()
        temp_dir = tempfile.mkdtemp()
        
        try:
            if file_extension == '.gz':
                # 處理 .gz 檔案
                output_path = os.path.join(temp_dir, 'extracted_file.txt')
                with gzip.open(file_path, 'rt', encoding='utf-8', 
                               errors='ignore') as gz_file:
                    with open(output_path, 'w', encoding='utf-8') as out_file:
                        shutil.copyfileobj(gz_file, out_file)
                print(f"✅ 成功解壓 .gz 檔案到: {output_path}")
                return output_path
                
            elif file_extension == '.zip':
                # 處理 .zip 檔案
                with zipfile.ZipFile(file_path, 'r') as zip_file:
                    # 取得第一個檔案
                    file_list = zip_file.namelist()
                    if not file_list:
                        print("❌ ZIP 檔案為空")
                        return None
                    
                    first_file = file_list[0]
                    extracted_path = zip_file.extract(first_file, temp_dir)
                    print(f"✅ 成功解壓 .zip 檔案到: {extracted_path}")
                    return extracted_path
                    
            elif file_extension in ['.tar', '.tar.gz', '.tgz']:
                # 處理 .tar 相關檔案
                with tarfile.open(file_path, 'r:*') as tar_file:
                    members = tar_file.getmembers()
                    if not members:
                        print("❌ TAR 檔案為空")
                        return None
                    
                    first_member = members[0]
                    if first_member.isfile():
                        tar_file.extract(first_member, temp_dir)
                        extracted_path = os.path.join(
                            temp_dir, first_member.name
                        )
                        print(f"✅ 成功解壓 .tar 檔案到: {extracted_path}")
                        return extracted_path
                        
            else:
                print(f"⚠️ 不支援的壓縮格式: {file_extension}")
                return None
                
        except Exception as e:
            print(f"❌ 解壓縮失敗: {e}")
            # 清理暫存目錄
            try:
                shutil.rmtree(temp_dir)
            except Exception:
                pass
            return None
    
    def _process_cisco_logs(self, log_path: str) -> pd.DataFrame:
        """處理 Cisco ASA 日誌檔案，轉換為結構化資料"""
        # 導入 ETL 模組
        try:
            from ..etl_pipeline.log_cleaning import step1_process_logs
            from ..etl_pipeline.log_mapping import step2_apply_mappings
            from ..etl_pipeline.feature_engineering import step3_generate_features
        except ImportError as e:
            print(f"❌ 無法導入 ETL 模組：{e}")
            print("📄 嘗試直接讀取為 CSV...")
            return self._load_csv_with_fallback(log_path)
        
        import tempfile
        import os
        
        # 建立暫存目錄
        with tempfile.TemporaryDirectory() as temp_dir:
            step1_out = os.path.join(temp_dir, "step1_cleaned.csv")
            step2_out = os.path.join(temp_dir, "step2_mapped.csv")
            step3_out = os.path.join(temp_dir, "step3_features.csv")
            unique_json = os.path.join(temp_dir, "unique.json")
            mappings_json = os.path.join(temp_dir, "mappings.json")
            
            try:
                # Step 1: 清洗原始日誌
                print("  📋 Step 1: 清洗原始日誌...")
                step1_process_logs(log_path, step1_out, unique_json, batch_id=1, show_progress=False)
                
                # Step 2: 應用映射
                print("  🗺️ Step 2: 應用欄位映射...")
                step2_apply_mappings(step1_out, step2_out, mappings_json, show_progress=False)
                
                # Step 3: 特徵工程
                print("  ⚙️ Step 3: 特徵工程...")
                step3_generate_features(step2_out, step3_out, mappings_json, show_progress=False)
                
                # 載入最終結果
                df = pd.read_csv(step3_out)
                print(f"  ✅ ETL 處理完成，產生 {len(df)} 筆結構化資料")
                return df
                
            except Exception as e:
                print(f"  ❌ ETL 處理失敗：{e}")
                print("  📄 改用直接 CSV 讀取...")
                return self._load_csv_with_fallback(log_path)
    
    def _load_csv_with_fallback(self, csv_path: str) -> pd.DataFrame:
        """使用多種方法載入 CSV 檔案"""
        try:
            # 方法 1: 標準讀取
            return pd.read_csv(csv_path)
        except pd.errors.ParserError:
            try:
                # 方法 2: 使用 Python 引擎，跳過錯誤行
                print("⚠️ CSV 解析錯誤，使用 Python 引擎重試...")
                return pd.read_csv(
                    csv_path, engine='python', 
                    error_bad_lines=False, warn_bad_lines=False
                )
            except Exception:
                try:
                    # 方法 3: 更寬鬆的解析
                    print("⚠️ 使用更寬鬆的 CSV 解析...")
                    return pd.read_csv(
                        csv_path, sep=None, engine='python', 
                        encoding='utf-8', on_bad_lines='skip'
                    )
                except Exception as e:
                    print(f"❌ 所有 CSV 解析方法都失敗：{e}")
                    raise
    
    def _apply_basic_etl_transforms(self, df: pd.DataFrame) -> pd.DataFrame:
        """應用基本的 ETL 轉換"""
        # 處理缺失值
        if df.isna().any().any():
            print("🔧 處理缺失值...")
            df = df.fillna(0)
        
        # 移除完全空白的行
        df = df.dropna(how='all')
        
        # 確保數值欄位格式正確
        numeric_cols = df.select_dtypes(include=['object']).columns
        for col in numeric_cols:
            if df[col].dtype == 'object':
                # 嘗試轉換為數值
                try:
                    df[col] = pd.to_numeric(df[col], errors='ignore')
                except Exception:
                    pass
        
        return df
    
    def _prepare_features(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.Series]:
        """準備特徵和標籤"""
        # 確定目標欄位
        if self.task_type == "binary":
            target_col = "is_attack"
        else:
            target_col = "crlevel"
        
        if target_col not in df.columns:
            raise ValueError(f"❌ 找不到目標欄位：{target_col}")
        
        # 排除目標欄位
        feature_cols = [c for c in df.columns if c not in ["is_attack", "crlevel"]]
        
        X = df[feature_cols].copy()
        y = df[target_col].copy()
        
        # 處理缺失值
        if X.isna().any().any():
            print("⚠️ 偵測到缺失值，使用 0 填充")
            X = X.fillna(0)
        
        print(f"✅ 特徵數量：{len(feature_cols)}")
        print(f"✅ 標籤分佈：\n{y.value_counts()}")
        
        return X, y
    
    def _split_data(
        self, 
        X: pd.DataFrame, 
        y: pd.Series
    ) -> Tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series]:
        """分割訓練集和測試集"""
        test_size = self.config.get("test_size", 0.2)
        random_state = self.config.get("random_state", 42)
        
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, 
            test_size=test_size, 
            random_state=random_state,
            stratify=y
        )
        
        print(f"✅ 訓練集：{len(X_train)} 筆")
        print(f"✅ 測試集：{len(X_test)} 筆")
        
        return X_train, X_test, y_train, y_test
    
    def _train_models(
        self, 
        X_train: pd.DataFrame, 
        y_train: pd.Series
    ) -> Dict[str, Any]:
        """訓練模型"""
        print(f"\n🤖 開始訓練 {self.task_type} 模型...")
        
        # 使用 ModelBuilder 建立和訓練模型
        models = {}
        
        # 訓練 LightGBM
        print("  ⚙️ 訓練 LightGBM...")
        lgb_model = self.model_builder.build_lightgbm(
            X_train, y_train, 
            task_type=self.task_type
        )
        models["LightGBM"] = lgb_model
        
        # 訓練 XGBoost
        print("  ⚙️ 訓練 XGBoost...")
        xgb_model = self.model_builder.build_xgboost(
            X_train, y_train,
            task_type=self.task_type
        )
        models["XGBoost"] = xgb_model
        
        # 訓練 CatBoost
        print("  ⚙️ 訓練 CatBoost...")
        cat_model = self.model_builder.build_catboost(
            X_train, y_train,
            task_type=self.task_type
        )
        models["CatBoost"] = cat_model
        
        print(f"✅ 完成訓練 {len(models)} 個模型")
        return models
    
    def _evaluate_models(
        self,
        models: Dict[str, Any],
        X_test: pd.DataFrame,
        y_test: pd.Series
    ) -> Dict[str, Dict[str, Any]]:
        """評估模型"""
        print("\n📊 評估模型效能...")
        
        results = {}
        for name, model in models.items():
            print(f"  📈 評估 {name}...")
            y_pred = model.predict(X_test)
            
            # 計算指標
            acc = accuracy_score(y_test, y_pred)
            report = classification_report(y_test, y_pred, output_dict=True)
            cm = confusion_matrix(y_test, y_pred)
            
            results[name] = {
                "accuracy": float(acc),
                "classification_report": report,
                "confusion_matrix": cm.tolist(),
                "predictions": y_pred.tolist()
            }
            
            print(f"    ✅ Accuracy: {acc:.4f}")
        
        return results
    
    def _save_models(
        self, 
        models: Dict[str, Any], 
        out_dir: str
    ) -> Dict[str, str]:
        """儲存訓練好的模型"""
        print("\n💾 儲存模型...")
        
        saved_paths = {}
        models_dir = os.path.join(out_dir, "models")
        
        for name, model in models.items():
            # 標準化模型名稱
            model_filename = f"{self.task_type}_{name.lower().replace(' ', '_')}.pkl"
            model_path = os.path.join(models_dir, model_filename)
            
            joblib.dump(model, model_path)
            saved_paths[name] = model_path
            print(f"  ✅ {name}: {model_path}")
        
        return saved_paths
    
    def _save_reports(
        self,
        results: Dict[str, Dict[str, Any]],
        out_dir: str
    ) -> str:
        """儲存評估報告"""
        print("\n📝 儲存評估報告...")
        
        reports_dir = os.path.join(out_dir, "reports")
        report_path = os.path.join(reports_dir, f"{self.task_type}_evaluation.json")
        
        # 準備可序列化的報告
        serializable_results = {}
        for name, result in results.items():
            serializable_results[name] = {
                "accuracy": result["accuracy"],
                "classification_report": result["classification_report"],
                "confusion_matrix": result["confusion_matrix"]
            }
        
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(serializable_results, f, indent=2, ensure_ascii=False)
        
        print(f"  ✅ 報告: {report_path}")
        return report_path
    
    def run(self, csv_path: str) -> Dict[str, Any]:
        """
        執行完整訓練流程
        
        Args:
            csv_path: 訓練資料 CSV 路徑
            
        Returns:
            包含訓練結果的字典
        """
        try:
            # 建立輸出目錄
            self.out_dir = self._prepare_artifacts_dir()
            print(f"📁 輸出目錄：{self.out_dir}\n")
            
            # 1. 載入資料
            df = self._load_data(csv_path)
            
            # 2. 準備特徵
            X, y = self._prepare_features(df)
            
            # 3. 分割資料
            X_train, X_test, y_train, y_test = self._split_data(X, y)
            
            # 4. 訓練模型
            models = self._train_models(X_train, y_train)
            
            # 5. 評估模型
            results = self._evaluate_models(models, X_test, y_test)
            
            # 6. 儲存模型
            model_paths = self._save_models(models, self.out_dir)
            
            # 7. 儲存報告
            report_path = self._save_reports(results, self.out_dir)
            
            # 8. 集成學習（如果配置啟用）
            ensemble_result = None
            if self.config.get("ENABLE_ENSEMBLE", False):
                ensemble_result = self._run_ensemble(models, X_train, y_train, X_test, y_test)
            
            # 找出最佳模型
            best_model_name = max(results.keys(), 
                                 key=lambda k: results[k]["accuracy"])
            best_accuracy = results[best_model_name]["accuracy"]
            
            print("\n✨ 訓練完成！")
            print(f"🏆 最佳模型：{best_model_name} (Accuracy: {best_accuracy:.4f})")
            
            return {
                "success": True,
                "output_dir": self.out_dir,
                "models": models,
                "model_paths": model_paths,
                "results": results,
                "report_path": report_path,
                "best_model": best_model_name,
                "best_accuracy": best_accuracy,
                "ensemble_result": ensemble_result
            }
            
        except Exception as e:
            print(f"❌ 訓練失敗：{str(e)}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "error": str(e)
            }
    
    def _run_ensemble(self, models: Dict[str, Any], X_train, y_train, X_test, y_test) -> Dict[str, Any]:
        """執行集成學習"""
        try:
            print("\n🧩 開始集成學習...")
            
            # 準備集成器
            base_estimators = [(name, model) for name, model in models.items()]
            
            combo_opt = ComboOptimizer(
                estimators=base_estimators,
                X_train=X_train,
                y_train=y_train,
                X_valid=X_test,
                y_valid=y_test,
                task_type=self.task_type,
                config=self.config,
                out_dir=self.out_dir
            )
            
            ensemble_result = combo_opt.optimize()
            print("✅ 集成學習完成！")
            return ensemble_result
            
        except Exception as e:
            print(f"⚠️ 集成學習失敗：{e}")
            return {"success": False, "error": str(e)}


# 向後相容的別名
TrainingPipeline = CiscoTrainingPipeline
