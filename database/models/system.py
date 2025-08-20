"""
System Models
Mengelola interaction tracking dan system logs
"""

import logging
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from .base import DatabaseManager

logger = logging.getLogger(__name__)

class UserInteractionModel:
    """User interaction model for tracking user activities"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
    
    def log_interaction(self, user_phone: str, interaction_type: str, 
                       message_content: str = None, response_content: str = None,
                       success: bool = True, response_time: float = None) -> bool:
        """Log user interaction"""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO user_interactions 
                    (user_phone, interaction_type, message_content, response_content, 
                     success, response_time)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (user_phone, interaction_type, message_content, response_content,
                      success, response_time))
                
                conn.commit()
                return True
                
        except Exception as e:
            logger.error(f"Error logging interaction: {str(e)}")
            return False
    
    def get_user_interactions(self, user_phone: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get user's recent interactions"""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT * FROM user_interactions 
                    WHERE user_phone = ? 
                    ORDER BY created_at DESC 
                    LIMIT ?
                ''', (user_phone, limit))
                
                return [dict(row) for row in cursor.fetchall()]
                
        except Exception as e:
            logger.error(f"Error getting user interactions: {str(e)}")
            return []
    
    def get_interaction_stats(self, days: int = 7) -> Dict[str, Any]:
        """Get interaction statistics for the last N days"""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                
                start_date = datetime.now() - timedelta(days=days)
                
                # Total interactions
                cursor.execute('''
                    SELECT COUNT(*) as total 
                    FROM user_interactions 
                    WHERE created_at >= ?
                ''', (start_date,))
                total = cursor.fetchone()['total']
                
                # Interactions by type
                cursor.execute('''
                    SELECT interaction_type, COUNT(*) as count 
                    FROM user_interactions 
                    WHERE created_at >= ?
                    GROUP BY interaction_type
                    ORDER BY count DESC
                ''', (start_date,))
                by_type = {row['interaction_type']: row['count'] for row in cursor.fetchall()}
                
                # Success rate
                cursor.execute('''
                    SELECT 
                        COUNT(*) as total,
                        SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as successful
                    FROM user_interactions 
                    WHERE created_at >= ?
                ''', (start_date,))
                result = cursor.fetchone()
                success_rate = (result['successful'] / result['total'] * 100) if result['total'] > 0 else 0
                
                # Average response time
                cursor.execute('''
                    SELECT AVG(response_time) as avg_response_time 
                    FROM user_interactions 
                    WHERE created_at >= ? AND response_time IS NOT NULL
                ''', (start_date,))
                avg_response_time = cursor.fetchone()['avg_response_time'] or 0
                
                return {
                    'total_interactions': total,
                    'by_type': by_type,
                    'success_rate': round(success_rate, 2),
                    'avg_response_time': round(avg_response_time, 3),
                    'period_days': days
                }
                
        except Exception as e:
            logger.error(f"Error getting interaction stats: {str(e)}")
            return {}


class SystemLogModel:
    """System log model for audit and debugging"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
    
    def log_event(self, level: str, message: str, module: str = None, 
                  user_phone: str = None, extra_data: Dict[str, Any] = None) -> bool:
        """Log system event"""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO system_logs 
                    (level, message, module, user_phone, extra_data)
                    VALUES (?, ?, ?, ?, ?)
                ''', (level, message, module, user_phone, 
                      json.dumps(extra_data) if extra_data else None))
                
                conn.commit()
                return True
                
        except Exception as e:
            logger.error(f"Error logging system event: {str(e)}")
            return False
    
    def get_logs(self, level: str = None, module: str = None, 
                 user_phone: str = None, days: int = 7, limit: int = 100) -> List[Dict[str, Any]]:
        """Get system logs with filters"""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                
                query = '''
                    SELECT * FROM system_logs 
                    WHERE created_at >= ?
                '''
                params = [datetime.now() - timedelta(days=days)]
                
                if level:
                    query += ' AND level = ?'
                    params.append(level)
                
                if module:
                    query += ' AND module = ?'
                    params.append(module)
                
                if user_phone:
                    query += ' AND user_phone = ?'
                    params.append(user_phone)
                
                query += ' ORDER BY created_at DESC LIMIT ?'
                params.append(limit)
                
                cursor.execute(query, params)
                
                logs = []
                for row in cursor.fetchall():
                    log = dict(row)
                    try:
                        if log['extra_data']:
                            log['extra_data'] = json.loads(log['extra_data'])
                    except:
                        pass
                    logs.append(log)
                
                return logs
                
        except Exception as e:
            logger.error(f"Error getting logs: {str(e)}")
            return []
    
    def get_error_summary(self, days: int = 7) -> Dict[str, Any]:
        """Get error summary for monitoring"""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                
                start_date = datetime.now() - timedelta(days=days)
                
                # Error count by level
                cursor.execute('''
                    SELECT level, COUNT(*) as count 
                    FROM system_logs 
                    WHERE created_at >= ? AND level IN ('WARNING', 'ERROR', 'CRITICAL')
                    GROUP BY level
                ''', (start_date,))
                error_counts = {row['level']: row['count'] for row in cursor.fetchall()}
                
                # Recent critical errors
                cursor.execute('''
                    SELECT message, module, created_at 
                    FROM system_logs 
                    WHERE created_at >= ? AND level = 'CRITICAL'
                    ORDER BY created_at DESC 
                    LIMIT 10
                ''', (start_date,))
                critical_errors = [dict(row) for row in cursor.fetchall()]
                
                # Error trends by module
                cursor.execute('''
                    SELECT module, COUNT(*) as count 
                    FROM system_logs 
                    WHERE created_at >= ? AND level IN ('ERROR', 'CRITICAL')
                    GROUP BY module
                    ORDER BY count DESC
                    LIMIT 10
                ''', (start_date,))
                error_by_module = {row['module']: row['count'] for row in cursor.fetchall()}
                
                return {
                    'error_counts': error_counts,
                    'critical_errors': critical_errors,
                    'error_by_module': error_by_module,
                    'period_days': days
                }
                
        except Exception as e:
            logger.error(f"Error getting error summary: {str(e)}")
            return {}
    
    def cleanup_old_logs(self, days: int = 30, admin_phone: str = None) -> bool:
        """Clean up old logs (admin only)"""
        if admin_phone:
            from .user import UserModel
            user_model = UserModel(self.db)
            if not user_model.is_admin(admin_phone):
                return False
        
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                
                cutoff_date = datetime.now() - timedelta(days=days)
                
                cursor.execute('''
                    DELETE FROM system_logs 
                    WHERE created_at < ?
                ''', (cutoff_date,))
                
                deleted_count = cursor.rowcount
                conn.commit()
                
                # Log the cleanup
                self.log_event(
                    'INFO',
                    f"Log cleanup completed: {deleted_count} logs deleted",
                    'SystemLogModel',
                    admin_phone,
                    {'deleted_count': deleted_count, 'cutoff_days': days}
                )
                
                return True
                
        except Exception as e:
            logger.error(f"Error cleaning up logs: {str(e)}")
            return False
