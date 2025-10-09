"""
=============================================================================
Cisco ASA 資料狀態檢測器
-----------------------------------------------------------------------------
功能：
1. 自動偵測資料是否已清洗
2. 判斷資料格式（原始 Syslog / CSV / 已處理）
3. 決定是否需要執行 ETL 處理
=============================================================================
"""
import pandas as pd
from typing import Dict, Tuple
import logging


class CiscoDataStateDetector:
    """Cisco ASA 資料狀態檢測器"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
    def detect_data_state(self, df: pd.DataFrame) -> Dict:
        """
        偵測資料狀態
        
        Args:
            df: 要檢測的資料框
            
        Returns:
            包含檢測結果的字典：
            {
                "format": "raw_syslog" | "csv_raw" | "csv_processed" | "csv_with_features",
                "has_is_attack": bool,
                "has_features": bool,
                "needs_parsing": bool,
                "needs_feature_engineering": bool,
                "column_count": int,
                "row_count": int,
                "recommendations": List[str]
            }
        """
        print("🔍 開始檢測 Cisco ASA 資料狀態...")
        
        result = {
            "format": "unknown",
            "has_is_attack": False,
            "has_features": False,
            "needs_parsing": False,
            "needs_feature_engineering": False,
            "column_count": len(df.columns),
            "row_count": len(df),
            "recommendations": []
        }
        
        # 檢查基本欄位
        columns = set(df.columns)
        
        # 1. 檢查是否有 is_attack 欄位
        result["has_is_attack"] = "is_attack" in columns
        
        # 2. 檢查是否包含原始 Syslog
        has_raw_log = "raw_log" in columns or "Description" in columns
        
        # 3. 檢查是否有特徵工程欄位（檢查幾個關鍵特徵）
        feature_indicators = {
            "hour", "day_of_week", "src_conn_count_1min",
            "src_is_private", "connection_direction"
        }
        has_features = bool(feature_indicators & columns)
        result["has_features"] = has_features
        
        # 4. 檢查關鍵欄位
        basic_cisco_columns = {
            "Severity", "SyslogID", "SourceIP", "DestinationIP"
        }
        processed_columns = {
            "severity", "syslog_id", "source_ip", "destination_ip"
        }
        
        has_basic_cisco = basic_cisco_columns.issubset(columns)
        has_processed = processed_columns.issubset(columns)
        
        # 判斷資料格式
        if has_features and result["has_is_attack"]:
            result["format"] = "csv_with_features"
            result["needs_parsing"] = False
            result["needs_feature_engineering"] = False
            result["recommendations"].append(
                "✅ 資料已包含特徵工程，可直接用於訓練/推論"
            )
            
        elif has_processed and result["has_is_attack"]:
            result["format"] = "csv_processed"
            result["needs_parsing"] = False
            result["needs_feature_engineering"] = True
            result["recommendations"].append(
                "⚙️ 資料已清洗但缺少特徵工程，建議執行特徵工程"
            )
            
        elif has_basic_cisco and has_raw_log:
            result["format"] = "csv_raw"
            result["needs_parsing"] = True
            result["needs_feature_engineering"] = True
            result["recommendations"].append(
                "🔄 偵測到原始 CSV 格式，需要執行完整 ETL 處理"
            )
            
        elif has_raw_log and result["column_count"] <= 5:
            result["format"] = "raw_syslog"
            result["needs_parsing"] = True
            result["needs_feature_engineering"] = True
            result["recommendations"].append(
                "📄 偵測到原始 Syslog 格式，需要解析並執行 ETL"
            )
            
        else:
            result["format"] = "unknown"
            result["recommendations"].append(
                "⚠️ 無法確定資料格式，請檢查資料結構"
            )
        
        # 5. 檢查 is_attack 標籤品質
        if result["has_is_attack"]:
            attack_ratio = df["is_attack"].sum() / len(df) if len(df) > 0 else 0
            result["attack_ratio"] = attack_ratio
            
            if attack_ratio == 0:
                result["recommendations"].append(
                    "⚠️ is_attack 標籤全為 0，可能需要重新建立"
                )
            elif attack_ratio == 1:
                result["recommendations"].append(
                    "⚠️ is_attack 標籤全為 1，可能需要重新建立"
                )
            else:
                result["recommendations"].append(
                    f"✅ is_attack 標籤比例：{attack_ratio:.2%}"
                )
        else:
            result["recommendations"].append(
                "❌ 缺少 is_attack 標籤，需要根據 Severity 建立"
            )
        
        # 6. 檢查資料品質
        missing_ratio = df.isnull().sum().sum() / (len(df) * len(df.columns))
        if missing_ratio > 0.1:
            result["recommendations"].append(
                f"⚠️ 資料缺失率較高 ({missing_ratio:.2%})，可能影響模型效能"
            )
        
        # 印出檢測結果
        self._print_detection_result(result)
        
        return result
    
    def _print_detection_result(self, result: Dict):
        """印出檢測結果"""
        print("\n" + "="*60)
        print("📊 Cisco ASA 資料狀態檢測結果")
        print("="*60)
        
        print(f"\n資料格式：{result['format']}")
        print(f"資料筆數：{result['row_count']:,}")
        print(f"欄位數量：{result['column_count']}")
        
        print(f"\n包含 is_attack 標籤：{'✅ 是' if result['has_is_attack'] else '❌ 否'}")
        print(f"包含特徵工程：{'✅ 是' if result['has_features'] else '❌ 否'}")
        
        print(f"\n需要解析處理：{'✅ 是' if result['needs_parsing'] else '❌ 否'}")
        print(f"需要特徵工程：{'✅ 是' if result['needs_feature_engineering'] else '❌ 否'}")
        
        if result["recommendations"]:
            print("\n💡 建議：")
            for rec in result["recommendations"]:
                print(f"  {rec}")
        
        print("="*60 + "\n")
    
    def should_skip_etl(self, detection_result: Dict) -> Tuple[bool, str]:
        """
        根據檢測結果判斷是否應該跳過 ETL 處理
        
        Args:
            detection_result: detect_data_state 的返回結果
            
        Returns:
            (是否跳過, 原因說明)
        """
        data_format = detection_result["format"]
        
        if data_format == "csv_with_features":
            return True, "資料已包含完整特徵，無需處理"
        
        elif data_format == "csv_processed" and not detection_result["needs_feature_engineering"]:
            return True, "資料已清洗且不需特徵工程"
        
        else:
            return False, "需要執行 ETL 處理"
    
    def get_processing_plan(self, detection_result: Dict) -> Dict:
        """
        根據檢測結果產生處理計畫
        
        Args:
            detection_result: detect_data_state 的返回結果
            
        Returns:
            處理計畫字典
        """
        plan = {
            "steps": [],
            "estimated_time": "unknown"
        }
        
        if detection_result["needs_parsing"]:
            plan["steps"].append({
                "name": "日誌解析",
                "description": "解析原始 Syslog 或 CSV 格式",
                "required": True
            })
        
        if not detection_result["has_is_attack"]:
            plan["steps"].append({
                "name": "建立標籤",
                "description": "根據 Severity 建立 is_attack 標籤",
                "required": True
            })
        
        if detection_result["needs_feature_engineering"]:
            plan["steps"].append({
                "name": "特徵工程",
                "description": "建立時間、連線、行為等特徵",
                "required": False
            })
        
        # 估算處理時間
        row_count = detection_result["row_count"]
        if row_count < 10000:
            plan["estimated_time"] = "< 1 分鐘"
        elif row_count < 100000:
            plan["estimated_time"] = "1-5 分鐘"
        elif row_count < 1000000:
            plan["estimated_time"] = "5-30 分鐘"
        else:
            plan["estimated_time"] = "> 30 分鐘"
        
        return plan


def detect_cisco_data_state(df: pd.DataFrame) -> Dict:
    """
    便利函式：偵測 Cisco ASA 資料狀態
    
    Args:
        df: 要檢測的資料框
        
    Returns:
        檢測結果字典
    """
    detector = CiscoDataStateDetector()
    return detector.detect_data_state(df)


def should_skip_etl(df: pd.DataFrame) -> Tuple[bool, str]:
    """
    便利函式：判斷是否應該跳過 ETL 處理
    
    Args:
        df: 要檢測的資料框
        
    Returns:
        (是否跳過, 原因說明)
    """
    detector = CiscoDataStateDetector()
    result = detector.detect_data_state(df)
    return detector.should_skip_etl(result)
