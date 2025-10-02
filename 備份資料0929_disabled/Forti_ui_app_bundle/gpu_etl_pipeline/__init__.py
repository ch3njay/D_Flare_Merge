"""
gpu_etl_pipeline package
------------------------
功能：
- GPU 加速版的日誌資料 ETL（清洗 → 映射 → 特徵工程）
- 完整保留原本 CPU 版功能：抽樣、唯一值清單、欄位排序、特徵工程、靜默/互動模式
- 內部以 RAPIDS cuDF / cuPy 為優先；無 GPU 時會自動退回 pandas / numpy
"""