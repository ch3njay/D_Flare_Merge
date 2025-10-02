"""
D-Flare 增強主題系統
運用 Streamlit 原生方式進行布局和配色調整
"""
import streamlit as st

def apply_enhanced_theme():
    """應用增強的主題配置，模擬 Settings > Appearance 的效果"""
    
    # 確保 Wide mode 啟用
    if 'wide_mode_applied' not in st.session_state:
        try:
            st.set_page_config(
                page_title="D-FLARE Unified Dashboard", 
                page_icon="🛡️", 
                layout="wide",  # 對應 Settings > Appearance > Wide mode
                initial_sidebar_state="expanded"
            )
            st.session_state.wide_mode_applied = True
        except:
            pass
    
    # 應用深色主題風格的 CSS（對應 Settings > Appearance > Dark）
    st.markdown("""
        <style>
        /* === 基礎變數定義 (模擬 config.toml [theme] 設定) === */
        :root {
            --primary-color: #FF6B35;
            --background-color: #0F1419;
            --secondary-bg-color: #1A1F29;
            --text-color: #E6E8EB;
            --border-color: #2D3748;
            
            --success-color: #4CAF50;
            --warning-color: #FFA726;
            --error-color: #FF4757;
            --info-color: #42A5F5;
        }
        
        /* === 主體背景 === */
        .stApp {
            background-color: var(--background-color);
            color: var(--text-color);
        }
        
        /* === 側邊欄樣式 === */
        section[data-testid="stSidebar"] {
            background-color: #0D1117;
            border-right: 1px solid var(--border-color);
        }
        
        section[data-testid="stSidebar"] .stMarkdown {
            color: var(--text-color);
        }
        
        /* === 主內容區域 === */
        .main .block-container {
            background-color: var(--secondary-bg-color);
            border-radius: 12px;
            border: 1px solid var(--border-color);
            padding: 2rem;
            margin-top: 1rem;
        }
        
        /* === 按鈕樣式 === */
        .stButton > button {
            background: linear-gradient(135deg, var(--primary-color), #FF8A50);
            color: white;
            border: none;
            border-radius: 8px;
            font-weight: 600;
            padding: 0.5rem 1rem;
            transition: all 0.3s ease;
        }
        
        .stButton > button:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 25px rgba(255, 107, 53, 0.4);
        }
        
        /* === 卡片樣式 === */
        .element-container {
            background-color: var(--secondary-bg-color);
            border-radius: 8px;
            padding: 1rem;
            margin: 0.5rem 0;
        }
        
        /* === 選擇框和輸入框 === */
        .stSelectbox > div > div {
            background-color: var(--secondary-bg-color);
            border: 1px solid var(--border-color);
            color: var(--text-color);
        }
        
        .stTextInput > div > div > input {
            background-color: var(--secondary-bg-color);
            border: 1px solid var(--border-color);
            color: var(--text-color);
        }
        
        /* === 標題樣式 === */
        .stMarkdown h1, .stMarkdown h2, .stMarkdown h3 {
            color: var(--text-color);
        }
        
        /* === 品牌卡片 === */
        .brand-hero {
            background: linear-gradient(135deg, var(--primary-color), #2D3748);
            border-radius: 16px;
            padding: 2rem;
            margin: 1rem 0;
            color: white;
            box-shadow: 0 10px 30px rgba(255, 107, 53, 0.3);
        }
        
        /* === 功能卡片 === */
        .feature-card {
            background: var(--secondary-bg-color);
            border: 1px solid var(--border-color);
            border-radius: 12px;
            padding: 1.5rem;
            margin: 0.5rem;
            transition: all 0.3s ease;
        }
        
        .feature-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 12px 35px rgba(255, 107, 53, 0.2);
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
        
        /* === 圖表和數據視覺化 === */
        .stPlotlyChart {
            background-color: var(--secondary-bg-color);
            border-radius: 8px;
            border: 1px solid var(--border-color);
        }
        
        /* === 狀態指示器 === */
        .success-badge {
            background-color: var(--success-color);
            color: white;
            padding: 0.25rem 0.75rem;
            border-radius: 20px;
            font-size: 0.8rem;
            font-weight: 600;
        }
        
        .warning-badge {
            background-color: var(--warning-color);
            color: white;
            padding: 0.25rem 0.75rem;
            border-radius: 20px;
            font-size: 0.8rem;
            font-weight: 600;
        }
        
        .error-badge {
            background-color: var(--error-color);
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
        
        ::-webkit-scrollbar-track {
            background: var(--secondary-bg-color);
        }
        
        ::-webkit-scrollbar-thumb {
            background: var(--primary-color);
            border-radius: 4px;
        }
        
        ::-webkit-scrollbar-thumb:hover {
            background: #FF8A50;
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
    status_badge = render_status_badge(status, "運行中" if status == "success" else "維護中")
    
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