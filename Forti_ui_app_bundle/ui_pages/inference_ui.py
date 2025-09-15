import io
import threading
import time
import streamlit as st
from . import _ensure_module
_ensure_module("numpy", "numpy_stub")
_ensure_module("pandas", "pandas_stub")
import pandas as pd
import joblib


def _get_feature_names(model):
    features = getattr(model, "feature_names_in_", None)
    if features is None:
        if hasattr(model, "get_booster"):
            features = model.get_booster().feature_names
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
                binary_model.seek(0)
                bin_clf = joblib.load(binary_model)
                features = _get_feature_names(bin_clf)
                df_bin = _prepare_df(df.copy(), features)
                bin_pred = bin_clf.predict(df_bin)
                result = pd.DataFrame({"is_attack": bin_pred})
                if do_multi:
                    mask = result["is_attack"] == 1
                    if mask.any():
                        multi_model.seek(0)
                        mul_clf = joblib.load(multi_model)
                        m_features = _get_feature_names(mul_clf)
                        df_mul = _prepare_df(df_bin.copy(), m_features)
                        cr_pred = mul_clf.predict(df_mul.loc[mask])
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
