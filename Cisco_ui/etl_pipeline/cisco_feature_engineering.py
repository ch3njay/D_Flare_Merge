"""
=============================================================================
Cisco ASA 特徵工程模組
-----------------------------------------------------------------------------
專門針對 Cisco ASA 日誌特性設計的特徵工程
參考 Forti 的設計思路，但完全適應 Cisco ASA 的欄位特性
=============================================================================
"""
import pandas as pd
import numpy as np
from typing import Dict, List
import logging
from datetime import timedelta


class CiscoASAFeatureEngineer:
    """Cisco ASA 特徵工程器"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
    def create_all_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        建立所有特徵
        
        Args:
            df: 原始資料框
            
        Returns:
            包含新特徵的資料框
        """
        print("🔧 開始建立 Cisco ASA 特徵...")
        
        # 確保必要欄位存在
        df = self._ensure_required_columns(df)
        
        # 1. 時間特徵
        df = self._create_time_features(df)
        
        # 2. 連線特徵
        df = self._create_connection_features(df)
        
        # 3. IP 特徵
        df = self._create_ip_features(df)
        
        # 4. 行為特徵（基於時間窗口）
        df = self._create_behavioral_features(df)
        
        # 5. Severity 相關特徵
        df = self._create_severity_features(df)
        
        # 6. SyslogID 相關特徵
        df = self._create_syslogid_features(df)
        
        # 7. 統計特徵
        df = self._create_statistical_features(df)
        
        print(f"✅ 特徵工程完成，共建立 {len(df.columns)} 個欄位")
        
        return df
    
    def _ensure_required_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """確保必要欄位存在"""
        required_cols = {
            "datetime": pd.NaT,
            "severity": "0",
            "syslog_id": "0",
            "source_ip": "0.0.0.0",
            "source_port": 0,
            "destination_ip": "0.0.0.0",
            "destination_port": 0,
            "protocol": "unknown",
            "action": "unknown",
            "bytes": 0,
            "duration": 0,
            "is_attack": 0
        }
        
        for col, default_val in required_cols.items():
            if col not in df.columns:
                df[col] = default_val
        
        # 確保datetime是datetime型態
        if not pd.api.types.is_datetime64_any_dtype(df["datetime"]):
            df["datetime"] = pd.to_datetime(df["datetime"], errors="coerce")
        
        return df
    
    def _create_time_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """建立時間相關特徵"""
        print("  ⏰ 建立時間特徵...")
        
        if "datetime" in df.columns:
            # 小時 (0-23)
            df["hour"] = df["datetime"].dt.hour
            
            # 星期幾 (0=Monday, 6=Sunday)
            df["day_of_week"] = df["datetime"].dt.dayofweek
            
            # 是否為上班時間 (8-18點)
            df["is_business_hour"] = (
                (df["hour"] >= 8) & (df["hour"] < 18)
            ).astype(int)
            
            # 是否為週末
            df["is_weekend"] = (df["day_of_week"] >= 5).astype(int)
            
            # 時段分類 (0:深夜, 1:早上, 2:下午, 3:晚上)
            df["time_period"] = pd.cut(
                df["hour"],
                bins=[0, 6, 12, 18, 24],
                labels=[0, 1, 2, 3],
                include_lowest=True
            ).astype(int)
        
        return df
    
    def _create_connection_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """建立連線相關特徵"""
        print("  🔗 建立連線特徵...")
        
        # 是否為特權端口 (< 1024)
        df["src_is_privileged_port"] = (
            df["source_port"].astype(int) < 1024
        ).astype(int)
        df["dst_is_privileged_port"] = (
            df["destination_port"].astype(int) < 1024
        ).astype(int)
        
        # 是否為常見服務端口
        common_ports = {
            20, 21,    # FTP
            22,        # SSH
            23,        # Telnet
            25,        # SMTP
            53,        # DNS
            80, 8080, 8000,  # HTTP
            443, 8443,       # HTTPS
            445,       # SMB
            3389,      # RDP
            3306,      # MySQL
            5432,      # PostgreSQL
            1433       # MSSQL
        }
        df["dst_is_common_port"] = df["destination_port"].astype(int).isin(
            common_ports
        ).astype(int)
        
        # 端口範圍分類
        df["dst_port_range"] = pd.cut(
            df["destination_port"].astype(int),
            bins=[0, 1024, 49152, 65536],
            labels=[0, 1, 2],  # 0:特權, 1:註冊, 2:動態
            include_lowest=True
        ).astype(int)
        
        # 連線時長分類
        df["duration_category"] = pd.cut(
            df["duration"].astype(float),
            bins=[0, 1, 10, 60, float("inf")],
            labels=[0, 1, 2, 3],  # 0:極短, 1:短, 2:中, 3:長
            include_lowest=True
        ).astype(int)
        
        # 資料量分類
        df["bytes_category"] = pd.cut(
            df["bytes"].astype(float),
            bins=[0, 1024, 10240, 102400, float("inf")],
            labels=[0, 1, 2, 3],  # 0:極小, 1:小, 2:中, 3:大
            include_lowest=True
        ).astype(int)
        
        return df
    
    def _create_ip_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """建立 IP 相關特徵"""
        print("  🌐 建立 IP 特徵...")
        
        # 是否為內部 IP (RFC1918 私有地址)
        df["src_is_private"] = df["source_ip"].apply(
            self._is_private_ip
        ).astype(int)
        df["dst_is_private"] = df["destination_ip"].apply(
            self._is_private_ip
        ).astype(int)
        
        # 連線方向 (0:內→內, 1:內→外, 2:外→內, 3:外→外)
        df["connection_direction"] = (
            df["src_is_private"] * 2 + df["dst_is_private"]
        )
        
        # IP 網段 (取前三段)
        df["src_subnet"] = df["source_ip"].apply(
            lambda x: ".".join(str(x).split(".")[:3]) if "." in str(x) else "unknown"
        )
        df["dst_subnet"] = df["destination_ip"].apply(
            lambda x: ".".join(str(x).split(".")[:3]) if "." in str(x) else "unknown"
        )
        
        # 是否為相同網段
        df["is_same_subnet"] = (
            df["src_subnet"] == df["dst_subnet"]
        ).astype(int)
        
        return df
    
    def _create_behavioral_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """建立行為特徵（基於時間窗口）"""
        print("  📊 建立行為特徵...")
        
        # 確保資料按時間排序
        df = df.sort_values("datetime").reset_index(drop=True)
        
        # 1分鐘、5分鐘、15分鐘時間窗口
        for window_minutes in [1, 5, 15]:
            window_key = f"{window_minutes}min"
            
            # 來源 IP 在窗口內的連線數
            df[f"src_conn_count_{window_key}"] = self._count_in_window(
                df, "source_ip", window_minutes
            )
            
            # 目的 IP 在窗口內的連線數
            df[f"dst_conn_count_{window_key}"] = self._count_in_window(
                df, "destination_ip", window_minutes
            )
            
            # 來源 IP 在窗口內的不同目的 IP 數量
            df[f"src_unique_dst_{window_key}"] = self._count_unique_in_window(
                df, "source_ip", "destination_ip", window_minutes
            )
            
            # 來源 IP 在窗口內的不同目的端口數量
            df[f"src_unique_dport_{window_key}"] = self._count_unique_in_window(
                df, "source_ip", "destination_port", window_minutes
            )
        
        # 來源 IP 的連線頻率（連線數 / 時間跨度）
        df["src_connection_rate"] = self._calculate_connection_rate(
            df, "source_ip"
        )
        
        return df
    
    def _create_severity_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """建立 Severity 相關特徵"""
        print("  🚨 建立 Severity 特徵...")
        
        # Severity 數值化
        df["severity_numeric"] = df["severity"].astype(int)
        
        # Severity 分類
        # 0: emergency (忽略)
        # 1-2: 嚴重 (alert, critical)
        # 3-4: 警告 (error, warning)
        # 5-7: 正常 (notification, informational, debugging)
        df["severity_category"] = pd.cut(
            df["severity_numeric"],
            bins=[0, 2, 4, 8],
            labels=[0, 1, 2],  # 0:嚴重, 1:警告, 2:正常
            include_lowest=True
        ).astype(int)
        
        # 來源 IP 的平均 severity
        df["src_avg_severity"] = df.groupby("source_ip")["severity_numeric"].transform("mean")
        
        # 來源 IP 的最大 severity
        df["src_max_severity"] = df.groupby("source_ip")["severity_numeric"].transform("max")
        
        return df
    
    def _create_syslogid_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """建立 SyslogID 相關特徵"""
        print("  🆔 建立 SyslogID 特徵...")
        
        # SyslogID 數值化
        df["syslogid_numeric"] = df["syslog_id"].astype(str).str.extract(
            r"(\d+)"
        ).astype(float).fillna(0).astype(int)
        
        # SyslogID 分類（根據 Cisco ASA 常見訊息 ID）
        # 3xxxxx: 連線相關
        # 4xxxxx: 存取控制
        # 5xxxxx: VPN
        # 6xxxxx: 系統
        # 7xxxxx: 其他
        df["syslogid_category"] = (
            df["syslogid_numeric"] // 100000
        ).clip(0, 7)
        
        # 來源 IP 觸發的不同 SyslogID 數量
        df["src_unique_syslogid"] = df.groupby("source_ip")["syslogid_numeric"].transform("nunique")
        
        return df
    
    def _create_statistical_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """建立統計特徵"""
        print("  📈 建立統計特徵...")
        
        # 來源 IP 統計
        df["src_total_bytes"] = df.groupby("source_ip")["bytes"].transform("sum")
        df["src_avg_bytes"] = df.groupby("source_ip")["bytes"].transform("mean")
        df["src_total_duration"] = df.groupby("source_ip")["duration"].transform("sum")
        df["src_avg_duration"] = df.groupby("source_ip")["duration"].transform("mean")
        
        # 目的 IP 統計
        df["dst_total_connections"] = df.groupby("destination_ip")["destination_ip"].transform("count")
        df["dst_unique_sources"] = df.groupby("destination_ip")["source_ip"].transform("nunique")
        
        # 來源-目的 IP 配對統計
        df["src_dst_pair_count"] = df.groupby(
            ["source_ip", "destination_ip"]
        )["source_ip"].transform("count")
        
        # Action 統計
        df["src_deny_ratio"] = self._calculate_ratio(
            df, "source_ip", "action", "deny"
        )
        
        return df
    
    # === 輔助函式 ===
    
    def _is_private_ip(self, ip: str) -> bool:
        """判斷是否為私有 IP"""
        try:
            parts = str(ip).split(".")
            if len(parts) != 4:
                return False
            
            first = int(parts[0])
            second = int(parts[1])
            
            # 10.0.0.0/8
            if first == 10:
                return True
            # 172.16.0.0/12
            if first == 172 and 16 <= second <= 31:
                return True
            # 192.168.0.0/16
            if first == 192 and second == 168:
                return True
            
            return False
        except:
            return False
    
    def _count_in_window(
        self, df: pd.DataFrame, group_col: str, window_minutes: int
    ) -> pd.Series:
        """計算時間窗口內的計數"""
        try:
            window = timedelta(minutes=window_minutes)
            result = pd.Series(0, index=df.index)
            
            for idx, row in df.iterrows():
                time_start = row["datetime"] - window
                time_end = row["datetime"]
                
                mask = (
                    (df["datetime"] >= time_start) &
                    (df["datetime"] <= time_end) &
                    (df[group_col] == row[group_col])
                )
                
                result.iloc[idx] = mask.sum()
            
            return result
        except:
            return pd.Series(0, index=df.index)
    
    def _count_unique_in_window(
        self, df: pd.DataFrame, group_col: str, count_col: str, window_minutes: int
    ) -> pd.Series:
        """計算時間窗口內的唯一值數量"""
        try:
            window = timedelta(minutes=window_minutes)
            result = pd.Series(0, index=df.index)
            
            for idx, row in df.iterrows():
                time_start = row["datetime"] - window
                time_end = row["datetime"]
                
                mask = (
                    (df["datetime"] >= time_start) &
                    (df["datetime"] <= time_end) &
                    (df[group_col] == row[group_col])
                )
                
                result.iloc[idx] = df.loc[mask, count_col].nunique()
            
            return result
        except:
            return pd.Series(0, index=df.index)
    
    def _calculate_connection_rate(
        self, df: pd.DataFrame, group_col: str
    ) -> pd.Series:
        """計算連線頻率"""
        try:
            result = pd.Series(0.0, index=df.index)
            
            for group_val in df[group_col].unique():
                mask = df[group_col] == group_val
                group_df = df[mask]
                
                if len(group_df) > 1:
                    time_span = (
                        group_df["datetime"].max() - group_df["datetime"].min()
                    ).total_seconds()
                    
                    if time_span > 0:
                        rate = len(group_df) / time_span
                        result[mask] = rate
            
            return result
        except:
            return pd.Series(0.0, index=df.index)
    
    def _calculate_ratio(
        self, df: pd.DataFrame, group_col: str, value_col: str, target_value: str
    ) -> pd.Series:
        """計算特定值的比例"""
        try:
            total = df.groupby(group_col)[value_col].transform("count")
            target = df.groupby(group_col)[value_col].transform(
                lambda x: (x == target_value).sum()
            )
            
            ratio = target / total
            ratio = ratio.fillna(0)
            
            return ratio
        except:
            return pd.Series(0.0, index=df.index)


