import streamlit as st
import threading
import time

from ui_shared.upload_limits import insert_upload_limit

from ..gpu_etl_pipeliner import run_pipeline
from . import apply_dark_theme  # [ADDED]

ARCHIVE_TYPES = ["zip", "tar", "gz", "bz2", "xz", "7z"]

def app() -> None:
    apply_dark_theme()  # [ADDED]
    st.title("GPU ETL Pipeline")
    uploaded_files = st.file_uploader(
        "Upload log files",
        type=["csv", "txt", "log", *ARCHIVE_TYPES],
        accept_multiple_files=True,
        help=insert_upload_limit(
            "Max file size: {limit} per file。支援 CSV/TXT/LOG 與壓縮檔 (ZIP/TAR/GZ/BZ2/XZ/7Z)。"
        ),
    )
    do_clean = st.checkbox("Run cleaning", value=True)
    do_map = st.checkbox("Run mapping", value=True)
    do_fe = st.checkbox("Run feature engineering", value=True)
    out_path = st.text_input("Output CSV path", "engineered_data.csv")
    if st.button("Run ETL"):
        if not uploaded_files:
            st.error("Please upload at least one file")
            return
        paths = []
        for f in uploaded_files:
            tmp = f"uploaded_{f.name}"
            with open(tmp, "wb") as g:
                g.write(f.getbuffer())
            paths.append(tmp)

        progress = st.progress(0)
        status = st.empty()
        result = {"value": None, "error": None}

        def _run():
            try:
                result["value"] = run_pipeline(
                    paths,
                    out_path=out_path,
                    do_clean=do_clean,
                    do_map=do_map,
                    do_fe=do_fe,
                    quiet=True,
                )
            except Exception as exc:  # pragma: no cover - runtime failure
                result["error"] = exc

        thread = threading.Thread(target=_run)
        thread.start()
        pct = 0
        while thread.is_alive():
            if pct < 95:
                pct += 5
            progress.progress(pct)
            status.text(f"ETL in progress... {pct}%")
            time.sleep(0.1)
        thread.join()
        if result["error"] is None:
            progress.progress(100)
            status.text("ETL completed")
            st.success(f"ETL completed: {result['value']}")
        else:
            status.text("ETL failed")
            st.error(f"ETL failed: {result['error']}")
