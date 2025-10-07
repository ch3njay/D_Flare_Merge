import streamlit as st
import threading
import time
import os
import io
import contextlib
import queue
from . import _ensure_module, apply_dark_theme  # [MODIFIED]

_ensure_module("numpy", "numpy_stub")

_ensure_module("pandas", "pandas_stub")

import sys
from pathlib import Path

# 確保專案根目錄在 Python 路徑中
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

_IMPORT_ERROR_MSG = ""
try:
    from Forti_ui_app_bundle.training_pipeline.pipeline_main import TrainingPipeline
    _TRAINING_PIPELINE_AVAILABLE = True
except ImportError as e1:
    _IMPORT_ERROR_MSG += f"Absolute import failed: {e1}\n"
    try:
        from ..training_pipeline.pipeline_main import TrainingPipeline
        _TRAINING_PIPELINE_AVAILABLE = True
    except ImportError as e2:
        _IMPORT_ERROR_MSG += f"Relative import failed: {e2}\n"
        # 嘗試通過直接添加路徑的方式
        try:
            import os
            forti_path = os.path.join(os.path.dirname(__file__), "..", "..")
            if forti_path not in sys.path:
                sys.path.insert(0, forti_path)
            from Forti_ui_app_bundle.training_pipeline.pipeline_main import TrainingPipeline
            _TRAINING_PIPELINE_AVAILABLE = True
        except ImportError as e3:
            _IMPORT_ERROR_MSG += f"Direct path import failed: {e3}\n"
            _TRAINING_PIPELINE_AVAILABLE = False
        # 提供一個簡單的 fallback，但在 UI 中明確告知用戶
        class TrainingPipeline:
            def __init__(self, *args, **kwargs):
                self.config = {}
                self.task_type = "binary"
                self.optuna_enabled = False
                self.optimize_base = False
                self.optimize_ensemble = False
                self.use_tuned_for_training = True
                
            def run(self, *args, **kwargs):
                raise ImportError("真正的 TrainingPipeline 模組無法載入")


