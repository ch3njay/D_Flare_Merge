"""Cisco ASA ETL Pipeline UI 頁面。

此頁面提供 Cisco ASA 防火牆日誌的 ETL 處理介面，支援：
- 上傳 Cisco ASA 格式的日誌檔案（.csv, .txt, .log, .gz）
- 執行兩階段 ETL：清洗 (log_cleaning) → 映射 (log_mapping)
- 顯示處理進度與結果統計
- 下載處理後的資料

Cisco ASA Log 格式特點：
- 使用鍵值對 (key=value) 格式
- 標準欄位：Datetime, SyslogID, Severity, SourceIP, DestinationIP 等
- 與 Fortinet 格式不同，需要專門的解析邏輯
"""
import streamlit as st
import os
import time
import tempfile
from pathlib import Path
from typing import List, Tuple

try:
    from ..etl_pipeliner import run_etl_pipeline
    from . import apply_dark_theme
except ImportError:
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
    from etl_pipeliner import run_etl_pipeline


def _save_uploaded_files(uploaded_files: List) -> List[str]:
    """將上傳的檔案儲存到臨時目錄並返回路徑列表。"""
    temp_dir = tempfile.gettempdir()
    saved_paths = []
    
    for uploaded_file in uploaded_files:
        # 為每個檔案建立唯一的臨時檔案名稱
        timestamp = int(time.time() * 1000)
        temp_path = os.path.join(temp_dir, f"cisco_etl_{timestamp}_{uploaded_file.name}")
        
        with open(temp_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        saved_paths.append(temp_path)
    
    return saved_paths


def _display_file_info(uploaded_files: List) -> None:
    """顯示已上傳檔案的資訊。"""
    st.success(f"✅ 已選擇 {len(uploaded_files)} 個檔案")
    
    with st.expander("📁 查看選擇的檔案"):
        for idx, file in enumerate(uploaded_files, 1):
            file_size = len(file.getvalue()) / 1024 / 1024  # MB
            st.text(f"{idx}. {file.name} ({file_size:.2f} MB)")


def _display_etl_results(outputs, processing_time: float) -> None:
    """顯示 ETL 處理結果。"""
    st.markdown("---")
    st.subheader("📊 處理結果")
    
    # 統計資訊
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Batch ID", outputs.batch_id)
    
    with col2:
        st.metric("處理記錄數", f"{outputs.processed_count:,}")
    
    with col3:
        st.metric("處理時間", f"{processing_time:.2f} 秒")
    
    # 輸出檔案資訊
    st.subheader("📄 輸出檔案")
    
    with st.expander("查看輸出檔案路徑"):
        st.text(f"清洗後檔案 (Step 1): {outputs.step1_csv}")
        st.text(f"預處理檔案 (Step 2): {outputs.step2_csv}")
        st.text(f"唯一值統計: {outputs.unique_json}")
        
        # 檢查檔案是否存在
        if os.path.exists(outputs.step1_csv):
            st.success(f"✅ Step 1 檔案已建立 ({os.path.getsize(outputs.step1_csv) / 1024 / 1024:.2f} MB)")
        
        if os.path.exists(outputs.step2_csv):
            st.success(f"✅ Step 2 檔案已建立 ({os.path.getsize(outputs.step2_csv) / 1024 / 1024:.2f} MB)")
    
    # 提供下載連結
    if os.path.exists(outputs.step2_csv):
        with open(outputs.step2_csv, "rb") as f:
            st.download_button(
                label="📥 下載預處理資料 (Step 2)",
                data=f,
                file_name=f"cisco_preprocessed_{outputs.batch_id}.csv",
                mime="text/csv"
            )


def app() -> None:
    """Cisco ETL Pipeline UI 主函式。"""
    try:
        apply_dark_theme()
    except:
        pass
    
    st.title("🔧 Cisco ASA ETL Pipeline")
    
    # ==================== 檔案上傳區 ====================
    st.subheader("1️⃣ 上傳日誌檔案")
    
    uploaded_files = st.file_uploader(
        "選擇 Cisco ASA 日誌檔案 (支援多檔案選擇)",
        type=["csv", "txt", "log", "gz"],
        accept_multiple_files=True,
        help="支援格式：CSV, TXT, LOG, GZ | "
             "請上傳 Cisco ASA 防火牆的日誌檔案 | "
             "最大檔案大小：2GB"
    )
    
    # 顯示已選擇的檔案
    if uploaded_files:
        _display_file_info(uploaded_files)
    
    # ==================== 輸出設定區 ====================
    st.subheader("2️⃣ 輸出設定")
    
    col1, col2 = st.columns(2)
    
    with col1:
        output_dir = st.text_input(
            "輸出目錄",
            value="./cisco_etl_output",
            help="處理後的檔案將儲存在此目錄"
        )
    
    with col2:
        show_progress = st.checkbox(
            "顯示詳細進度",
            value=True,
            help="在處理過程中顯示進度條"
        )
    
    # ==================== 執行區 ====================
    st.subheader("3️⃣ 執行 ETL")
    
    if not uploaded_files:
        st.warning("⚠️ 請先上傳日誌檔案")
        st.button("🚀 開始處理", disabled=True, key="cisco_etl_disabled_btn")
        return
    
    # 顯示處理資訊
    if len(uploaded_files) > 1:
        st.info(f"📋 將處理 {len(uploaded_files)} 個檔案，目前僅支援處理第一個檔案")
    
    st.success(f"✅ 準備處理：{uploaded_files[0].name}")
    
    # 修復：強制確保primary按鈕樣式正確顯示
    st.markdown("""
    <style>
    /* 強制Primary按鈕樣式 */
    div[data-testid="stButton"] > button[kind="primary"] {
        background-color: #ff4b4b !important;
        border: 1px solid #ff4b4b !important;
        color: white !important;
    }
    div[data-testid="stButton"] > button[kind="primary"]:hover {
        background-color: #ff6c6c !important;
        border: 1px solid #ff6c6c !important;
        color: white !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    if st.button("🚀 開始處理", type="primary", key="cisco_etl_start_btn"):
        # 儲存上傳的檔案
        with st.spinner("📤 正在儲存上傳的檔案..."):
            saved_paths = _save_uploaded_files(uploaded_files)
        
        # 建立輸出目錄
        os.makedirs(output_dir, exist_ok=True)
        
        # 顯示處理進度
        st.markdown("---")
        st.subheader("🔄 處理進度")
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        try:
            # 階段 1: 準備
            status_text.text("📋 初始化 ETL Pipeline...")
            progress_bar.progress(10)
            time.sleep(0.5)
            
            # 階段 2: 執行 ETL
            status_text.text("🔄 執行日誌清洗與映射...")
            progress_bar.progress(30)
            
            start_time = time.time()
            
            # 執行 ETL Pipeline
            outputs = run_etl_pipeline(
                raw_log_path=saved_paths[0],
                output_dir=output_dir,
                show_progress=show_progress
            )
            
            processing_time = time.time() - start_time
            
            progress_bar.progress(90)
            status_text.text("✅ ETL 處理完成")
            time.sleep(0.3)
            
            # 階段 3: 完成
            progress_bar.progress(100)
            status_text.text("🎉 所有處理已完成")
            
            # 顯示結果
            _display_etl_results(outputs, processing_time)
            
            st.balloons()
            
        except Exception as e:
            st.error(f"❌ ETL 處理失敗：{str(e)}")
            st.exception(e)
            
            # 顯示除錯資訊
            with st.expander("🔍 除錯資訊"):
                st.code(f"錯誤類型: {type(e).__name__}")
                st.code(f"錯誤訊息: {str(e)}")
                
                import traceback
                st.code(traceback.format_exc())
        
        finally:
            # 清理臨時檔案
            try:
                for path in saved_paths:
                    if os.path.exists(path):
                        os.remove(path)
            except:
                pass
    
    # ==================== 說明區 ====================
    with st.expander("ℹ️ Cisco ASA Log 格式說明"):
        st.markdown("""
        ### Cisco ASA 日誌格式特點
        
        Cisco ASA 使用鍵值對格式，例如：
        ```
        Datetime=2024-01-01 10:30:45 SyslogID=106023 Severity=4 
        SourceIP=192.168.1.100 SourcePort=51234 
        DestinationIP=8.8.8.8 DestinationPort=443 
        Protocol=tcp Action=Built Duration=120 Bytes=4096
        ```
        
        ### 標準欄位
        - **Datetime**: 日期時間
        - **SyslogID**: Syslog 訊息 ID
        - **Severity**: 嚴重程度 (0-7，數字越小越嚴重)
        - **SourceIP/SourcePort**: 來源 IP/埠號
        - **DestinationIP/DestinationPort**: 目的地 IP/埠號
        - **Protocol**: 通訊協定 (tcp/udp/icmp)
        - **Action**: 動作 (Built/Teardown/Denied)
        - **Duration**: 連線持續時間
        - **Bytes**: 傳輸位元組數
        - **Description**: 描述資訊
        
        ### 與 Fortinet 的差異
        - Fortinet 使用逗號分隔的欄位
        - Cisco ASA 使用空格分隔的鍵值對
        - 欄位名稱和內容格式不同
        - 需要不同的解析邏輯
        """)
    
    with st.expander("📚 使用說明"):
        st.markdown("""
        ### 使用步驟
        
        1. **上傳檔案**：選擇一個或多個 Cisco ASA 日誌檔案
        2. **設定輸出**：指定輸出目錄和進度顯示選項
        3. **開始處理**：點擊「開始處理」按鈕
        4. **查看結果**：處理完成後查看統計資訊和下載結果
        
        ### 注意事項
        
        - 確保上傳的檔案是 Cisco ASA 格式
        - 大型檔案可能需要較長處理時間
        - 處理過程中請勿關閉瀏覽器視窗
        - 建議先用小檔案測試流程
        
        ### 後續步驟
        
        處理完成後，可以使用預處理資料進行：
        - **特徵工程**：使用 GPU ETL 頁面
        - **模型訓練**：使用訓練工具頁面
        - **模型推論**：使用推論頁面
        """)


if __name__ == "__main__":
    app()
