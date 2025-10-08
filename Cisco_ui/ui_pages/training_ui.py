"""Cisco ASA Training UI - 模型訓練介面"""
import streamlit as st
import threading
import time
import os
import tempfile
from pathlib import Path

# 確保專案根目錄在 Python 路徑中
import sys
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

# 導入主題設定
try:
    from . import apply_dark_theme
except ImportError:
    def apply_dark_theme():
        pass

# 導入訓練管線
_TRAINING_PIPELINE_AVAILABLE = False
_IMPORT_ERROR_MSG = ""

try:
    from Cisco_ui.training_pipeline.pipeline_main import CiscoTrainingPipeline
    _TRAINING_PIPELINE_AVAILABLE = True
except ImportError as e1:
    _IMPORT_ERROR_MSG += f"絕對導入失敗: {e1}\n"
    try:
        from ..training_pipeline.pipeline_main import CiscoTrainingPipeline
        _TRAINING_PIPELINE_AVAILABLE = True
    except ImportError as e2:
        _IMPORT_ERROR_MSG += f"相對導入失敗: {e2}\n"
        _TRAINING_PIPELINE_AVAILABLE = False


def app() -> None:
    """訓練工具主介面"""
    apply_dark_theme()
    
    st.title("🤖 Cisco ASA 模型訓練")
    
    # 檢查訓練管線是否可用
    if not _TRAINING_PIPELINE_AVAILABLE:
        st.error("⚠️ 訓練管線模組無法載入，此功能暫時不可用。")
        with st.expander("詳細錯誤訊息"):
            st.code(_IMPORT_ERROR_MSG)
            st.code(f"Current working directory: {os.getcwd()}")
            st.code(f"Python path: {sys.path[:3]}...")
        return
    
    # 介面說明
    st.info(
        "📚 **訓練工具說明**\n\n"
        "此工具可協助您訓練二元分類（攻擊/正常）或多元分類（風險等級）模型。\n"
        "請上傳包含特徵欄位和標籤的 CSV 檔案。"
    )
    
    # 檔案上傳
    st.subheader("1️⃣ 上傳訓練資料")
    uploaded_files = st.file_uploader(
        "選擇訓練資料檔案 (支援多檔案選擇)",
        type=["csv", "txt", "log", "gz", "zip"],
        accept_multiple_files=True,
        help="支援格式：CSV, TXT, LOG 及壓縮檔 (.gz, .zip) | "
             "請上傳包含特徵和標籤（is_attack 或 crlevel）的資料檔案"
    )
    
    # 顯示已選擇的檔案
    if uploaded_files:
        st.success(f"✅ 已選擇 {len(uploaded_files)} 個檔案")
        with st.expander("📁 查看選擇的檔案"):
            for idx, file in enumerate(uploaded_files, 1):
                file_size = len(file.getvalue()) / 1024 / 1024  # MB
                st.text(f"{idx}. {file.name} ({file_size:.2f} MB)")
    
    # 訓練參數設定
    st.subheader("2️⃣ 訓練參數設定")
    
    col1, col2 = st.columns(2)
    
    with col1:
        task_type = st.selectbox(
            "任務類型",
            ["binary", "multiclass"],
            format_func=lambda x: "二元分類（攻擊偵測）" if x == "binary" else "多元分類（風險等級）",
            help="選擇訓練任務類型"
        )
    
    with col2:
        test_size = st.slider(
            "測試集比例",
            min_value=0.1,
            max_value=0.5,
            value=0.2,
            step=0.05,
            help="用於評估模型的資料比例"
        )
    
    # 模型閾值設定
    st.subheader("🎯 模型閾值調整")
    threshold = st.slider(
        "決策閾值 (Decision Threshold)",
        min_value=0.0,
        max_value=1.0,
        value=0.5,
        step=0.01,
        help="調整模型的決策閾值，影響分類的敏感度與特異性"
    )
    
    # 進階設定
    with st.expander("🔧 進階設定"):
        random_state = st.number_input(
            "隨機種子",
            min_value=0,
            value=42,
            help="設定隨機種子以確保結果可重現"
        )
        
        output_dir = st.text_input(
            "輸出目錄",
            value="./artifacts",
            help="訓練結果和模型的儲存位置"
        )
    
    # 訓練按鈕
    st.subheader("3️⃣ 開始訓練")
    
    if not uploaded_files:
        st.warning("⚠️ 請先上傳訓練資料")
        st.button("🚀 開始訓練", disabled=True)
        return
    
    # 處理多檔案選擇
    if len(uploaded_files) > 1:
        st.info(f"📋 偵測到 {len(uploaded_files)} 個檔案，將使用第一個檔案進行訓練：**{uploaded_files[0].name}**")
    
    uploaded_file = uploaded_files[0]
    
    # 顯示檔案資訊
    st.success(f"✅ 使用檔案：{uploaded_file.name}")
    
    if st.button("🚀 開始訓練", type="primary"):
        # 儲存上傳的檔案到臨時目錄
        temp_dir = tempfile.gettempdir()
        temp_path = Path(temp_dir) / uploaded_file.name
        
        with open(temp_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        # 建立訓練配置
        config = {
            "test_size": test_size,
            "random_state": random_state,
            "output_dir": output_dir,
            "threshold": threshold
        }
        
        # 建立進度顯示
        st.markdown("---")
        st.subheader("📊 訓練進度")
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        log_container = st.container()
        
        # 執行訓練
        with log_container:
            status_text.text("🔄 初始化訓練管線...")
            progress_bar.progress(10)
            
            try:
                # 建立訓練管線
                pipeline = CiscoTrainingPipeline(
                    task_type=task_type,
                    config=config
                )
                
                status_text.text("📂 載入訓練資料...")
                progress_bar.progress(20)
                time.sleep(0.5)
                
                # 執行訓練（同步執行以顯示進度）
                with st.spinner("🤖 訓練模型中..."):
                    results = pipeline.run(str(temp_path))
                
                progress_bar.progress(100)
                
                # 顯示訓練結果
                if results.get("success"):
                    st.success("✅ 訓練完成！")
                    
                    # 顯示結果摘要
                    st.markdown("---")
                    st.subheader("🎯 訓練結果")
                    
                    # 最佳模型資訊
                    best_model = results.get("best_model")
                    best_accuracy = results.get("best_accuracy", 0)
                    
                    st.metric(
                        label="🏆 最佳模型",
                        value=best_model,
                        delta=f"準確率: {best_accuracy:.2%}"
                    )
                    
                    # 模型效能比較
                    st.subheader("📈 模型效能比較")
                    model_results = results.get("results", {})
                    
                    # 建立效能比較表
                    perf_data = []
                    for model_name, result in model_results.items():
                        perf_data.append({
                            "模型": model_name,
                            "準確率": f"{result['accuracy']:.4f}"
                        })
                    
                    if perf_data:
                        st.table(perf_data)
                    
                    # 儲存路徑
                    st.subheader("💾 儲存位置")
                    output_dir = results.get("output_dir")
                    st.info(f"📁 輸出目錄：`{output_dir}`")
                    
                    # 模型檔案路徑
                    model_paths = results.get("model_paths", {})
                    if model_paths:
                        with st.expander("查看模型檔案路徑"):
                            for model_name, path in model_paths.items():
                                st.code(f"{model_name}: {path}")
                    
                    # 報告路徑
                    report_path = results.get("report_path")
                    if report_path:
                        st.caption(f"📝 評估報告：`{report_path}`")
                    
                    # 下載提示
                    st.markdown("---")
                    st.info(
                        "💡 **提示**：訓練好的模型已儲存到輸出目錄，"
                        "您可以在「模型推論」頁面使用這些模型進行預測。"
                    )
                    
                else:
                    error_msg = results.get("error", "未知錯誤")
                    st.error(f"❌ 訓練失敗：{error_msg}")
                
            except Exception as e:
                error_str = str(e)
                st.error(f"❌ 訓練過程發生錯誤：{error_str}")
                
                # 檢查是否是 CSV 格式錯誤
                if "Error tokenizing data" in error_str or "Expected" in error_str and "fields" in error_str:
                    st.markdown("---")
                    st.subheader("🔍 CSV 格式診斷")
                    st.warning(
                        "檢測到 CSV 格式問題。這通常是由於：\n"
                        "- 某些行的欄位數量不一致\n"
                        "- 數據中包含未轉義的分隔符（如逗號）\n"
                        "- 引號格式不正確"
                    )
                    
                    with st.expander("🛠️ 建議的解決方案"):
                        st.markdown("""
                        **1. 檢查文件格式**
                        - 使用文本編輯器打開 CSV 文件
                        - 檢查第22行（或錯誤提到的行數）
                        - 確認每行的欄位數量是否一致
                        
                        **2. 修復常見問題**
                        - 如果文本欄位包含逗號，請用雙引號包圍
                        - 如果有換行符在文本中，請移除或替換
                        - 確保所有行的欄位數量相同
                        
                        **3. 使用工具修復**
                        - 可以使用 Excel 打開並重新保存為 CSV 格式
                        - 或使用專門的 CSV 清理工具
                        
                        **4. 測試建議**
                        - 先用較小的數據集（如前100行）進行測試
                        - 確認格式正確後再使用完整數據集
                        """)
                        
                        # 提供簡單的修復工具
                        st.markdown("**快速修復工具：**")
                        if st.button("🔧 嘗試自動修復 CSV 格式"):
                            try:
                                import pandas as pd
                                
                                # 嘗試用容錯模式重新讀取
                                try:
                                    df_fixed = pd.read_csv(
                                        temp_path,
                                        error_bad_lines=False,
                                        warn_bad_lines=False,
                                        on_bad_lines='skip'
                                    )
                                    st.success(f"✅ 自動修復成功！載入了 {len(df_fixed)} 行數據")
                                    st.info("請重新點擊「開始訓練」按鈕")
                                except Exception:
                                    df_fixed = pd.read_csv(
                                        temp_path,
                                        sep=None,
                                        engine='python',
                                        quoting=3,
                                        skipinitialspace=True
                                    )
                                    st.success(f"✅ 使用 Python 引擎修復成功！載入了 {len(df_fixed)} 行數據")
                                    st.info("請重新點擊「開始訓練」按鈕")
                                    
                            except Exception as fix_error:
                                st.error(f"❌ 自動修復失敗：{str(fix_error)}")
                                st.info("請手動檢查並修復 CSV 文件格式")
                
                import traceback
                with st.expander("詳細錯誤訊息"):
                    st.code(traceback.format_exc())
            
            finally:
                # 清理臨時檔案
                try:
                    temp_path.unlink()
                except:
                    pass
    
    # 使用說明
    with st.expander("ℹ️ 使用說明"):
        st.markdown("""
        ### 資料格式要求
        
        #### 二元分類 (binary)
        - 必須包含 `is_attack` 欄位（0: 正常, 1: 攻擊）
        - 其他欄位作為特徵
        
        #### 多元分類 (multiclass)
        - 必須包含 `crlevel` 欄位（0-4: 風險等級）
        - 其他欄位作為特徵
        
        ### 參數說明
        
        #### 測試集比例
        - 控制用於評估模型效能的資料比例
        - 建議值：0.2 (20%) 到 0.3 (30%)
        
        #### 決策閾值 (Threshold)
        - **0.5**: 平衡敏感度和特異性（預設值）
        - **< 0.5**: 提高敏感度，減少漏報（False Negative）
        - **> 0.5**: 提高特異性，減少誤報（False Positive）
        - Cisco ASA 攻擊偵測建議：0.3-0.4（優先避免漏報）
        
        ### 訓練流程
        1. **資料載入**：讀取 CSV 檔案並進行初步驗證
        2. **特徵準備**：自動分離特徵和標籤
        3. **資料分割**：按指定比例分為訓練集和測試集
        4. **模型訓練**：訓練 LightGBM、XGBoost、CatBoost 模型
        5. **閾值應用**：根據設定的閾值調整分類決策
        6. **模型評估**：計算準確率、精確率、召回率等指標
        7. **結果儲存**：儲存最佳模型和詳細評估報告
        
        ### 輸出檔案
        - `models/`: 訓練好的模型檔案 (.pkl)
        - `reports/`: 詳細評估報告 (JSON)
        - 模型效能比較表
        
        ### 注意事項
        - 確保資料集大小足夠（建議 > 10,000 筆）
        - 特徵欄位應為數值型，避免文字或過多缺失值
        - 閾值調整會直接影響攻擊偵測的敏感度
        - 訓練時間依資料量和模型複雜度而定
        - 建議先使用預設參數測試，再根據需求調整閾值
        """)