def app() -> None:
    apply_dark_theme()  # [ADDED]
    st.title("Training Pipeline")
    
    # 檢查 TrainingPipeline 是否可用
    if not _TRAINING_PIPELINE_AVAILABLE:
        st.error("⚠️ TrainingPipeline 模組無法載入，此功能暫時不可用。")
        with st.expander("詳細錯誤訊息"):
            st.code(_IMPORT_ERROR_MSG)
            st.code(f"Current working directory: {os.getcwd()}")
            st.code(f"Python path: {sys.path[:3]}...")
            st.code(f"File location: {__file__}")
        return
    
    st.markdown(
        """
        <style>
        .df-training-tip {
            background: color-mix(in srgb, var(--secondaryBackgroundColor) 80%, var(--backgroundColor) 20%);
            border: 1px solid color-mix(in srgb, var(--primaryColor) 28%, transparent);
            color: var(--textColor);
            padding: 0.85rem 1.1rem;
            border-radius: 0.85rem;
            margin-bottom: 1.2rem;
            box-shadow: 0 18px 36px -24px color-mix(in srgb, var(--primaryColor) 45%, transparent);
        }
        .df-training-tip strong {
            color: var(--primaryColor);
        }
        </style>
        <div class="df-training-tip">
            <strong>提示：</strong>訓練狀態會依照 Streamlit 主題自動調整色彩，確保在亮/暗模式下都具備清晰對比。
        </div>
        """,
        unsafe_allow_html=True,
    )

    uploaded_file = st.file_uploader(
        "Upload training CSV",
        type=["csv"],
        help="Max file size: 2GB",
    )
    task_type = st.selectbox("Task type", ["binary", "multiclass"])

    optuna_enabled = st.checkbox("Enable Optuna", value=False)
    optimize_base = False
    optimize_ensemble = False
    use_tuned_for_training = False
    ensemble_mode = "free"

    if optuna_enabled:
        optimize_base = st.checkbox("Optimize base models", value=False)
        optimize_ensemble = st.checkbox("Optimize ensemble", value=False)

        if optimize_base or optimize_ensemble:
            use_tuned_for_training = st.checkbox("Use tuned params for training", value=True)
            if optimize_ensemble and use_tuned_for_training:
                ensemble_mode = st.selectbox(
                    "Ensemble mode",
                    ["free", "fixed"],
                    help="Optuna ensemble search mode",
                )
        else:
            st.info("Optuna disabled because no optimization scope selected.")
            optuna_enabled = False

    if st.button("Run training"):
        if uploaded_file is None:
            st.error("Please upload a CSV file")
            return
        tmp_path = f"uploaded_{uploaded_file.name}"
        with open(tmp_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        pipeline = TrainingPipeline(
            task_type=task_type,
            optuna_enabled=optuna_enabled,
            optimize_base=optimize_base,
            optimize_ensemble=optimize_ensemble,
            use_tuned_for_training=use_tuned_for_training,
        )
        pipeline.config.setdefault("ENSEMBLE_SETTINGS", {})["MODE"] = ensemble_mode
        progress = st.progress(0)
        status = st.empty()
        log_box = st.empty()

        result = {"error": None, "output": None}

        log_queue: "queue.Queue[str]" = queue.Queue()

        class _QueueStream(io.TextIOBase):
            def write(self, buf: str) -> int:  # pragma: no cover - thin wrapper
                log_queue.put(buf)
                return len(buf)

            def flush(self) -> None:  # pragma: no cover - no buffering
                pass

        def _run():
            try:
                stream = _QueueStream()
                with contextlib.redirect_stdout(stream), contextlib.redirect_stderr(stream):
                    result["output"] = pipeline.run(tmp_path)

            except Exception as exc:  # pragma: no cover - runtime failure
                result["error"] = exc

        thread = threading.Thread(target=_run)
        thread.start()
        pct = 0
        log_text = ""
        while thread.is_alive():
            if pct < 95:
                pct += 5
            progress.progress(pct)
            status.text(f"Training in progress... {pct}%")
            while not log_queue.empty():
                log_text += log_queue.get()
            log_box.code(log_text)
            time.sleep(0.1)
        thread.join()
        while not log_queue.empty():
            log_text += log_queue.get()
        log_box.code(log_text)
        if result["error"] is None:
            progress.progress(100)
            status.text("Training finished")
            st.success("Training finished")

            # Debug: 檢查 result 結構
            st.write(f"DEBUG: result keys: {list(result.keys())}")
            st.write(f"DEBUG: result['error']: {result.get('error')}")
            st.write(f"DEBUG: result['output'] type: {type(result.get('output'))}")
            if result.get("output"):
                st.write(f"DEBUG: output keys: {list(result['output'].keys())}")
            
            artifacts_dir = result["output"].get("artifacts_dir") if result["output"] else None
            if artifacts_dir:

                from pathlib import Path
                import os

                st.write(f"DEBUG: artifacts_dir = {artifacts_dir}")
                
                # 檢查目錄是否存在
                if os.path.exists(artifacts_dir):
                    st.write(f"DEBUG: artifacts_dir exists")
                    # 列出目錄內容
                    try:
                        contents = os.listdir(artifacts_dir)
                        st.write(f"DEBUG: artifacts_dir contents: {contents}")
                        
                        models_dir = os.path.join(artifacts_dir, "models")
                        if os.path.exists(models_dir):
                            models_contents = os.listdir(models_dir)
                            st.write(f"DEBUG: models dir contents: {models_contents}")
                        else:
                            st.write("DEBUG: models directory does not exist")
                    except Exception as e:
                        st.write(f"DEBUG: Error listing contents: {e}")
                else:
                    st.write(f"DEBUG: artifacts_dir does not exist")

                model_path = Path(artifacts_dir) / "models" / "ensemble_best.joblib"
                st.write(f"DEBUG: Looking for model at: {model_path}")
                if model_path.exists():

                    with open(model_path, "rb") as f:
                        model_bytes = f.read()
                    st.download_button(
                        "Download ensemble model",
                        model_bytes,
                        file_name="ensemble_best.joblib",
                    )
                    st.info(f"Artifacts saved to: {artifacts_dir}")
                else:
                    st.warning("Model file not found in artifacts directory.")

            else:
                st.warning("No artifacts directory returned.")


        else:
            status.text("Training failed")
            st.error(f"Training failed: {result['error']}")
