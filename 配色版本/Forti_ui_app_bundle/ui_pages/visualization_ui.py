import html

import streamlit as st
from . import _ensure_module, apply_dark_theme  # [MODIFIED]
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
    apply_dark_theme()  # [ADDED]
    st.title("Prediction Visualization")
    st.markdown(
        """
        <style>
        .viz-card {
            margin-top: 1rem;
            padding: 1.25rem 1.5rem;
            border-radius: 18px;
            border: 1px solid var(--muted-border, rgba(148, 163, 184, 0.35));
            background: var(--app-surface-muted, rgba(15, 23, 42, 0.82));
            box-shadow: var(--df-button-shadow, 0 22px 45px -28px rgba(30, 41, 59, 0.55));
        }
        .viz-card--inline {
            display: inline-flex;
            align-items: center;
            gap: 0.65rem;
            margin-top: 0;
            background: var(--app-surface, rgba(15, 23, 42, 0.65));
            border: 1px solid var(--muted-border, rgba(148, 163, 184, 0.35));
            padding: 0.7rem 1rem;
            border-radius: 14px;
            box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.05);
        }
        .viz-card--inline strong {
            color: var(--df-title-color);
        }
        .viz-chart-title {
            font-weight: 600;
            font-size: 1.05rem;
            margin-bottom: 0.85rem;
            color: var(--df-title-color);
        }
        .viz-hint {
            color: var(--df-caption-color);
            font-size: 0.9rem;
            margin-top: 0.35rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

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
        st.markdown(
            f"<div class='viz-card viz-card--inline'>📄 正在檢視：<strong>{html.escape(str(report_path))}</strong></div>",
            unsafe_allow_html=True,
        )

    bin_counts = counts["is_attack"]
    total_events = int(bin_counts.sum())
    attack_events = int(bin_counts.get(1, 0))
    safe_events = int(bin_counts.get(0, 0))
    attack_ratio = (attack_events / total_events * 100) if total_events else 0.0
    safe_ratio = (safe_events / total_events * 100) if total_events else 0.0

    st.markdown("#### 概況總覽")
    stats_cols = st.columns(3)
    stats_cols[0].metric("總事件數", f"{total_events:,}")
    stats_cols[1].metric(
        "攻擊判定",
        f"{attack_events:,}",
        help=f"{attack_ratio:.1f}% of events" if total_events else "尚無資料",
    )
    stats_cols[2].metric(
        "一般流量",
        f"{safe_events:,}",
        help=f"{safe_ratio:.1f}% of events" if total_events else "尚無資料",
    )

    cr_counts = counts.get("crlevel")
    if cr_counts is None:
        cr_counts = pd.Series(dtype=int)

    if not cr_counts.empty:
        if cr_counts.sum() > 0:
            top_level = int(cr_counts.idxmax())
            high_risk = int(cr_counts.loc[cr_counts.index >= 3].sum())
            st.markdown(
                f"<div class='viz-hint'>最高風險等級：<strong>L{top_level}</strong> ・ 高風險事件 {high_risk} 筆</div>",
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                "<div class='viz-hint'>尚未偵測到高風險事件。</div>",
                unsafe_allow_html=True,
            )
    else:
        st.markdown(
            "<div class='viz-hint'>尚未偵測到高風險事件。</div>",
            unsafe_allow_html=True,
        )

    bin_colors = ["#22c55e", "#ef4444"]
    mul_colors = ["#22c55e", "#fde047", "#fb923c", "#f97316", "#ef4444"]

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("<div class='viz-card'>", unsafe_allow_html=True)
        st.markdown("<div class='viz-chart-title'>Binary distribution (bar)</div>", unsafe_allow_html=True)
        fig, ax = plt.subplots(figsize=(4, 3))
        ax.bar(bin_counts.index.astype(str), bin_counts.values, color=bin_colors)
        ax.set_ylabel("事件數")
        st.pyplot(fig, use_container_width=True)
        plt.close(fig)
        st.markdown("</div>", unsafe_allow_html=True)
    with col2:
        st.markdown("<div class='viz-card'>", unsafe_allow_html=True)
        st.markdown("<div class='viz-chart-title'>Binary distribution (pie)</div>", unsafe_allow_html=True)
        fig, ax = plt.subplots(figsize=(4, 3))
        _pie_chart(ax, bin_counts, bin_colors)
        st.pyplot(fig, use_container_width=True)
        plt.close(fig)
        st.markdown("</div>", unsafe_allow_html=True)

    col3, col4 = st.columns(2)
    with col3:
        st.markdown("<div class='viz-card'>", unsafe_allow_html=True)
        st.markdown("<div class='viz-chart-title'>crlevel distribution (bar)</div>", unsafe_allow_html=True)
        fig, ax = plt.subplots(figsize=(4, 3))
        ax.bar(cr_counts.index.astype(str), cr_counts.values, color=mul_colors)
        ax.set_ylabel("事件數")
        st.pyplot(fig, use_container_width=True)
        plt.close(fig)
        st.markdown("</div>", unsafe_allow_html=True)
    with col4:
        st.markdown("<div class='viz-card'>", unsafe_allow_html=True)
        st.markdown("<div class='viz-chart-title'>crlevel distribution (pie)</div>", unsafe_allow_html=True)
        fig, ax = plt.subplots(figsize=(4, 3))
        _pie_chart(ax, cr_counts, mul_colors)
        st.pyplot(fig, use_container_width=True)
        plt.close(fig)
        st.markdown("</div>", unsafe_allow_html=True)

    critical = st.session_state.get("last_critical")
    if critical is not None and not critical.empty:
        st.markdown("#### 高風險事件明細")
        st.markdown("<div class='viz-card'>", unsafe_allow_html=True)
        st.dataframe(critical, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)
