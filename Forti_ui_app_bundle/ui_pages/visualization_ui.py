"""
Fortinet 視覺化 UI 模組
提供數據視覺化和圖表展示功能

注意：matplotlib 圖表顏色（bin_colors, mul_colors）為數據視覺化配色，
與主題系統分離，不需要遷移到 config.toml
"""
import html
import os
import platform

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
from . import _ensure_module, apply_dark_theme  # [MODIFIED]

_ensure_module("numpy", "numpy_stub")
_ensure_module("pandas", "pandas_stub")


def _setup_chinese_font():
    """設定 matplotlib 中文字型支援"""
    system = platform.system()
    if system == "Windows":
        # Windows 系統常見中文字型
        fonts = ["Microsoft YaHei", "SimHei", "SimSun", "KaiTi"]
    elif system == "Darwin":  # macOS
        fonts = ["PingFang TC", "Heiti TC", "STHeiti", "Arial Unicode MS"]
    else:  # Linux
        fonts = ["WenQuanYi Micro Hei", "DejaVu Sans", "Liberation Sans"]
    
    for font in fonts:
        try:
            plt.rcParams['font.sans-serif'] = [font]
            # 測試字型是否可用
            fm.FontProperties(family=font)
            break
        except (OSError, ImportError):
            continue
    
    # 設定負號正常顯示
    plt.rcParams['axes.unicode_minus'] = False


# 初始化中文字型
_setup_chinese_font()


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


# 設定檔案
VIZ_SETTINGS_FILE = "forti_visualization_settings.json"

# 預設設定
DEFAULT_VIZ_SETTINGS = {
    "chart_folder": "",
    "auto_refresh": True,
    "show_png_preview": False
}

# HTML常數
VIZ_CARD_OPEN = "<div class='viz-card'>"
VIZ_CARD_CLOSE = "</div>"

# 圖表檔案對應
CHART_FILES = {
    "二元長條圖": "binary_bar.png",
    "二元圓餅圖": "binary_pie.png",
    "多元長條圖": "multiclass_bar.png",
    "多元圓餅圖": "multiclass_pie.png"
}


def _load_viz_settings():
    """載入可視化設定"""
    if "forti_viz_settings" not in st.session_state:
        try:
            import json
            if os.path.exists(VIZ_SETTINGS_FILE):
                with open(VIZ_SETTINGS_FILE, 'r', encoding='utf-8') as f:
                    loaded = json.load(f)
                    st.session_state["forti_viz_settings"] = {**DEFAULT_VIZ_SETTINGS, **loaded}
            else:
                st.session_state["forti_viz_settings"] = DEFAULT_VIZ_SETTINGS.copy()
        except (FileNotFoundError, json.JSONDecodeError):
            st.session_state["forti_viz_settings"] = (
                DEFAULT_VIZ_SETTINGS.copy())
    return st.session_state["forti_viz_settings"]


