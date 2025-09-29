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

try:
    from training_pipeline.pipeline_main import TrainingPipeline
except ModuleNotFoundError as exc:  # pragma: no cover - local package fallback
    if exc.name != "training_pipeline":
        raise
    from ..training_pipeline import TrainingPipeline

def app() -> None:
    apply_dark_theme()  # [ADDED]
    st.title("Training Pipeline")

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

            artifacts_dir = result["output"].get("artifacts_dir") if result["output"] else None
            if artifacts_dir:

                from pathlib import Path

                model_path = Path(artifacts_dir) / "models" / "ensemble_best.joblib"
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
