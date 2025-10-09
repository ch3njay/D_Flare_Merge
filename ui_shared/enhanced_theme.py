"""
D-Flare 增強主題系統
運用 Streamlit 原生 theme 配置（.streamlit/config.toml）進行布局和配色調整
所有顏色由 Streamlit Settings > Appearance 控制，支援 Light/Dark/Custom 切換

例外：品牌識別元素（英雄卡片、側邊欄品牌選擇）使用固定品牌配色以保持視覺識別一致性
- Fortinet: 橘紅色漸層 (#f97316 → #ef4444)
- Cisco: 青藍色漸層 (#38bdf8 → #2563eb)
"""
import streamlit as st


# 測試相容性別名
def apply_custom_theme():
    """別名函數，用於測試相容性"""
    return apply_enhanced_theme()


def apply_enhanced_theme():
    """應用增強的主題配置，使用 Streamlit 原生 theme 變數（從 config.toml）"""

    # 確保 Wide mode 啟用
    if 'wide_mode_applied' not in st.session_state:
        try:
            st.set_page_config(
                page_title="D-FLARE Unified Dashboard",
                page_icon="🛡️",
                layout="wide",
                initial_sidebar_state="expanded"
            )
            st.session_state.wide_mode_applied = True
        except Exception:
            pass
    
    # 應用增強樣式（僅增強 layout 和效果，不覆蓋 Streamlit 主題顏色）
    st.markdown("""
        <style>
        /* ============================================================
           D-FLARE 增強主題樣式
           僅提供 layout、動畫、特殊效果增強
           顏色完全由 Streamlit Settings > Appearance 控制
        ============================================================ */
        
        /* === 側邊欄樣式增強 === */
        section[data-testid="stSidebar"] {
            background: linear-gradient(180deg,
                var(--background-color) 0%,
                var(--secondary-background-color) 100%);
        }
        
        /* === 主內容區域布局 === */
        .main .block-container {
            border-radius: 12px;
            padding: 2rem;
            margin-top: 1rem;
        }
        
        /* === 按鈕增強樣式（超強視覺效果） === */
        .stButton > button,
        button[kind="primary"],
        button[kind="secondary"] {
            background: linear-gradient(135deg,
                var(--primary-color),
                color-mix(in srgb, var(--primary-color) 85%, white));
            border: 2px solid var(--primary-color);
            border-radius: 12px;
            font-weight: 600;
            padding: 0.5rem 1rem;
            transition: all 0.3s ease;
            box-shadow: 0 4px 12px
                color-mix(in srgb, var(--primary-color) 35%, transparent),
                0 2px 4px rgba(0, 0, 0, 0.1),
                inset 0 1px 0 rgba(255, 255, 255, 0.2);
            color: white;
            text-shadow: 0 1px 2px rgba(0, 0, 0, 0.2);
        }
        
        .stButton > button:hover,
        button[kind="primary"]:hover,
        button[kind="secondary"]:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 25px
                color-mix(in srgb, var(--primary-color) 40%, transparent);
        }
        
        /* === 卡片布局 === */
        .element-container {
            border-radius: 8px;
            padding: 1rem;
            margin: 0.5rem 0;
        }
        
        /* === 選擇框和輸入框增強 === */
        .stSelectbox > div > div,
        .stTextInput > div > div > input {
            border-radius: 8px;
        }
        
        /* === 品牌卡片增強 === */
        .brand-hero {
            background: linear-gradient(135deg,
                var(--primary-color) 0%,
                var(--secondary-background-color) 100%);
            border-radius: 16px;
            padding: 2rem;
            margin: 1rem 0;
            box-shadow: 0 10px 30px
                color-mix(in srgb, var(--primary-color) 30%, transparent);
        }
        
        /* === 功能卡片 === */
        .feature-card {
            border-radius: 12px;
            padding: 1.5rem;
            margin: 0.5rem;
            transition: all 0.3s ease;
        }
        
        .feature-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 12px 35px
                color-mix(in srgb, var(--primary-color) 20%, transparent);
            border-color: var(--primary-color);
        }
        
        /* === 響應式設計 === */
        @media (max-width: 768px) {
            .main .block-container {
                padding: 1rem;
                margin-top: 0.5rem;
            }
            
            .brand-hero {
                padding: 1.5rem;
                text-align: center;
            }
        }
        
        /* === 圖表容器增強 === */
        .stPlotlyChart {
            border-radius: 8px;
        }
        
        /* === 狀態指示器（使用主題 color palette）=== */
        .success-badge {
            background-color: var(--green-color);
            color: white;
            padding: 0.25rem 0.75rem;
            border-radius: 20px;
            font-size: 0.8rem;
            font-weight: 600;
        }
        
        .warning-badge {
            background-color: var(--yellow-color);
            color: white;
            padding: 0.25rem 0.75rem;
            border-radius: 20px;
            font-size: 0.8rem;
            font-weight: 600;
        }
        
        .error-badge {
            background-color: var(--red-color);
            color: white;
            padding: 0.25rem 0.75rem;
            border-radius: 20px;
            font-size: 0.8rem;
            font-weight: 600;
        }
        
        /* === 隱藏預設元素 === */
        #MainMenu, header, footer {
            visibility: hidden;
        }
        
        /* === 自訂滾動條 === */
        ::-webkit-scrollbar {
            width: 8px;
            height: 8px;
        }
        
        ::-webkit-scrollbar-thumb {
            background: var(--primary-color);
            border-radius: 4px;
        }
        
        ::-webkit-scrollbar-thumb:hover {
            background: color-mix(in srgb, var(--primary-color) 85%, white);
        }
        </style>
    """, unsafe_allow_html=True)


