import streamlit as st
from . import _ensure_module
_ensure_module("numpy", "numpy_stub")
_ensure_module("pandas", "pandas_stub")
import pandas as pd
import matplotlib.pyplot as plt


def _pie_chart(ax, counts, colors):
    ax.pie(
        counts.values,
        labels=counts.index.astype(str),
        colors=colors,
        autopct="%1.1f%%",
        pctdistance=0.8,
        labeldistance=1.1,
        textprops={"fontsize": 10},
        startangle=90,
    )
    ax.axis("equal")


def app() -> None:
    st.title("Prediction Visualization")
    counts = st.session_state.get("last_counts")
    report_path = st.session_state.get("last_report_path")
    if counts is None:
        st.info("No processed data available. Use the Folder Monitor to generate a report.")
        uploaded = st.file_uploader(
            "Upload prediction CSV",
            type=["csv"],
            help="Max file size: 2GB",
        )
        if uploaded is not None:
            df = pd.read_csv(uploaded)
            counts = {
                "is_attack": df["is_attack"].value_counts().reindex([0, 1], fill_value=0),
                "crlevel": df["crlevel"].value_counts().reindex([0, 1, 2, 3, 4], fill_value=0)
                if "crlevel" in df.columns
                else pd.Series(dtype=int),
            }
            st.session_state["last_counts"] = counts
            report_path = uploaded.name
    if counts is None:
        return
    if report_path:
        st.write(f"Showing results for: {report_path}")
    bin_colors = ["green", "red"]
    mul_colors = ["green", "yellowgreen", "gold", "orange", "red"]
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Binary distribution (bar)")
        fig, ax = plt.subplots(figsize=(4, 3))
        ax.bar(counts["is_attack"].index.astype(str), counts["is_attack"].values, color=bin_colors)
        st.pyplot(fig, use_container_width=True)
    with col2:
        st.subheader("Binary distribution (pie)")
        fig, ax = plt.subplots(figsize=(4, 3))
        _pie_chart(ax, counts["is_attack"], bin_colors)
        st.pyplot(fig, use_container_width=True)
    col3, col4 = st.columns(2)
    with col3:
        st.subheader("crlevel distribution (bar)")
        fig, ax = plt.subplots(figsize=(4, 3))
        ax.bar(counts["crlevel"].index.astype(str), counts["crlevel"].values, color=mul_colors)
        st.pyplot(fig, use_container_width=True)
    with col4:
        st.subheader("crlevel distribution (pie)")
        fig, ax = plt.subplots(figsize=(4, 3))
        _pie_chart(ax, counts["crlevel"], mul_colors)
        st.pyplot(fig, use_container_width=True)

    critical = st.session_state.get("last_critical")
    if critical is not None and not critical.empty:
        st.subheader("Critical traffic (crlevel ≥ 4)")
        st.dataframe(critical)
