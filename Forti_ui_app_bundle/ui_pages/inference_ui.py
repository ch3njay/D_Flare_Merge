import io
import threading
import time
import tempfile
import os
import streamlit as st
from . import _ensure_module, apply_dark_theme  # [MODIFIED]
_ensure_module("numpy", "numpy_stub")
_ensure_module("pandas", "pandas_stub")
import pandas as pd
import joblib


def _load_model_safe(uploaded_file, model_type="binary"):
    """安全載入模型，處理版本相容性問題"""
    
    def _fix_xgboost_compatibility(xgb_model):
        """修復 XGBoost 模型的版本兼容性問題"""
        try:
            # 移除已廢棄的屬性
            deprecated_attrs = ['use_label_encoder']
            for attr in deprecated_attrs:
                if hasattr(xgb_model, attr):
                    try:
                        delattr(xgb_model, attr)
                        print(f"移除已廢棄屬性: {attr}")
                    except Exception:
                        pass
            # 補上 gpu_id 屬性，避免 CPU-only 環境出錯
            if not hasattr(xgb_model, 'gpu_id'):
                try:
                    xgb_model.gpu_id = -1
                    print("自動補上 gpu_id=-1 以支援 CPU-only 環境")
                except Exception as gpu_e:
                    print(f"gpu_id 屬性補充失敗: {str(gpu_e)}")
            # 補上 predictor 屬性，強制切換到 CPU 推論
            if not hasattr(xgb_model, 'predictor'):
                try:
                    xgb_model.predictor = 'cpu_predictor'
                    print("自動補上 predictor='cpu_predictor' 以支援 CPU-only 環境")
                except Exception as pred_e:
                    print(f"predictor 屬性補充失敗: {str(pred_e)}")
            return xgb_model
        except Exception as e:
            print(f"XGBoost 兼容性修復失敗: {str(e)}")
            return xgb_model
    
    try:
        # 重置檔案指針
        uploaded_file.seek(0)
        
        # 使用 joblib 載入模型
        model = joblib.load(uploaded_file)
        
        # 檢查是否是 XGBoost 模型並處理版本問題
        if hasattr(model, 'get_booster'):
            # 先應用兼容性修復
            model = _fix_xgboost_compatibility(model)
            
            try:
                # 嘗試取得 booster 並測試
                booster = model.get_booster()
                
                # 嘗試進行一個簡單的測試預測來檢查模型是否正常
                import numpy as np
                test_data = np.zeros((1, 10))  # 建立測試數據
                try:
                    _ = model.predict(test_data)
                except Exception:
                    # 嘗試使用 save_model/load_model 修復
                    with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as tmp_file:
                        try:
                            booster.save_model(tmp_file.name)
                            
                            import xgboost as xgb
                            # 根據模型類型選擇正確的類別
                            if 'Classifier' in type(model).__name__:
                                new_model = xgb.XGBClassifier()
                            else:
                                new_model = xgb.XGBRegressor()
                            
                            new_model.load_model(tmp_file.name)
                            
                            # 複製重要屬性
                            for attr in ['classes_', 'n_classes_', '_n_classes', 'feature_names_in_']:
                                if hasattr(model, attr):
                                    setattr(new_model, attr, getattr(model, attr))
                            
                            # 測試修復後的模型
                            _ = new_model.predict(test_data)
                            model = new_model
                            
                        except Exception:
                            return None
                        finally:
                            if os.path.exists(tmp_file.name):
                                os.unlink(tmp_file.name)
                                
            except Exception:
                return None
        
        # 檢查是否是 VotingClassifier 
        elif hasattr(model, 'estimators_'):
            try:
                estimators = getattr(model, 'estimators_', [])
                print(f"VotingClassifier 檢測到，estimators_ 類型: {type(estimators)}, 長度: {len(estimators) if hasattr(estimators, '__len__') else 'N/A'}")
                
                # 安全地處理不同的 estimators_ 結構
                if estimators:
                    # 檢查第一個元素的結構
                    first_item = estimators[0] if len(estimators) > 0 else None
                    if first_item is not None:
                        print(f"第一個估計器類型: {type(first_item)}")
                        
                        # 如果是 tuple 結構 (name, estimator)
                        if isinstance(first_item, tuple) and len(first_item) == 2:
                            for i, (name, estimator) in enumerate(estimators):
                                if hasattr(estimator, 'get_booster'):
                                    # 先修復 XGBoost 兼容性
                                    fixed_estimator = _fix_xgboost_compatibility(estimator)
                                    estimators[i] = (name, fixed_estimator)
                                    # 確保更新到原始模型
                                    model.estimators_[i] = (name, fixed_estimator)
                                    try:
                                        # 簡單測試
                                        import numpy as np
                                        test_data = np.zeros((1, 10))
                                        _ = fixed_estimator.predict(test_data)
                                        print(f"VotingClassifier 中的 XGBoost 估計器 {name} 修復成功")
                                    except Exception as est_error:
                                        print(f"VotingClassifier 中的 XGBoost 估計器 {name} 仍有問題: {str(est_error)}")
                                        # 如果還是有問題，嘗試更深層的修復
                                        try:
                                            # 強制設置缺失的屬性
                                            if not hasattr(fixed_estimator, 'use_label_encoder'):
                                                fixed_estimator.use_label_encoder = False
                                            if not hasattr(fixed_estimator, 'predictor'):
                                                fixed_estimator.predictor = 'cpu_predictor'
                                                print(f"VotingClassifier 中的 XGBoost 估計器 {name} 自動補上 predictor='cpu_predictor'")
                                            _ = fixed_estimator.predict(test_data)
                                            print(f"VotingClassifier 中的 XGBoost 估計器 {name} 強制修復成功")
                                        except Exception as deep_error:
                                            print(f"VotingClassifier 中的 XGBoost 估計器 {name} 深層修復失敗: {str(deep_error)}")
                        
                        # 如果直接是估計器列表
                        elif hasattr(first_item, 'predict'):
                            for i, estimator in enumerate(estimators):
                                if hasattr(estimator, 'get_booster'):
                                    # 先修復 XGBoost 兼容性
                                    fixed_estimator = _fix_xgboost_compatibility(estimator)
                                    estimators[i] = fixed_estimator
                                    # 確保更新到原始模型
                                    model.estimators_[i] = fixed_estimator
                                    try:
                                        import numpy as np
                                        test_data = np.zeros((1, 10))
                                        _ = fixed_estimator.predict(test_data)
                                        print(f"VotingClassifier 中的 XGBoost 估計器 {i} 修復成功")
                                    except Exception as est_error:
                                        print(f"VotingClassifier 中的 XGBoost 估計器 {i} 仍有問題: {str(est_error)}")
                                        # 如果還是有問題，嘗試更深層的修復
                                        try:
                                            # 強制設置缺失的屬性
                                            if not hasattr(fixed_estimator, 'use_label_encoder'):
                                                fixed_estimator.use_label_encoder = False
                                            if not hasattr(fixed_estimator, 'predictor'):
                                                fixed_estimator.predictor = 'cpu_predictor'
                                                print(f"VotingClassifier 中的 XGBoost 估計器 {i} 自動補上 predictor='cpu_predictor'")
                                            _ = fixed_estimator.predict(test_data)
                                            print(f"VotingClassifier 中的 XGBoost 估計器 {i} 強制修復成功")
                                        except Exception as deep_error:
                                            print(f"VotingClassifier 中的 XGBoost 估計器 {i} 深層修復失敗: {str(deep_error)}")
                                            if not hasattr(fixed_estimator, 'use_label_encoder'):
                                                fixed_estimator.use_label_encoder = False
                                            # 再次測試
                                            _ = fixed_estimator.predict(test_data)
                                            print(f"VotingClassifier 中的 XGBoost 估計器 {i} 強制修復成功")
                                        except Exception as deep_error:
                                            print(f"VotingClassifier 中的 XGBoost 估計器 {i} 深層修復失敗: {str(deep_error)}")
                        
                        else:
                            print(f"未知的 estimators_ 結構: {type(first_item)}")
                            
            except Exception as vc_error:
                print(f"處理 VotingClassifier 時出錯: {str(vc_error)}")
                # 不阻止模型載入，繼續使用原始模型
        
        return model
        
    except Exception as e:
        # 記錄錯誤但不使用 Streamlit 函數
        print(f"模型載入失敗: {model_type}, 錯誤: {str(e)}")
        return None


