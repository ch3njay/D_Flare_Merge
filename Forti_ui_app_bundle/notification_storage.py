# 通知記錄持久化儲存模組
from __future__ import annotations

import sqlite3
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

# 添加 ui_shared 模組路徑
_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT / "ui_shared") not in sys.path:
    sys.path.insert(0, str(_ROOT / "ui_shared"))

from notification_models import NotificationMessage, SEVERITY_LABELS


class NotificationStorage:
    """通知記錄持久化儲存管理器。"""
    
    def __init__(self, db_path: str = "notifications.db"):
        """初始化通知儲存。
        
        Args:
            db_path: SQLite 資料庫檔案路徑
        """
        self.db_path = db_path
        self._init_database()
    
    def _init_database(self) -> None:
        """初始化資料庫結構。"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS notifications (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp REAL NOT NULL,
                    severity INTEGER NOT NULL,
                    source_ip TEXT,
                    description TEXT,
                    suggestion TEXT,
                    aggregated_count INTEGER DEFAULT 1,
                    time_window_start TEXT,
                    time_window_end TEXT,
                    match_signature TEXT,
                    file_path TEXT,
                    file_hash TEXT,
                    status TEXT DEFAULT 'sent',
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS notification_descriptions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    notification_id INTEGER,
                    description TEXT,
                    FOREIGN KEY (notification_id) REFERENCES notifications (id)
                )
            """)
            
            # 創建索引加速查詢
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_notifications_timestamp
                ON notifications (timestamp)
            """)

            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_notifications_file_hash
                ON notifications (file_hash)
            """)

            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_notifications_severity
                ON notifications (severity)
            """)

    def save_notification(
        self,
        message: NotificationMessage,
        file_path: str = "",
        file_hash: str = "",
        status: str = "sent"
    ) -> int:
        """儲存通知記錄。
        
        Args:
            message: 通知訊息物件
            file_path: 來源檔案路徑
            file_hash: 檔案雜湊值
            status: 通知狀態 (sent, failed, pending)
            
        Returns:
            通知記錄的 ID
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # 插入主要通知記錄
            cursor.execute("""
                INSERT INTO notifications (
                    timestamp, severity, source_ip, description, suggestion,
                    aggregated_count, time_window_start, time_window_end,
                    match_signature, file_path, file_hash, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                time.time(),
                message.severity,
                message.source_ip or "",
                message.description or "",
                message.suggestion or "",
                message.aggregated_count,
                message.time_window[0] if message.time_window else None,
                message.time_window[1] if message.time_window else None,
                message.match_signature or "",
                file_path,
                file_hash,
                status
            ))
            
            notification_id = cursor.lastrowid
            
            # 儲存聚合描述
            if message.aggregated_descriptions:
                for desc in message.aggregated_descriptions:
                    if desc and desc.strip():
                        cursor.execute("""
                            INSERT INTO notification_descriptions (
                                notification_id, description)
                            VALUES (?, ?)
                        """, (notification_id, desc.strip()))
            
            return notification_id
    
    def is_duplicate(self, file_hash: str,
                     dedupe_window_hours: int = 1) -> bool:
        """檢查是否為重複通知。
        
        Args:
            file_hash: 檔案雜湊值
            dedupe_window_hours: 去重時間窗口（小時）
            
        Returns:
            True 如果是重複通知
        """
        cutoff_time = time.time() - (dedupe_window_hours * 3600)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT COUNT(*) FROM notifications
                WHERE file_hash = ? AND timestamp > ?
            """, (file_hash, cutoff_time))
            
            count = cursor.fetchone()[0]
            return count > 0
    
    def get_recent_notifications(
        self,
        hours: int = 24,
        severity_filter: Optional[List[int]] = None,
        limit: int = 100
    ) -> List[Dict]:
        """取得最近的通知記錄。
        
        Args:
            hours: 時間範圍（小時）
            severity_filter: 嚴重度過濾器
            limit: 最大記錄數
            
        Returns:
            通知記錄列表
        """
        cutoff_time = time.time() - (hours * 3600)
        
        query = """
            SELECT id, timestamp, severity, source_ip, description, suggestion,
                   aggregated_count, time_window_start, time_window_end,
                   match_signature, file_path, status, created_at
            FROM notifications
            WHERE timestamp > ?
        """
        params = [cutoff_time]
        
        if severity_filter:
            placeholders = ",".join("?" * len(severity_filter))
            query += f" AND severity IN ({placeholders})"
            params.extend(severity_filter)
        
        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            
            notifications = []
            for row in cursor.fetchall():
                # 取得聚合描述
                cursor.execute("""
                    SELECT description FROM notification_descriptions
                    WHERE notification_id = ?
                """, (row[0],))
                
                aggregated_descriptions = [
                    desc[0] for desc in cursor.fetchall()]
                
                notifications.append({
                    "id": row[0],
                    "timestamp": row[1],
                    "datetime": datetime.fromtimestamp(row[1]).strftime(
                        "%Y-%m-%d %H:%M:%S"),
                    "severity": row[2],
                    "severity_label": SEVERITY_LABELS.get(row[2], str(row[2])),
                    "source_ip": row[3],
                    "description": row[4],
                    "suggestion": row[5],
                    "aggregated_count": row[6],
                    "time_window_start": row[7],
                    "time_window_end": row[8],
                    "match_signature": row[9],
                    "file_path": row[10],
                    "status": row[11],
                    "created_at": row[12],
                    "aggregated_descriptions": aggregated_descriptions
                })
            
            return notifications
    
    def get_statistics(self, hours: int = 24) -> Dict:
        """取得通知統計資訊。
        
        Args:
            hours: 統計時間範圍（小時）
            
        Returns:
            統計資訊字典
        """
        cutoff_time = time.time() - (hours * 3600)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # 總通知數
            cursor.execute("""
                SELECT COUNT(*) FROM notifications WHERE timestamp > ?
            """, (cutoff_time,))
            total_count = cursor.fetchone()[0]
            
            # 按嚴重度統計
            cursor.execute("""
                SELECT severity, COUNT(*) FROM notifications
                WHERE timestamp > ?
                GROUP BY severity
                ORDER BY severity DESC
            """, (cutoff_time,))
            severity_stats = dict(cursor.fetchall())
            
            # 按狀態統計
            cursor.execute("""
                SELECT status, COUNT(*) FROM notifications
                WHERE timestamp > ?
                GROUP BY status
            """, (cutoff_time,))
            status_stats = dict(cursor.fetchall())
            
            # 最近一小時活動
            recent_cutoff = time.time() - 3600
            cursor.execute("""
                SELECT COUNT(*) FROM notifications WHERE timestamp > ?
            """, (recent_cutoff,))
            recent_count = cursor.fetchone()[0]
            
            return {
                "total_count": total_count,
                "severity_stats": severity_stats,
                "status_stats": status_stats,
                "recent_count": recent_count,
                "time_range_hours": hours
            }
    
    def cleanup_old_notifications(self, keep_days: int = 30) -> int:
        """清理舊的通知記錄。
        
        Args:
            keep_days: 保留天數
            
        Returns:
            刪除的記錄數
        """
        cutoff_time = time.time() - (keep_days * 24 * 3600)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # 首先刪除關聯的描述記錄
            cursor.execute("""
                DELETE FROM notification_descriptions
                WHERE notification_id IN (
                    SELECT id FROM notifications WHERE timestamp < ?
                )
            """, (cutoff_time,))
            
            # 然後刪除主通知記錄
            cursor.execute("""
                DELETE FROM notifications WHERE timestamp < ?
            """, (cutoff_time,))
            
            deleted_count = cursor.rowcount
            
            # 清理資料庫
            conn.execute("VACUUM")
            
            return deleted_count
    
    def update_notification_status(self, notification_id: int, status: str) -> bool:
        """更新通知狀態。
        
        Args:
            notification_id: 通知 ID
            status: 新狀態
            
        Returns:
            是否更新成功
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE notifications SET status = ? WHERE id = ?
            """, (status, notification_id))
            
            return cursor.rowcount > 0


# 全域儲存實例
_notification_storage: Optional[NotificationStorage] = None


def get_notification_storage(db_path: str = "notifications.db") -> NotificationStorage:
    """取得全域通知儲存實例。"""
    global _notification_storage
    if _notification_storage is None:
        _notification_storage = NotificationStorage(db_path)
    return _notification_storage


__all__ = ["NotificationStorage", "get_notification_storage"]