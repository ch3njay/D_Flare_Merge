import streamlit as st
import threading
import time
import os
import io
import contextlib
import queue
from . import _ensure_module, apply_dark_theme  # [MODIFIED]

_ensure_module("numpy", "numpy_stub")

_ensure_module("pandas", "pandas_stub")

import sys
from pathlib import Path

# 確保專案根目錄在 Python 路徑中
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

_IMPORT_ERROR_MSG = ""
try:
    from Forti_ui_app_bundle.training_pipeline.pipeline_main import TrainingPipeline
    _TRAINING_PIPELINE_AVAILABLE = True
except ImportError as e1:
    _IMPORT_ERROR_MSG += f"Absolute import failed: {e1}\n"
    try:
        from ..training_pipeline.pipeline_main import TrainingPipeline
        _TRAINING_PIPELINE_AVAILABLE = True
    except ImportError as e2:
        _IMPORT_ERROR_MSG += f"Relative import failed: {e2}\n"
        # 嘗試通過直接添加路徑的方式
        try:
            import os
            forti_path = os.path.join(os.path.dirname(__file__), "..", "..")
            if forti_path not in sys.path:
                sys.path.insert(0, forti_path)
            from Forti_ui_app_bundle.training_pipeline.pipeline_main import TrainingPipeline
            _TRAINING_PIPELINE_AVAILABLE = True
        except ImportError as e3:
            _IMPORT_ERROR_MSG += f"Direct path import failed: {e3}\n"
            _TRAINING_PIPELINE_AVAILABLE = False
        # 提供一個簡單的 fallback，但在 UI 中明確告知用戶
        class TrainingPipeline:
            def __init__(self, *args, **kwargs):
                self.config = {}
                self.task_type = "binary"
                self.optuna_enabled = False
                self.optimize_base = False
                self.optimize_ensemble = False
                self.use_tuned_for_training = True
                
            def run(self, *args, **kwargs):
                raise ImportError("真正的 TrainingPipeline 模組無法載入")


