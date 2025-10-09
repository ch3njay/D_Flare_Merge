"""
=============================================================================
Cisco ASA 日誌解析模組
-----------------------------------------------------------------------------
功能：
1. 解析 Cisco ASA Syslog 格式日誌
2. 根據 Severity 建立 is_attack 標籤
3. 提取關鍵欄位並結構化
4. 支援多種 Cisco ASA 日誌格式
=============================================================================
"""
import re
import logging
from typing import Dict, Optional
from datetime import datetime

# Cisco ASA Severity 對照表（參考附件圖片）
SEVERITY_LEVELS = {
    "0": "emergencies",      # 系統不可用（硬體損壞）
    "1": "alert",            # 需要立即處理
    "2": "critical",         # 嚴重狀況
    "3": "error",            # 錯誤狀況
    "4": "warning",          # 警告狀況
    "5": "notification",     # 正常但重要的狀況
    "6": "informational",    # 資訊性訊息
    "7": "debugging"         # 除錯訊息
}

# Protocol 對照表
PROTOCOL_MAP = {
    "1": "ICMP",
    "6": "TCP",
    "17": "UDP",
    "4": "IP"
}


class CiscoASALogParser:
    """Cisco ASA 日誌解析器"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
    def parse_syslog_line(self, line: str) -> Optional[Dict]:
        """
        解析 Cisco ASA Syslog 格式日誌
        
        範例格式：
        <166>Jul 23 2025 23:59:09: %ASA-6-302013: Built inbound TCP connection...
        
        Args:
            line: 原始日誌行
            
        Returns:
            解析後的字典，若解析失敗則回傳 None
        """
        try:
            # 移除前導空白
            line = line.strip()
            if not line:
                return None
            
            result = {
                "raw_log": line,
                "Severity": "",
                "SyslogID": "",
                "Datetime": "",
                "SourceIP": "",
                "SourcePort": "",
                "DestinationIP": "",
                "DestinationPort": "",
                "Protocol": "",
                "Action": "",
                "Description": "",
                "Bytes": "0",
                "Duration": "0",
                "is_attack": 0
            }
            
            # 解析優先級 <166>
            priority_match = re.match(r'^<(\d+)>', line)
            if priority_match:
                line = line[priority_match.end():].strip()
            
            # 解析時間戳記：Jul 23 2025 23:59:09
            time_pattern = r'(\w{3}\s+\d{1,2}\s+\d{4}\s+\d{2}:\d{2}:\d{2})'
            time_match = re.search(time_pattern, line)
            if time_match:
                time_str = time_match.group(1)
                try:
                    dt = datetime.strptime(time_str, "%b %d %Y %H:%M:%S")
                    result["Datetime"] = dt.strftime("%Y-%m-%d %H:%M:%S")
                except:
                    result["Datetime"] = time_str
                line = line[time_match.end():].strip()
            
            # 解析 Cisco ASA 訊息標頭：%ASA-6-302013
            # 格式：%ASA-{severity}-{syslog_id}
            asa_pattern = r'%ASA-(\d+)-(\d+):'
            asa_match = re.search(asa_pattern, line)
            if asa_match:
                result["Severity"] = asa_match.group(1)
                result["SyslogID"] = asa_match.group(2)
                line = line[asa_match.end():].strip()
                result["Description"] = line
                
                # 根據 Severity 建立 is_attack 標籤
                # Severity 0: 應該過濾，返回 None
                # Severity 1-4: is_attack=1 (緊急/警告/錯誤)
                # Severity 5-7: is_attack=0 (通知/資訊/除錯)
                severity_int = int(result["Severity"])
                if severity_int == 0:
                    # Severity 0 是硬體問題，應過濾
                    return None
                elif severity_int >= 1 and severity_int <= 4:
                    result["is_attack"] = 1
                elif severity_int >= 5:
                    result["is_attack"] = 0
            
            # 解析 Action（Built, Teardown, Denied 等）
            action_keywords = [
                "built", "teardown", "denied", "deny", "permitted", "permit",
                "failed", "error", "warning", "alert", "blocked", "dropped"
            ]
            line_lower = line.lower()
            for keyword in action_keywords:
                if keyword in line_lower:
                    result["Action"] = keyword
                    break
            
            # 解析 Protocol
            if "tcp" in line_lower:
                result["Protocol"] = "TCP"
            elif "udp" in line_lower:
                result["Protocol"] = "UDP"
            elif "icmp" in line_lower:
                result["Protocol"] = "ICMP"
            
            # 解析 IP 地址和端口
            # 格式：192.168.20.120/30117 或 192.168.20.120:30117
            ip_port_pattern = r'(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})[/:](\d+)'
            ip_matches = re.findall(ip_port_pattern, line)
            
            if len(ip_matches) >= 2:
                # 第一個通常是 source
                result["SourceIP"] = ip_matches[0][0]
                result["SourcePort"] = ip_matches[0][1]
                # 第二個通常是 destination
                result["DestinationIP"] = ip_matches[1][0]
                result["DestinationPort"] = ip_matches[1][1]
            elif len(ip_matches) == 1:
                result["SourceIP"] = ip_matches[0][0]
                result["SourcePort"] = ip_matches[0][1]
            
            # 解析 Bytes
            bytes_match = re.search(r'(\d+)\s*bytes?', line, re.IGNORECASE)
            if bytes_match:
                result["Bytes"] = bytes_match.group(1)
            
            # 解析 Duration
            duration_match = re.search(r'duration\s*[:=]?\s*(\d+)', line, re.IGNORECASE)
            if duration_match:
                result["Duration"] = duration_match.group(1)
            
            return result
            
        except Exception as e:
            self.logger.error(f"解析日誌失敗：{line[:50]}... - {e}")
            return None
    
    def parse_csv_line(self, row: Dict) -> Optional[Dict]:
        """
        解析已經是 CSV 格式的資料
        
        Args:
            row: CSV 行資料（字典格式）
            
        Returns:
            標準化後的字典
        """
        try:
            result = {
                "raw_log": row.get("raw_log", row.get("Description", "")),
                "Severity": str(row.get("Severity", "")),
                "SyslogID": str(row.get("SyslogID", "")),
                "Datetime": row.get("Datetime", ""),
                "SourceIP": row.get("SourceIP", ""),
                "SourcePort": str(row.get("SourcePort", "0")),
                "DestinationIP": row.get("DestinationIP", ""),
                "DestinationPort": str(row.get("DestinationPort", "0")),
                "Protocol": self._normalize_protocol(row.get("Protocol", "")),
                "Action": self._normalize_action(row.get("Action", "")),
                "Description": row.get("Description", ""),
                "Bytes": str(row.get("Bytes", "0")),
                "Duration": str(row.get("Duration", "0")),
                "is_attack": 0
            }
            
            # 根據 Severity 建立 is_attack
            if result["Severity"]:
                try:
                    severity_int = int(result["Severity"])
                    if severity_int >= 1 and severity_int <= 4:
                        result["is_attack"] = 1
                    elif severity_int >= 5:
                        result["is_attack"] = 0
                except:
                    result["is_attack"] = 0
            
            return result
            
        except Exception as e:
            self.logger.error(f"解析 CSV 行失敗：{e}")
            return None
    
    def _normalize_protocol(self, protocol: str) -> str:
        """標準化協定名稱"""
        if not protocol:
            return "unknown"
        
        protocol = str(protocol).strip().upper()
        
        # 如果是數字，轉換為名稱
        if protocol.isdigit():
            return PROTOCOL_MAP.get(protocol, protocol)
        
        return protocol
    
    def _normalize_action(self, action: str) -> str:
        """標準化動作名稱"""
        if not action:
            return "unknown"
        
        action = str(action).strip().lower()
        
        # 統一動作名稱
        action_map = {
            "1": "built",
            "2": "teardown",
            "built": "built",
            "teardown": "teardown",
            "denied": "deny",
            "deny": "deny",
            "permitted": "permit",
            "permit": "permit",
            "dropped": "drop",
            "drop": "drop",
            "blocked": "block",
            "block": "block"
        }
        
        return action_map.get(action, action)
    
    def should_filter_severity_0(self, severity: str) -> bool:
        """
        判斷是否應該過濾 severity 0 的記錄
        
        Severity 0 (emergencies) 通常代表硬體損壞，
        不在本系統分析範圍內
        """
        try:
            return int(severity) == 0
        except:
            return False


# 便利函式
def parse_cisco_log(line: str) -> Optional[Dict]:
    """快速解析單行 Cisco ASA 日誌"""
    parser = CiscoASALogParser()
    return parser.parse_syslog_line(line)


def parse_cisco_csv_row(row: Dict) -> Optional[Dict]:
    """快速解析 CSV 格式的 Cisco ASA 資料"""
    parser = CiscoASALogParser()
    return parser.parse_csv_line(row)
