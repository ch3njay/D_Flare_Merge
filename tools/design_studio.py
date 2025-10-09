"""
D-Flare 設計工作室 - 互動式主題和布局調整工具
"""
import streamlit as st
import json
from pathlib import Path

def render_design_studio():
    """渲染設計工作室介面"""
    st.title("🎨 D-Flare 設計工作室")
    st.markdown("讓我們一起客製化您的儀表板外觀！")
    
    # 建立分頁
    tabs = st.tabs(["🎨 配色方案", "📐 布局調整", "🚀 即時預覽"])
    
    with tabs[0]:
        render_color_palette_editor()
    
    with tabs[1]:
        render_layout_editor()
    
    with tabs[2]:
        render_live_preview()

def render_color_palette_editor():
    """配色方案編輯器 - 從 config.toml 讀取預設值"""
    st.header("配色方案設計")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("主要色彩")
        
        # 主色調選擇（預設值來自 config.toml）
        primary_color = st.color_picker(
            "主要色彩 (按鈕、重點)", "#FF6B35")
        secondary_color = st.color_picker(
            "次要色彩 (輔助元素)", "#1A1F29")
        accent_color = st.color_picker(
            "強調色彩 (警告、提示)", "#42A5F5")
        
        st.subheader("背景色系")
        bg_color = st.color_picker("主背景", "#0F1419")
        surface_color = st.color_picker("卡片背景", "#1A1F29")
        border_color = st.color_picker("邊框顏色", "#2D3748")
        
    with col2:
        st.subheader("文字色彩")
        text_primary = st.color_picker("主要文字", "#E6E8EB")
        text_secondary = st.color_picker("次要文字", "#A0AEC0")
        text_muted = st.color_picker("輔助文字", "#718096")
        
        st.subheader("預設主題風格")
        base_theme = st.selectbox(
            "基礎主題", 
            ["現代企業", "科技藍調", "安全橙調", "自然綠調", "專業灰調"]
        )
        
        if st.button("應用預設風格"):
            apply_preset_theme(base_theme)
    
    # 即時色彩預覽
    st.subheader("色彩搭配預覽")
    preview_color_scheme(primary_color, secondary_color, accent_color, 
                        bg_color, surface_color, text_primary)

def render_layout_editor():
    """布局調整編輯器"""
    st.header("布局結構調整")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("側邊欄設定")
        sidebar_width = st.slider("側邊欄寬度 (px)", 250, 400, 296)
        sidebar_collapsed = st.checkbox("預設收合側邊欄")
        
        st.subheader("卡片佈局")
        card_columns = st.selectbox("每列卡片數量", [2, 3, 4], index=1)
        card_spacing = st.slider("卡片間距 (rem)", 0.5, 2.0, 1.0, 0.1)
        card_radius = st.slider("卡片圓角 (px)", 8, 32, 18, 2)
        
    with col2:
        st.subheader("內容區域")
        content_max_width = st.slider("內容最大寬度 (px)", 800, 1400, 1200)
        content_padding = st.slider("內容邊距 (rem)", 1.0, 4.0, 2.6, 0.2)
        
        st.subheader("響應式設計")
        mobile_breakpoint = st.slider("手機斷點 (px)", 480, 768, 600)
        tablet_breakpoint = st.slider("平板斷點 (px)", 768, 1024, 992)
        
    # 布局預覽
    st.subheader("布局預覽")
    preview_layout(sidebar_width, card_columns, card_spacing, card_radius)

def render_live_preview():
    """即時預覽介面"""
    st.header("即時預覽效果")
    
    # 模擬的儀表板預覽
    st.markdown("""
    <div style="
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 20px;
        padding: 2rem;
        color: white;
        margin: 1rem 0;
    ">
        <h2>🛡️ D-FLARE 統一儀表板</h2>
        <p>威脅偵測與回應平台</p>
    </div>
    """, unsafe_allow_html=True)
    
    # 功能卡片預覽
    cols = st.columns(3)
    
    with cols[0]:
        st.markdown("""
        <div style="
            background: white;
            border: 1px solid #e2e8f0;
            border-radius: 12px;
            padding: 1.5rem;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        ">
            <h4>🔍 威脅偵測</h4>
            <p>即時監控與分析</p>
        </div>
        """, unsafe_allow_html=True)
    
    with cols[1]:
        st.markdown("""
        <div style="
            background: white;
            border: 1px solid #e2e8f0;
            border-radius: 12px;
            padding: 1.5rem;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        ">
            <h4>⚡ 自動回應</h4>
            <p>智慧處理機制</p>
        </div>
        """, unsafe_allow_html=True)
    
    with cols[2]:
        st.markdown("""
        <div style="
            background: white;
            border: 1px solid #e2e8f0;
            border-radius: 12px;
            padding: 1.5rem;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        ">
            <h4>📊 報表分析</h4>
            <p>數據視覺化</p>
        </div>
        """, unsafe_allow_html=True)