def app() -> None:
    apply_dark_theme()  # [ADDED]
    st.title("Training Pipeline")
    
    # 檢查 TrainingPipeline 是否可用
    if not _TRAINING_PIPELINE_AVAILABLE:
        st.error("⚠️ TrainingPipeline 模組無法載入，此功能暫時不可用。")
        with st.expander("詳細錯誤訊息"):
            st.code(_IMPORT_ERROR_MSG)
            st.code(f"Current working directory: {os.getcwd()}")
            st.code(f"Python path: {sys.path[:3]}...")
            st.code(f"File location: {__file__}")
        return
    
    st.markdown(
        """
        <style>
        .df-training-tip {
            background: color-mix(in srgb, var(--secondaryBackgroundColor) 80%, var(--backgroundColor) 20%);
            border: 1px solid color-mix(in srgb, var(--primaryColor) 28%, transparent);
            color: var(--textColor);
            padding: 0.85rem 1.1rem;
            border-radius: 0.85rem;
            margin-bottom: 1.2rem;
            box-shadow: 0 18px 36px -24px color-mix(in srgb, var(--primaryColor) 45%, transparent);
        }
        .df-training-tip strong {
            color: var(--primaryColor);
        }
        </style>
        <div class="df-training-tip">
            <strong>提示：</strong>訓練狀態會依照 Streamlit 主題自動調整色彩，確保在亮/暗模式下都具備清晰對比。
        </div>
        """,
        unsafe_allow_html=True,
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
        col1, col2 = st.columns(2)
        
        with col1:
            random_state = st.number_input(
                "隨機種子",
                min_value=0,
                value=42,
                help="設定隨機種子以確保結果可重現"
            )
            
            optuna_enabled = st.checkbox("Enable Optuna", value=False)
        
        with col2:
            output_dir = st.text_input(
                "輸出目錄",
                value="./artifacts",
                help="訓練結果和模型的儲存位置"
            )
        
        # Optuna 設定
        optimize_base = False
        optimize_ensemble = False
        use_tuned_for_training = False
        ensemble_mode = "free"

        if optuna_enabled:
            st.markdown("**Optuna 優化設定**")
            col3, col4 = st.columns(2)
            
            with col3:
                optimize_base = st.checkbox("Optimize base models", value=False)
            
            with col4:
                optimize_ensemble = st.checkbox("Optimize ensemble", value=False)

            if optimize_base or optimize_ensemble:
                use_tuned_for_training = st.checkbox(
                    "Use tuned params for training", 
                    value=True
                )
                if optimize_ensemble and use_tuned_for_training:
                    ensemble_mode = st.selectbox(
                        "Ensemble mode",
                        ["free", "fixed"],
                        help="Optuna ensemble search mode",
                    )
            else:
                st.info("Optuna disabled because no optimization scope selected.")
                optuna_enabled = False

    # 開始訓練
    st.subheader("3️⃣ 開始訓練")
    
    if not uploaded_files:
        st.warning("⚠️ 請先上傳訓練資料")
        st.button("🚀 開始訓練", disabled=True)
        return
    
    # 處理多檔案選擇
    if len(uploaded_files) > 1:
        st.info(f"� 偵測到 {len(uploaded_files)} 個檔案，將使用第一個檔案進行訓練：**{uploaded_files[0].name}**")
    
    uploaded_file = uploaded_files[0]
    st.success(f"✅ 使用檔案：{uploaded_file.name}")

    if st.button("🚀 開始訓練", type="primary"):
        # 儲存上傳的檔案到臨時目錄
        tmp_path = f"uploaded_{uploaded_file.name}"
        with open(tmp_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        # 建立訓練管線並設定參數
        pipeline = TrainingPipeline(
            task_type=task_type,
            optuna_enabled=optuna_enabled,
            optimize_base=optimize_base,
            optimize_ensemble=optimize_ensemble,
            use_tuned_for_training=use_tuned_for_training,
        )
        
        # 設定測試集比例和閾值
        if hasattr(pipeline, 'config') and pipeline.config:
            pipeline.config["VALID_SIZE"] = test_size
            pipeline.config["RANDOM_STATE"] = random_state
            pipeline.config.setdefault("ENSEMBLE_SETTINGS", {})["MODE"] = ensemble_mode
            pipeline.config.setdefault("ENSEMBLE_SETTINGS", {})["THRESHOLD"] = threshold
        progress = st.progress(0)
        status = st.empty()
        log_box = st.empty()

        result = {"error": None, "output": None}

        log_queue: "queue.Queue[str]" = queue.Queue()

        class _QueueStream(io.TextIOBase):
            def write(self, buf: str) -> int:
                log_queue.put(buf)
                return len(buf)

            def flush(self) -> None:
                pass

        def _run():
            try:
                stream = _QueueStream()
                with contextlib.redirect_stdout(stream), \
                     contextlib.redirect_stderr(stream):
                    result["output"] = pipeline.run(tmp_path)

            except Exception as exc:
                result["error"] = exc

        thread = threading.Thread(target=_run)
        thread.start()
        pct = 0
        log_text = ""
        while thread.is_alive():
            if pct < 95:
                pct += 5
            progress.progress(pct)
            status.text(f"Training in progress... {pct}%")
            while not log_queue.empty():
                log_text += log_queue.get()
            log_box.code(log_text)
            time.sleep(0.1)
        thread.join()
        while not log_queue.empty():
            log_text += log_queue.get()
        log_box.code(log_text)
        if result["error"] is None:
            progress.progress(100)
            status.text("Training finished")
            st.success("Training finished")

            # Debug: 檢查 result 結構
            st.write(f"DEBUG: result keys: {list(result.keys())}")
            st.write(f"DEBUG: result['error']: {result.get('error')}")
            st.write(f"DEBUG: result['output'] type: {type(result.get('output'))}")
            if result.get("output"):
                st.write(f"DEBUG: output keys: {list(result['output'].keys())}")
            
            artifacts_dir = result["output"].get("artifacts_dir") if result["output"] else None
            if artifacts_dir:

                from pathlib import Path
                import os

                st.write(f"DEBUG: artifacts_dir = {artifacts_dir}")
                
                # 檢查目錄是否存在
                if os.path.exists(artifacts_dir):
                    st.write(f"DEBUG: artifacts_dir exists")
                    # 列出目錄內容
                    try:
                        contents = os.listdir(artifacts_dir)
                        st.write(f"DEBUG: artifacts_dir contents: {contents}")
                        
                        models_dir = os.path.join(artifacts_dir, "models")
                        if os.path.exists(models_dir):
                            models_contents = os.listdir(models_dir)
                            st.write(f"DEBUG: models dir contents: {models_contents}")
                        else:
                            st.write("DEBUG: models directory does not exist")
                    except Exception as e:
                        st.write(f"DEBUG: Error listing contents: {e}")
                else:
                    st.write(f"DEBUG: artifacts_dir does not exist")

                model_path = Path(artifacts_dir) / "models" / "ensemble_best.joblib"
                st.write(f"DEBUG: Looking for model at: {model_path}")
                if model_path.exists():

                    with open(model_path, "rb") as f:
                        model_bytes = f.read()
                    st.download_button(
                        "Download ensemble model",
                        model_bytes,
                        file_name="ensemble_best.joblib",
                    )
                    st.info(f"Artifacts saved to: {artifacts_dir}")
                else:
                    st.warning("Model file not found in artifacts directory.")

            else:
                st.warning("No artifacts directory returned.")


        else:
            status.text("Training failed")
            error_msg = result['error']
            st.error(f"Training failed: {error_msg}")
            
            # 檢查是否是 CSV 格式錯誤
            if ("Error tokenizing data" in str(error_msg) or 
                ("Expected" in str(error_msg) and "fields" in str(error_msg))):
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
                    - 檢查錯誤提到的行數（如第22行）
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
        - 攻擊偵測建議：0.3-0.4（優先避免漏報）
        
        #### Optuna 優化
        - **Optimize base models**: 自動調整單一模型參數
        - **Optimize ensemble**: 自動調整集成策略
        - **Free mode**: 靈活的集成搜尋
        - **Fixed mode**: 固定的集成結構
        
        ### 訓練流程
        1. **資料載入**：讀取並合併多個檔案
        2. **特徵準備**：自動特徵選擇和工程
        3. **資料分割**：按指定比例分為訓練集和測試集
        4. **模型訓練**：訓練 XGB、LGB、CAT、RF、ET 模型
        5. **集成優化**：使用 Stacking 或 Voting 方法
        6. **閾值應用**：根據設定的閾值進行最終預測
        7. **結果儲存**：儲存模型和評估報告
        
        ### 輸出檔案
        - `models/`: 訓練好的模型檔案 (.joblib)
        - `reports/`: 詳細的評估報告和指標
        - `ensemble_best.joblib`: 最佳集成模型
        
        ### 注意事項
        - 確保資料集大小足夠（建議 > 10,000 筆）
        - 類別分佈不要過於不平衡
        - 訓練時間依資料量和 Optuna 設定而定
        - 閾值調整會影響最終的分類效果
        """)