def _get_feature_names(model):
    """取得模型的特徵名稱"""
    features = getattr(model, "feature_names_in_", None)
    if features is None:
        if hasattr(model, "get_booster"):
            try:
                features = model.get_booster().feature_names
            except:
                # 如果取得 feature_names 失敗，返回 None
                features = None
        elif hasattr(model, "feature_names"):
            features = model.feature_names
    return features


def _prepare_df(df, features):
    if features is not None:
        df = df.reindex(columns=features)
    for col in df.columns:
        if pd.api.types.is_bool_dtype(df[col].dtype):
            df[col] = df[col].fillna(False).astype("int8", copy=False)
        else:
            df[col] = (
                pd.to_numeric(df[col], errors="coerce")
                .fillna(0)
                .astype("float32", copy=False)
            )
    return df


def app() -> None:
    apply_dark_theme()  # [ADDED]
    st.title("Model Inference")
    data_file = st.file_uploader(
        "Upload data CSV",
        type=["csv"],
        help="Max file size: 2GB",
    )
    binary_model = st.file_uploader(
        "Upload binary model",
        type=["pkl", "joblib"],
        help="Max file size: 2GB",
    )
    multi_model = st.file_uploader(
        "Upload multiclass model",
        type=["pkl", "joblib"],
        help="Max file size: 2GB",
    )
    col1, col2 = st.columns(2)
    run_binary = col1.button("Run binary inference")
    run_multi = col2.button("Run multiclass inference")

    def run_inference(do_multi: bool) -> None:
        progress = st.progress(0)
        status = st.empty()
        result_holder = {"df": None, "error": None}

        def _run():
            try:
                df = pd.read_csv(data_file)
                
                # 使用安全載入函數載入二元分類模型
                bin_clf = _load_model_safe(binary_model, "二元分類")
                if bin_clf is None:
                    result_holder["error"] = Exception("二元分類模型載入失敗")
                    return
                
                features = _get_feature_names(bin_clf)
                df_bin = _prepare_df(df.copy(), features)
                
                # 安全執行預測
                def _safe_predict(model, data, model_name="模型"):
                    """安全執行預測，處理 XGBoost 版本問題"""
                    try:
                        return model.predict(data)
                    except AttributeError as e:
                        if 'use_label_encoder' in str(e):
                            print(f"{model_name} 遇到 use_label_encoder 問題，嘗試修復...")
                            # 如果是 VotingClassifier，修復所有估計器
                            if hasattr(model, 'estimators_'):
                                for i, est in enumerate(model.estimators_):
                                    if hasattr(est, 'get_booster'):
                                        if not hasattr(est, 'use_label_encoder'):
                                            est.use_label_encoder = False
                                        # 移除可能存在的問題屬性
                                        for attr in ['use_label_encoder']:
                                            if hasattr(est, attr):
                                                try:
                                                    delattr(est, attr)
                                                except:
                                                    pass
                            # 如果是單個 XGBoost 模型
                            elif hasattr(model, 'get_booster'):
                                if not hasattr(model, 'use_label_encoder'):
                                    model.use_label_encoder = False
                                # 移除可能存在的問題屬性
                                for attr in ['use_label_encoder']:
                                    if hasattr(model, attr):
                                        try:
                                            delattr(model, attr)
                                        except:
                                            pass
                            
                            # 重新嘗試預測
                            return model.predict(data)
                        else:
                            raise e
                    except Exception as e:
                        print(f"{model_name} 預測失敗: {str(e)}")
                        raise e
                
                try:
                    bin_pred = _safe_predict(bin_clf, df_bin, "二元分類模型")
                except Exception as e:
                    # 如果預測失敗，嘗試轉換數據類型
                    print(f"預測遇到問題，嘗試數據類型轉換: {str(e)}")
                    # 確保所有數值列為 float32
                    df_converted = df_bin.copy()
                    for col in df_converted.columns:
                        if df_converted[col].dtype == 'object':
                            df_converted[col] = pd.to_numeric(
                                df_converted[col], errors='coerce')
                        df_converted[col] = df_converted[col].astype('float32')
                    df_converted = df_converted.fillna(0)
                    bin_pred = _safe_predict(bin_clf, df_converted, "二元分類模型（轉換後）")
                    df_bin = df_converted  # 使用轉換後的數據
                
                result = pd.DataFrame({"is_attack": bin_pred})
                
                if do_multi:
                    mask = result["is_attack"] == 1
                    if mask.any():
                        # 使用安全載入函數載入多元分類模型
                        mul_clf = _load_model_safe(multi_model, "多元分類")
                        if mul_clf is None:
                            result_holder["error"] = Exception("多元分類模型載入失敗")
                            return
                        
                        m_features = _get_feature_names(mul_clf)
                        df_mul = _prepare_df(df_bin.copy(), m_features)
                        
                        # 安全執行多元預測
                        try:
                            cr_pred = _safe_predict(mul_clf, df_mul.loc[mask], "多元分類模型")
                        except Exception as e:
                            print(f"多元預測遇到問題，嘗試數據類型轉換: {str(e)}")
                            df_mul_converted = df_mul.loc[mask].copy()
                            for col in df_mul_converted.columns:
                                if df_mul_converted[col].dtype == 'object':
                                    df_mul_converted[col] = pd.to_numeric(
                                        df_mul_converted[col], errors='coerce')
                                df_mul_converted[col] = (
                                    df_mul_converted[col].astype('float32'))
                            df_mul_converted = df_mul_converted.fillna(0)
                            cr_pred = _safe_predict(mul_clf, df_mul_converted, "多元分類模型（轉換後）")
                        
                        result.loc[mask, "crlevel"] = cr_pred
                        
                result_holder["df"] = result
            except Exception as exc:  # pragma: no cover - runtime failure
                result_holder["error"] = exc

        thread = threading.Thread(target=_run)
        thread.start()
        pct = 0
        while thread.is_alive():
            if pct < 95:
                pct += 5
            progress.progress(pct)
            status.text(f"Inference in progress... {pct}%")
            time.sleep(0.1)
        thread.join()
        if result_holder["error"] is None:
            progress.progress(100)
            status.text("Inference completed")
            st.session_state["prediction_results"] = result_holder["df"]
            st.dataframe(result_holder["df"])
        else:
            status.text("Inference failed")
            st.error(f"Inference failed: {result_holder['error']}")

    if run_binary:
        if data_file is None or binary_model is None:
            st.error("Please upload data and binary model files")
        else:
            run_inference(do_multi=False)
    if run_multi:
        if data_file is None or binary_model is None or multi_model is None:
            st.error("Please upload data and both model files")
        else:
            run_inference(do_multi=True)