def create_cisco_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    便利函式：為 Cisco ASA 資料建立所有特徵
    自動處理欄位名稱大小寫不一致的問題
    
    Args:
        df: 原始資料框（支援駝峰式大寫或小寫+底線命名）
        
    Returns:
        包含新特徵的資料框
    """
    # 欄位名稱映射（駝峰式大寫 → 小寫+底線）
    field_mapping = {
        "Datetime": "datetime",
        "Severity": "severity",
        "SyslogID": "syslog_id",
        "SourceIP": "source_ip",
        "SourcePort": "source_port",
        "DestinationIP": "destination_ip",
        "DestinationPort": "destination_port",
        "Protocol": "protocol",
        "Action": "action",
        "Bytes": "bytes",
        "Duration": "duration",
        "Description": "description"
    }
    
    # 建立欄位名稱轉換（如果存在駝峰式欄位）
    rename_dict = {}
    for camel_case, snake_case in field_mapping.items():
        if camel_case in df.columns and snake_case not in df.columns:
            rename_dict[camel_case] = snake_case
    
    # 轉換欄位名稱
    if rename_dict:
        df = df.rename(columns=rename_dict)
        print(f"  🔄 已轉換 {len(rename_dict)} 個欄位名稱為內部格式")
    
    # 建立特徵
    engineer = CiscoASAFeatureEngineer()
    df_with_features = engineer.create_all_features(df)
    
    # 轉換回駝峰式大寫（保持一致性）
    reverse_mapping = {v: k for k, v in field_mapping.items() if v in df_with_features.columns}
    if reverse_mapping:
        df_with_features = df_with_features.rename(columns=reverse_mapping)
    
    return df_with_features
