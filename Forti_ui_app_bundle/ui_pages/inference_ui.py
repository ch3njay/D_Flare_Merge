import threading
import time
import tempfile
import os
from contextlib import suppress
import streamlit as st
import pandas as pd
import joblib
import xgboost as xgb
import numpy as np
from . import _ensure_module, apply_dark_theme  # [MODIFIED]

_ensure_module("numpy", "numpy_stub")
_ensure_module("pandas", "pandas_stub")

xgb.set_config(verbosity=0)

# 常數定義
MAX_FILE_SIZE_MSG = "Max file size: 2GB"


def _load_model_safe(uploaded_file):
    """安全載入模型，處理版本相容性問題"""

    def _reset_file_pointer(file):
        file.seek(0)

    def _load_with_joblib(file):
        return joblib.load(file)

    def _handle_xgboost_model(model):
        if hasattr(model, 'get_booster'):
            model = _fix_xgboost_compatibility(model)
            _test_xgboost_model(model)
        return model

    def _test_xgboost_model(model):
        try:
            test_data = np.zeros((1, 10))
            model.predict(test_data)
        except ValueError:
            _attempt_model_repair(model)

    def _attempt_model_repair(model):
        with tempfile.NamedTemporaryFile(
            suffix='.json', delete=False
        ) as tmp_file:
            try:
                model.get_booster().save_model(tmp_file.name)
                new_model = _reload_xgboost_model(tmp_file.name, model)
                test_data = np.zeros((1, 10))
                new_model.predict(test_data)
                return new_model
            finally:
                if os.path.exists(tmp_file.name):
                    os.unlink(tmp_file.name)

    def _reload_xgboost_model(file_path, old_model):
        if 'Classifier' in type(old_model).__name__:
            new_model = xgb.XGBClassifier()
        else:
            new_model = xgb.XGBRegressor()
        new_model.load_model(file_path)
        attrs = ['classes_', 'n_classes_', '_n_classes', 'feature_names_in_']
        for attr in attrs:
            if hasattr(old_model, attr):
                setattr(new_model, attr, getattr(old_model, attr))
        return new_model

    _reset_file_pointer(uploaded_file)
    model = _load_with_joblib(uploaded_file)
    if hasattr(model, 'get_booster'):
        model = _handle_xgboost_model(model)
    return model


def _get_feature_names(model):
    """取得模型的特徵名稱"""
    features = getattr(model, "feature_names_in_", None)
    if features is None:
        if hasattr(model, "get_booster"):
            try:
                features = model.get_booster().feature_names
            except AttributeError:
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
        help=MAX_FILE_SIZE_MSG,
    )
    binary_model = st.file_uploader(
        "Upload binary model",
        type=["pkl", "joblib"],
        help=MAX_FILE_SIZE_MSG,
    )
    multi_model = st.file_uploader(
        "Upload multiclass model",
        type=["pkl", "joblib"],
        help=MAX_FILE_SIZE_MSG,
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
                bin_clf = _load_model_safe(binary_model)
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
                            msg = f"{model_name} 遇到問題，嘗試修復..."
                            print(msg)
                            # 修復 VotingClassifier 中的 XGBoost 估計器
                            if hasattr(model, 'estimators_'):
                                for est in model.estimators_:
                                    if hasattr(est, 'get_booster'):
                                        if not hasattr(
                                            est, 'use_label_encoder'
                                        ):
                                            est.use_label_encoder = False
                                        # 移除可能存在的問題屬性
                                        for attr in ['use_label_encoder']:
                                            if hasattr(est, attr):
                                                with suppress(AttributeError):
                                                    delattr(est, attr)
                            # 如果是單個 XGBoost 模型
                            elif hasattr(model, 'get_booster'):
                                if not hasattr(model, 'use_label_encoder'):
                                    model.use_label_encoder = False
                                # 移除可能存在的問題屬性
                                for attr in ['use_label_encoder']:
                                    if hasattr(model, attr):
                                        with suppress(AttributeError):
                                            delattr(model, attr)
                            
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
                    model_name = "二元分類模型（轉換後）"
                    bin_pred = _safe_predict(bin_clf, df_converted, model_name)
                    df_bin = df_converted  # 使用轉換後的數據
                
                result = pd.DataFrame({"is_attack": bin_pred})
                
                if do_multi:
                    mask = result["is_attack"] == 1
                    if mask.any():
                        # 使用安全載入函數載入多元分類模型
                        mul_clf = _load_model_safe(multi_model)
                        if mul_clf is None:
                            result_holder["error"] = Exception("多元分類模型載入失敗")
                            return
                        
                        m_features = _get_feature_names(mul_clf)
                        df_mul = _prepare_df(df_bin.copy(), m_features)
                        
                        # 安全執行多元預測
                        try:
                            model_name = "多元分類模型"
                            data_subset = df_mul.loc[mask]
                            cr_pred = _safe_predict(
                                mul_clf, data_subset, model_name
                            )
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
                            model_name = "多元分類模型（轉換後）"
                            cr_pred = _safe_predict(
                                mul_clf, df_mul_converted, model_name
                            )
                        
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


def _fix_xgboost_compatibility(xgb_model):
    """修復 XGBoost 模型的版本兼容性問題"""
    try:
        if not hasattr(xgb_model, 'gpu_id'):
            xgb_model.gpu_id = -1
        if not hasattr(xgb_model, 'predictor'):
            xgb_model.predictor = 'cpu_predictor'
        return xgb_model
    except AttributeError as e:
        print(f"屬性錯誤修復失敗: {e}")
        return xgb_model
    except Exception as e:
        print(f"未知錯誤修復失敗: {e}")
        return xgb_model