def preview_color_scheme(primary, secondary, accent, bg, surface, text):
    """預覽色彩搭配效果"""
    st.markdown(f"""
    <div style="
        background: {bg};
        border: 1px solid {surface};
        border-radius: 16px;
        padding: 1.5rem;
        margin: 1rem 0;
    ">
        <h4 style="color: {text};">色彩搭配示例</h4>
        <div style="display: flex; gap: 1rem; margin: 1rem 0;">
            <div style="
                background: {primary};
                color: white;
                padding: 0.5rem 1rem;
                border-radius: 8px;
                font-weight: 600;
            ">主要按鈕</div>
            <div style="
                background: {secondary};
                color: white;
                padding: 0.5rem 1rem;
                border-radius: 8px;
                font-weight: 600;
            ">次要按鈕</div>
            <div style="
                background: {accent};
                color: white;
                padding: 0.5rem 1rem;
                border-radius: 8px;
                font-weight: 600;
            ">強調元素</div>
        </div>
        <div style="
            background: {surface};
            padding: 1rem;
            border-radius: 8px;
            color: {text};
        ">
            這是卡片內容區域的示例文字
        </div>
    </div>
    """, unsafe_allow_html=True)

def preview_layout(sidebar_width, card_columns, spacing, radius):
    """預覽布局效果"""
    st.markdown(f"""
    <div style="
        border: 2px dashed #cbd5e0;
        border-radius: 8px;
        padding: 1rem;
        margin: 1rem 0;
        display: flex;
        gap: 1rem;
    ">
        <div style="
            background: #f7fafc;
            width: {sidebar_width/4}px;
            height: 200px;
            border-radius: 8px;
            display: flex;
            align-items: center;
            justify-content: center;
            color: #4a5568;
            font-weight: 600;
        ">
            側邊欄<br>{sidebar_width}px
        </div>
        <div style="
            flex: 1;
            display: grid;
            grid-template-columns: repeat({card_columns}, 1fr);
            gap: {spacing}rem;
        ">
            {''.join([f'''
            <div style="
                background: #fff;
                border: 1px solid #e2e8f0;
                border-radius: {radius}px;
                padding: 1rem;
                text-align: center;
                color: #4a5568;
                height: 80px;
                display: flex;
                align-items: center;
                justify-content: center;
            ">卡片 {i+1}</div>
            ''' for i in range(card_columns * 2)])}
        </div>
    </div>
    """, unsafe_allow_html=True)

def apply_preset_theme(theme_name):
    """應用預設主題（對應 config.toml 配色）"""
    presets = {
        "現代企業": {
            "primary": "#2563EB",
            "secondary": "#64748B",
            "accent": "#0EA5E9"
        },
        "科技藍調": {
            "primary": "#3B82F6",
            "secondary": "#06B6D4",
            "accent": "#8B5CF6"
        },
        "安全橙調": {
            "primary": "#FF6B35",  # 當前 D-FLARE 主色
            "secondary": "#DC2626",
            "accent": "#F59E0B"
        },
        "自然綠調": {
            "primary": "#059669",
            "secondary": "#0D9488",
            "accent": "#65A30D"
        },
        "專業灰調": {
            "primary": "#374151",
            "secondary": "#6B7280",
            "accent": "#9CA3AF"
        }
    }
    
    if theme_name in presets:
        st.success(f"已應用 {theme_name} 主題預設！")
        st.info("提示：要永久套用主題，請修改 .streamlit/config.toml")
        return presets[theme_name]

if __name__ == "__main__":
    render_design_studio()