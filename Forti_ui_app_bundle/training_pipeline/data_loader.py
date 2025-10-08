# training_pipeline/data_loader.py
import numpy as np
import pandas as pd
from typing import Dict, Tuple


class DataLoader:
    def __init__(self, config: dict):
        self.config = config

    def load_data(self, file_path: str) -> pd.DataFrame:
        """智能載入數據，支持自動格式偵測和 ETL 預處理"""
        
                # 偵測資料格式
        data_format = self._detect_data_format(file_path)
        print(f"🔍 偵測到資料格式：{data_format}")
        
        if data_format == "compressed":
            print("📦 偵測到壓縮檔案，先解壓縮...")
            extracted_file = self._extract_compressed_file(file_path)
            if extracted_file:
                # 遞迴檢測解壓後的檔案格式
                return self.load_data(extracted_file)
            else:
                print("❌ 壓縮檔案解壓失敗，嘗試直接處理...")
                return self._load_with_fallback_methods(file_path)
        elif data_format == "fortinet_log":
            print("🔄 偵測到 Fortinet 日誌格式，執行 ETL 前處理...")
            return self._process_fortinet_logs(file_path)
        elif data_format == "csv":
            return self._load_with_fallback_methods(file_path)
        else:
            print("⚠️ 未知格式，嘗試各種載入方法...")
            return self._load_with_fallback_methods(file_path)
    
    def _detect_data_format(self, file_path: str) -> str:
        """偵測數據格式，支援壓縮檔案"""
        import os
        
        # 檢查是否為壓縮檔案
        file_extension = os.path.splitext(file_path)[1].lower()
        if file_extension in ['.gz', '.zip', '.7z', '.rar', '.tar', '.bz2']:
            return "compressed"
        
        try:
            # 嘗試以文本方式讀取
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                first_lines = [f.readline().strip() for _ in range(5)]
                first_lines = [line for line in first_lines if line]  # 移除空行
            
            # 檢查是否為 Fortinet 日誌格式 (key=value 對)
            fortinet_indicators = 0
            for line in first_lines:
                if not line:
                    continue
                # 檢查 Fortinet 日誌的特徵
                if ('logver=' in line and 'idseq=' in line and 
                    'devid=' in line and 'type=' in line):
                    fortinet_indicators += 1
                # 檢查 key=value 模式
                import re
                kv_pattern = re.compile(r'(\w+)=(".*?"|\'.*?\'|[^"\',\s]+)')
                if len(kv_pattern.findall(line)) > 5:  # 超過5個 key=value 對
                    fortinet_indicators += 1
            
            if fortinet_indicators >= 2:
                return "fortinet_log"
            
            # 檢查是否為 CSV 格式
            try:
                pd.read_csv(file_path, nrows=1)
                return "csv"
            except:
                pass
                
            return "unknown"
            
        except Exception as e:
            print(f"格式偵測失敗: {e}")
            return "unknown"
    
    def _extract_compressed_file(self, file_path: str) -> str | None:
        """解壓縮檔案並返回解壓後的檔案路徑"""
        import os
        import tempfile
        import zipfile
        import gzip
        import tarfile
        import shutil
        
        file_extension = os.path.splitext(file_path)[1].lower()
        temp_dir = tempfile.mkdtemp()
        
        try:
            if file_extension == '.gz':
                # 處理 .gz 檔案
                output_path = os.path.join(temp_dir, 'extracted_file.txt')
                with gzip.open(file_path, 'rt', encoding='utf-8', errors='ignore') as gz_file:
                    with open(output_path, 'w', encoding='utf-8') as out_file:
                        shutil.copyfileobj(gz_file, out_file)
                print(f"✅ 成功解壓 .gz 檔案到: {output_path}")
                return output_path
                
            elif file_extension == '.zip':
                # 處理 .zip 檔案
                with zipfile.ZipFile(file_path, 'r') as zip_file:
                    # 取得第一個檔案
                    file_list = zip_file.namelist()
                    if not file_list:
                        print("❌ ZIP 檔案為空")
                        return None
                    
                    first_file = file_list[0]
                    extracted_path = zip_file.extract(first_file, temp_dir)
                    print(f"✅ 成功解壓 .zip 檔案到: {extracted_path}")
                    return extracted_path
                    
            elif file_extension in ['.tar', '.tar.gz', '.tgz']:
                # 處理 .tar 相關檔案
                with tarfile.open(file_path, 'r:*') as tar_file:
                    # 取得第一個檔案
                    members = tar_file.getmembers()
                    if not members:
                        print("❌ TAR 檔案為空")
                        return None
                    
                    first_member = members[0]
                    if first_member.isfile():
                        tar_file.extract(first_member, temp_dir)
                        extracted_path = os.path.join(temp_dir, first_member.name)
                        print(f"✅ 成功解壓 .tar 檔案到: {extracted_path}")
                        return extracted_path
                        
            else:
                print(f"⚠️ 不支援的壓縮格式: {file_extension}")
                return None
                
        except Exception as e:
            print(f"❌ 解壓縮失敗: {e}")
            # 清理暫存目錄
            try:
                shutil.rmtree(temp_dir)
            except Exception:
                pass
            return None
    
    def _process_fortinet_logs(self, file_path: str) -> pd.DataFrame:
        """處理 Fortinet 原始日誌格式"""
        print("🔄 偵測到 Fortinet 日誌格式，開始 ETL 處理...")
        
        try:
            # 導入 ETL 模組
            from ..etl_pipeline.log_cleaning import parse_log_line
            import tempfile
            import os
            
            processed_records = []
            
            # 讀取並解析原始日誌
            with open(file_path, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    if line.strip():
                        record = parse_log_line(line.strip())
                        if record:
                            processed_records.append(record)
                        if line_num % 10000 == 0:
                            print(f"📈 已處理 {line_num} 行，成功解析 {len(processed_records)} 條記錄")
            
            print(f"✅ ETL 處理完成：共解析 {len(processed_records)} 條記錄")
            
            # 轉換為 DataFrame
            df = pd.DataFrame(processed_records)
            
            # 基本數據清理和轉換
            df = self._apply_basic_etl_transforms(df)
            
            print(f"📊 最終數據形狀: {df.shape}")
            return df
            
        except ImportError as e:
            print(f"❌ 無法導入 ETL 模組: {e}")
            raise RuntimeError("ETL 模組不可用，無法處理 Fortinet 日誌格式")
        except Exception as e:
            print(f"❌ ETL 處理失敗: {e}")
            raise RuntimeError(f"ETL 處理失敗: {str(e)}")
    
    def _apply_basic_etl_transforms(self, df: pd.DataFrame) -> pd.DataFrame:
        """應用基本的 ETL 轉換"""
        try:
            # 處理日期時間
            if 'date' in df.columns and 'time' in df.columns:
                df['datetime'] = pd.to_datetime(
                    df['date'] + ' ' + df['time'], 
                    errors='coerce'
                )
            
            # 處理數值欄位
            numeric_cols = ['srcport', 'dstport', 'sentpkt', 'rcvdpkt', 'duration', 'crscore']
            for col in numeric_cols:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
            
            # 設定攻擊標籤
            if 'crscore' in df.columns:
                df['is_attack'] = (pd.to_numeric(df['crscore'], errors='coerce') > 0).astype(int)
            else:
                df['is_attack'] = 0
            
            # 設定風險等級
            if 'crlevel' not in df.columns:
                df['crlevel'] = 'none'
            
            print("✅ 基本 ETL 轉換完成")
            return df
            
        except Exception as e:
            print(f"⚠️ ETL 轉換部分失敗: {e}")
            return df
    
    def _load_csv_with_fallback(self, file_path: str) -> pd.DataFrame:
        """使用容錯機制載入 CSV 文件"""
        try:
            df = pd.read_csv(file_path)
            print(f"✅ CSV 載入完成：{df.shape[0]} 筆，欄位 {df.shape[1]}")
            return df
        except pd.errors.ParserError as e:
            print(f"⚠️ CSV 格式問題：{str(e)}")
            return self._load_with_fallback_methods(file_path)
    
    def _load_with_fallback_methods(self, file_path: str) -> pd.DataFrame:
        """使用多種容錯方法載入文件"""
        print("🔄 嘗試使用容錯模式重新讀取...")
        
        # 容錯方法列表
        fallback_methods = [
            {
                "name": "容錯模式",
                "params": {
                    "error_bad_lines": False,
                    "warn_bad_lines": True,
                    "on_bad_lines": 'warn'
                }
            },
            {
                "name": "Python 引擎",
                "params": {
                    "sep": None,
                    "engine": 'python',
                    "quoting": 3,
                    "skipinitialspace": True
                }
            }
        ]
        
        for method in fallback_methods:
            try:
                df = pd.read_csv(file_path, **method["params"])
                print(f"✅ {method['name']}載入完成：{df.shape[0]} 筆，欄位 {df.shape[1]}")
                return df
            except Exception as e:
                print(f"❌ {method['name']}失敗: {e}")
                continue
        
        # 所有方法都失敗
        raise RuntimeError(
            f"無法載入文件：{file_path}\n"
            f"已嘗試所有載入方法都失敗。\n"
            f"請檢查：\n"
            f"1. 文件是否為有效的 CSV 格式\n"
            f"2. 或者是否為 Fortinet 日誌但格式不正確\n"
            f"3. 文件編碼是否正確（建議使用 UTF-8）"
        )

    # === 新增：帶報告版本（不破壞舊介面） ===
    @staticmethod
    def prepare_xy_with_report(df: pd.DataFrame, config: dict, task: str) -> Tuple[pd.DataFrame, pd.Series, Dict]:
        """
        與舊版一致的邏輯，但額外回傳 report：
        - dropped_by_dropcols
        - dropped_by_type
        - dropped_constant
        - initial_count, final_count, final_cols
        """
        target_col = config["TARGET_COLUMN"]
        drop_cols = set(config.get("DROP_COLUMNS", []))
        if target_col not in df.columns:
            raise KeyError(f"找不到目標欄位 {target_col}")

        report: Dict = {}
        init_cols = list(df.columns)
        report["initial_count"] = len(init_cols)
        report["initial_cols"] = init_cols

        y = df[target_col]
        # 1) 丟掉 DROP_COLUMNS
        X1 = df.drop(columns=list(drop_cols & set(df.columns)), errors="ignore")
        report["dropped_by_dropcols"] = sorted(list(set(init_cols) - set(X1.columns) - {target_col}))
        report["after_drop_cols"] = list(X1.columns)

        # 2) 僅保留 numeric/bool
        keep_cols = []
        for c in X1.columns:
            if c == target_col:
                continue
            dt = X1[c].dtype
            if pd.api.types.is_bool_dtype(dt) or pd.api.types.is_numeric_dtype(dt):
                keep_cols.append(c)
        X2 = X1[keep_cols].copy()
        report["dropped_by_type"] = sorted(list(set(X1.columns) - set(X2.columns)))
        report["after_type_filter"] = list(X2.columns)

        # 3) 補值 + 型別統一
        for c in X2.columns:
            if pd.api.types.is_bool_dtype(X2[c].dtype):
                X2[c] = X2[c].fillna(False).astype(np.int8, copy=False)
            else:
                X2[c] = X2[c].fillna(0).astype(np.float32, copy=False)

        # 4) 去常數欄（含全 NaN/單一值）
        nunique = X2.nunique(dropna=False)
        const_cols = nunique[nunique <= 1].index.tolist()
        X3 = X2.drop(columns=const_cols, errors="ignore")
        report["dropped_constant"] = const_cols

        report["final_cols"] = list(X3.columns)
        report["final_count"] = int(X3.shape[1])

        # 第二次訊息：特徵篩選摘要
        print(f"✅ 特徵篩選完成：由 {report['initial_count']} → {report['final_count']} 欄")
        print(f"• 由 DROP_COLUMNS 移除：{report['dropped_by_dropcols'] or '無'}")
        print(f"• 非數值/布林被過濾：{report['dropped_by_type'] or '無'}")
        print(f"• 常數/全空欄移除：{report['dropped_constant'] or '無'}")

        return X3, y, report

    # === 舊介面（維持不破壞） ===
    @staticmethod
    def prepare_xy(df: pd.DataFrame, config: dict, task: str):
        X, y, _ = DataLoader.prepare_xy_with_report(df, config, task)
        return X, y
