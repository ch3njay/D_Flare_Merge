import streamlit as st
import threading
import time
from ..gpu_etl_pipeliner import run_pipeline
from . import apply_dark_theme  # [ADDED]

try:
    from streamlit_fs_browser import fs_browser
    FS_BROWSER_AVAILABLE = True
except ImportError:
    FS_BROWSER_AVAILABLE = False

def app() -> None:
    apply_dark_theme()  # [ADDED]
    st.title("GPU ETL Pipeline")
    uploaded_files = st.file_uploader(
        "Upload log files",
        type=["csv", "txt", "gz"],
        accept_multiple_files=True,
        help="Max file size: 2GB per file",
    )
    do_clean = st.checkbox("Run cleaning", value=True)
    do_map = st.checkbox("Run mapping", value=True)
    do_fe = st.checkbox("Run feature engineering", value=True)

    # 新增：用跳窗選擇輸出路徑
    out_path = None
    if FS_BROWSER_AVAILABLE:
        st.write("選擇輸出檔案路徑（可瀏覽）")
        out_path = fs_browser(select_files=True, select_directories=False, key="out_path_select")
        if out_path:
            st.session_state["out_path"] = out_path
        else:
            out_path = st.session_state.get("out_path", "engineered_data.csv")
    else:
        out_path = st.text_input("Output CSV path", "engineered_data.csv")
        st.info("如需跳窗選擇，請先安裝 streamlit-fs-browser")

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