def render_enhanced_sidebar():
    """渲染增強版側邊欄"""
    with st.sidebar:
        st.markdown("""
            <div style="text-align: center; padding: 1rem 0;">
                <h2 style="color: #FF6B35; margin: 0;">🛡️ D-FLARE</h2>
                <p style="color: #E6E8EB; margin: 0.5rem 0;">統一威脅分析平台</p>
            </div>
        """, unsafe_allow_html=True)

        return st.selectbox(
            "選擇品牌模組",
            ["Fortinet", "Cisco"],
            key="brand_selection"
        )


def render_status_badge(status, text):
    """渲染狀態標籤"""
    badge_class = f"{status}-badge"
    return f'<span class="{badge_class}">{text}</span>'


def render_feature_card(icon, title, description, status="success"):
    """渲染功能卡片"""
    status_text = "運行中" if status == "success" else "維護中"
    status_badge = render_status_badge(status, status_text)

    return f"""
    <div class="feature-card">
        <h3 style="margin-top: 0; color: #FF6B35;">{icon} {title}</h3>
        <p style="margin: 0.5rem 0; color: #E6E8EB;">{description}</p>
        <div style="margin-top: 1rem;">
            {status_badge}
        </div>
    </div>
    """


if __name__ == "__main__":
    apply_enhanced_theme()
    st.title("🎨 D-Flare 增強主題測試")
    
    brand = render_enhanced_sidebar()
    
    st.markdown(f"""
        <div class="brand-hero">
            <h1>歡迎使用 {brand} 安全平台</h1>
            <p>現代化威脅偵測與回應系統</p>
        </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown(render_feature_card(
            "🔍", "威脅偵測", "即時監控與分析可疑活動", "success"
        ), unsafe_allow_html=True)

    with col2:
        st.markdown(render_feature_card(
            "⚡", "自動回應", "智慧化威脅處理機制", "success"
        ), unsafe_allow_html=True)

    with col3:
        st.markdown(render_feature_card(
            "📊", "報表分析", "comprehensive 數據視覺化", "warning"
        ), unsafe_allow_html=True)