def _save_viz_settings(data):
    """儲存可視化設定"""
    st.session_state["forti_viz_settings"] = data
    try:
        import json
        with open(VIZ_SETTINGS_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        st.success("✅ 可視化設定已儲存")
    except (IOError, PermissionError) as e:
        st.error(f"❌ 設定儲存失敗：{e}")


def app() -> None:
    apply_dark_theme()  # [ADDED]
    st.title("📊 Prediction Visualization")
    
    # 載入設定
    settings = _load_viz_settings()
    
    # 設定面板
    with st.expander("🔧 可視化設定", expanded=False):
        chart_folder = st.text_input(
            "圖表檔案資料夾",
            value=settings.get("chart_folder", ""),
            help="指定PNG圖表檔案的存放資料夾"
        )
        
        show_png_preview = st.checkbox(
            "顯示PNG圖片預覽",
            value=settings.get("show_png_preview", False),
            help="啟用預生成PNG圖片的預覽功能"
        )
        
        auto_refresh = st.checkbox(
            "自動重新整理",
            value=settings.get("auto_refresh", True),
            help="當有新資料時自動更新圖表"
        )
        
        # 儲存設定
        if st.button("💾 儲存可視化設定"):
            new_settings = {
                "chart_folder": chart_folder,
                "show_png_preview": show_png_preview,
                "auto_refresh": auto_refresh
            }
            _save_viz_settings(new_settings)
    
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

    # 檢查是否需要自動同步更新
    if st.session_state.get("visualization_needs_update", False):
        st.session_state.visualization_needs_update = False
        if st.session_state.get("visualization_last_update"):
            st.success("🔄 視覺化已自動同步更新")

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
        fig, ax = plt.subplots(figsize=(6, 4))
        ax.bar(bin_counts.index.astype(str), bin_counts.values, color=bin_colors)
        ax.set_title("二元分類分佈 ", fontsize=14, pad=20)
        ax.set_xlabel("分類標籤 (0: 正常, 1: 攻擊)", fontsize=10)
        ax.set_ylabel("事件數量", fontsize=10)
        plt.tight_layout()
        st.pyplot(fig)
        plt.close(fig)
        st.markdown("<div class='viz-description'>📊 顯示攻擊與正常事件的數量分佈對比，方便識別資料平衡性</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
    with col2:
        st.markdown("<div class='viz-card'>", unsafe_allow_html=True)
        fig, ax = plt.subplots(figsize=(4, 3))
        _pie_chart(ax, bin_counts, bin_colors)
        ax.set_title("二元分類分佈 ", fontsize=14, pad=20)
        plt.tight_layout()
        st.pyplot(fig, use_container_width=True)
        plt.close(fig)
        st.markdown("<div class='viz-description'>🥧 以百分比形式顯示攻擊事件佔總事件的比例</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    col3, col4 = st.columns(2)
    with col3:
        st.markdown("<div class='viz-card'>", unsafe_allow_html=True)
        fig, ax = plt.subplots(figsize=(6, 4))
        level_labels = [f"L{i}" for i in range(5)]
        ax.bar(level_labels, cr_counts.values, color=mul_colors)
        ax.set_title("風險等級分佈 ", fontsize=14, pad=20)
        ax.set_xlabel("風險等級 (L0: 最低, L4: 最高)", fontsize=10)
        ax.set_ylabel("事件數量", fontsize=10)
        plt.tight_layout()
        st.pyplot(fig)
        plt.close(fig)
        st.markdown("<div class='viz-description'>📈 展示不同風險等級事件的分佈情況，協助優先處理高風險事件</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
    with col4:
        st.markdown("<div class='viz-card'>", unsafe_allow_html=True)
        fig, ax = plt.subplots(figsize=(4, 3))
        _pie_chart(ax, cr_counts, mul_colors)
        ax.set_title("風險等級分佈 ", fontsize=14, pad=20)
        plt.tight_layout()
        st.pyplot(fig, use_container_width=True)
        plt.close(fig)
        st.markdown("<div class='viz-description'>🎯 以百分比顯示各風險等級的佔比</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    critical = st.session_state.get("last_critical")
    if critical is not None and not critical.empty:
        st.markdown("#### 高風險事件明細")
        st.markdown("<div class='viz-card'>", unsafe_allow_html=True)
        st.dataframe(critical, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    # PNG圖片預覽功能（類似Cisco版本）
    if settings.get("show_png_preview", False):
        st.markdown("---")
        st.markdown("#### 📷 預生成圖表預覽")
        
        chart_folder = settings.get("chart_folder", "")
        if chart_folder:
            # 圖表選擇按鈕
            col1, col2, col3, col4 = st.columns(4)
            buttons = list(CHART_FILES.keys())
            cols = [col1, col2, col3, col4]
            
            for col, label in zip(cols, buttons):
                if col.button(label):
                    st.session_state["forti_selected_chart"] = label
            
            # 顯示選中的圖表
            selected = st.session_state.get("forti_selected_chart", buttons[0])
            filename = CHART_FILES[selected]
            st.markdown(f"##### 目前檢視：{selected}")
            
            chart_path = os.path.join(chart_folder, filename)
            if os.path.exists(chart_path):
                st.image(chart_path, caption=f"{selected} ({chart_path})", use_column_width=True)
            else:
                st.warning(f"找不到圖表檔案：{chart_path}")
                st.info("請確認圖表資料夾路徑是否正確，或生成相應的PNG圖表檔案。")
        else:
            st.info("請在設定中指定圖表檔案資料夾路徑。")
