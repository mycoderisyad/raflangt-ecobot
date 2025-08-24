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

    def log_interaction(
        self,
        user_phone: str,
        interaction_type: str,
        message_content: str = None,
        response_content: str = None,
        success: bool = True,
        response_time: float = None,
    ) -> bool:
        """Log user interaction"""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO user_interactions 
                    (user_phone, interaction_type, message_content, response_content, 
                     success, response_time)
                    VALUES (?, ?, ?, ?, ?, ?)
                """,
                    (
                        user_phone,
                        interaction_type,
                        message_content,
                        response_content,
                        success,
                        response_time,
                    ),
                )

                conn.commit()
                return True

        except Exception as e:
            logger.error(f"Error logging interaction: {str(e)}")
            return False

    def get_user_interactions(
        self, user_phone: str, limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get user's recent interactions"""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT * FROM user_interactions 
                    WHERE user_phone = ? 
                    ORDER BY created_at DESC 
                    LIMIT ?
                """,
                    (user_phone, limit),
                )

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
                cursor.execute(
                    """
                    SELECT COUNT() as total 
                    FROM user_interactions 
                    WHERE created_at >= ?
                """,
                    (start_date,),
                )
                total = cursor.fetchone()["total"]

                # Interactions by type
                cursor.execute(
                    """
                    SELECT interaction_type, COUNT() as count 
                    FROM user_interactions 
                    WHERE created_at >= ?
                    GROUP BY interaction_type
                    ORDER BY count DESC
                """,
                    (start_date,),
                )
                by_type = {
                    row["interaction_type"]: row["count"] for row in cursor.fetchall()
                }

                # Success rate
                cursor.execute(
                    """
                    SELECT 
                        COUNT() as total,
                        SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as successful
                    FROM user_interactions 
                    WHERE created_at >= ?
                """,
                    (start_date,),
                )
                result = cursor.fetchone()
                success_rate = (
                    (result["successful"] / result["total"] * 100)
                    if result["total"] > 0
                    else 0
                )

                # Average response time
                cursor.execute(
                    """
                    SELECT AVG(response_time) as avg_response_time 
                    FROM user_interactions 
                    WHERE created_at >= ? AND response_time IS NOT NULL
                """,
                    (start_date,),
                )
                avg_response_time = cursor.fetchone()["avg_response_time"] or 0

                return {
                    "total_interactions": total,
                    "by_type": by_type,
                    "success_rate": round(success_rate, 2),
                    "avg_response_time": round(avg_response_time, 3),
                    "period_days": days,
                }

        except Exception as e:
            logger.error(f"Error getting interaction stats: {str(e)}")
            return {}


class SystemLogModel:
    """System log model for audit and debugging"""

    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager

    def log_event(
        self,
        level: str,
        message: str,
        module: str = None,
        user_phone: str = None,
        extra_data: Dict[str, Any] = None,
    ) -> bool:
        """Log system event"""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO system_logs 
                    (level, message, module, user_phone, extra_data)
                    VALUES (?, ?, ?, ?, ?)
                """,
                    (
                        level,
                        message,
                        module,
                        user_phone,
                        json.dumps(extra_data) if extra_data else None,
                    ),
                )

                conn.commit()
                return True

        except Exception as e:
            logger.error(f"Error logging system event: {str(e)}")
            return False

    def get_logs(
        self,
        level: str = None,
        module: str = None,
        user_phone: str = None,
        days: int = 7,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Get system logs with filters"""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()

                query = """
                    SELECT * FROM system_logs 
                    WHERE created_at >= ?
                """
                params = [datetime.now() - timedelta(days=days)]

                if level:
                    query += " AND level = ?"
                    params.append(level)

                if module:
                    query += " AND module = ?"
                    params.append(module)

                if user_phone:
                    query += " AND user_phone = ?"
                    params.append(user_phone)

                query += " ORDER BY created_at DESC LIMIT ?"
                params.append(limit)

                cursor.execute(query, params)

                logs = []
                for row in cursor.fetchall():
                    log = dict(row)
                    try:
                        if log["extra_data"]:
                            log["extra_data"] = json.loads(log["extra_data"])
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
                cursor.execute(
                    """
                    SELECT level, COUNT() as count 
                    FROM system_logs 
                    WHERE created_at >= ? AND level IN ('WARNING', 'ERROR', 'CRITICAL')
                    GROUP BY level
                """,
                    (start_date,),
                )
                error_counts = {row["level"]: row["count"] for row in cursor.fetchall()}

                # Recent critical errors
                cursor.execute(
                    """
                    SELECT message, module, created_at 
                    FROM system_logs 
                    WHERE created_at >= ? AND level = 'CRITICAL'
                    ORDER BY created_at DESC 
                    LIMIT 10
                """,
                    (start_date,),
                )
                critical_errors = [dict(row) for row in cursor.fetchall()]

                # Error trends by module
                cursor.execute(
                    """
                    SELECT module, COUNT() as count 
                    FROM system_logs 
                    WHERE created_at >= ? AND level IN ('ERROR', 'CRITICAL')
                    GROUP BY module
                    ORDER BY count DESC
                    LIMIT 10
                """,
                    (start_date,),
                )
                error_by_module = {
                    row["module"]: row["count"] for row in cursor.fetchall()
                }

                return {
                    "error_counts": error_counts,
                    "critical_errors": critical_errors,
                    "error_by_module": error_by_module,
                    "period_days": days,
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

                cursor.execute(
                    """
                    DELETE FROM system_logs 
                    WHERE created_at < ?
                """,
                    (cutoff_date,),
                )

                deleted_count = cursor.rowcount
                conn.commit()

                # Log the cleanup
                self.log_event(
                    "INFO",
                    f"Log cleanup completed: {deleted_count} logs deleted",
                    "SystemLogModel",
                    admin_phone,
                    {"deleted_count": deleted_count, "cutoff_days": days},
                )

                return True

        except Exception as e:
            logger.error(f"Error cleaning up logs: {str(e)}")
            return False


class SystemModel:
    """Main system model that aggregates various system statistics and operations"""

    def __init__(self):
        from .base import DatabaseManager

        self.db = DatabaseManager()
        self.interaction_model = UserInteractionModel(self.db)
        self.log_model = SystemLogModel(self.db)

    def get_user_statistics(self) -> Dict[str, Any]:
        """Get comprehensive user statistics"""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()

                # Basic user counts
                cursor.execute(
                    """
                    SELECT 
                        COUNT(*) as total_users,
                        SUM(CASE WHEN role='admin' THEN 1 ELSE 0 END) as admin_count,
                        SUM(CASE WHEN role='koordinator' THEN 1 ELSE 0 END) as koordinator_count,
                        SUM(CASE WHEN role='warga' THEN 1 ELSE 0 END) as warga_count,
                        SUM(CASE WHEN registration_status='registered' THEN 1 ELSE 0 END) as registered_count,
                        SUM(CASE WHEN registration_status='pending' THEN 1 ELSE 0 END) as pending_count,
                        SUM(CASE WHEN is_active=1 THEN 1 ELSE 0 END) as active_count
                    FROM users
                """
                )
                user_stats = dict(cursor.fetchone())

                # Active users today
                cursor.execute(
                    """
                    SELECT COUNT(DISTINCT user_phone) as active_today
                    FROM user_interactions 
                    WHERE DATE(created_at) = DATE('now')
                """
                )
                user_stats.update(cursor.fetchone())

                # Total points distributed
                cursor.execute("SELECT SUM(points) as total_points FROM users")
                user_stats.update(cursor.fetchone())

                return user_stats

        except Exception as e:
            logger.error(f"Error getting user statistics: {str(e)}")
            return {}

    def get_system_health(self) -> Dict[str, Any]:
        """Get overall system health metrics"""
        try:
            # Get error counts from last 24 hours
            error_summary = self.log_model.get_error_summary(days=1)

            # Get interaction stats
            interaction_stats = self.interaction_model.get_interaction_stats(days=1)

            # Database size and performance
            with self.db.get_connection() as conn:
                cursor = conn.cursor()

                # Recent activity indicators
                cursor.execute(
                    """
                    SELECT 
                        (SELECT COUNT(*) FROM user_interactions WHERE DATE(created_at) = DATE('now')) as interactions_today,
                        (SELECT COUNT(*) FROM waste_classifications WHERE DATE(created_at) = DATE('now')) as classifications_today,
                        (SELECT COUNT(*) FROM system_logs WHERE level='ERROR' AND DATE(created_at) = DATE('now')) as errors_today
                """
                )
                activity = dict(cursor.fetchone())

                # System status assessment
                health_score = 100
                status_messages = []

                # Check error rates
                if activity["errors_today"] > 10:
                    health_score -= 20
                    status_messages.append("High error rate detected")
                elif activity["errors_today"] > 5:
                    health_score -= 10
                    status_messages.append("Moderate error rate")

                # Check activity levels
                if activity["interactions_today"] < 5:
                    health_score -= 15
                    status_messages.append("Low user activity")

                # Check response times
                if interaction_stats.get("avg_response_time", 0) > 2.0:
                    health_score -= 15
                    status_messages.append("Slow response times")

                # Determine overall status
                if health_score >= 90:
                    status = "EXCELLENT"
                elif health_score >= 75:
                    status = "GOOD"
                elif health_score >= 50:
                    status = "WARNING"
                else:
                    status = "CRITICAL"

                return {
                    "status": status,
                    "health_score": health_score,
                    "status_messages": status_messages,
                    "activity": activity,
                    "error_summary": error_summary,
                    "interaction_stats": interaction_stats,
                    "timestamp": datetime.now().isoformat(),
                }

        except Exception as e:
            logger.error(f"Error getting system health: {str(e)}")
            return {
                "status": "ERROR",
                "health_score": 0,
                "status_messages": [f"System health check failed: {str(e)}"],
                "timestamp": datetime.now().isoformat(),
            }

    def get_daily_report(self) -> Dict[str, Any]:
        """Generate daily system report"""
        try:
            user_stats = self.get_user_statistics()
            health = self.get_system_health()

            with self.db.get_connection() as conn:
                cursor = conn.cursor()

                # Waste classification stats
                cursor.execute(
                    """
                    SELECT 
                        waste_type,
                        COUNT(*) as count,
                        AVG(confidence) as avg_confidence
                    FROM waste_classifications 
                    WHERE DATE(created_at) = DATE('now')
                    GROUP BY waste_type
                """
                )
                waste_stats = {
                    row["waste_type"]: {
                        "count": row["count"],
                        "avg_confidence": round(row["avg_confidence"], 2),
                    }
                    for row in cursor.fetchall()
                }

                # Collection points status
                cursor.execute(
                    """
                    SELECT 
                        COUNT(*) as total_points,
                        SUM(CASE WHEN is_active=1 THEN 1 ELSE 0 END) as active_points
                    FROM collection_points
                """
                )
                collection_stats = dict(cursor.fetchone())

                return {
                    "date": datetime.now().strftime("%Y-%m-%d"),
                    "user_stats": user_stats,
                    "system_health": health,
                    "waste_classifications": waste_stats,
                    "collection_points": collection_stats,
                    "generated_at": datetime.now().isoformat(),
                }

        except Exception as e:
            logger.error(f"Error generating daily report: {str(e)}")
            return {}

    def log_system_event(
        self,
        level: str,
        message: str,
        module: str = None,
        user_phone: str = None,
        extra_data: Dict[str, Any] = None,
    ) -> bool:
        """Convenience method to log system events"""
        return self.log_model.log_event(level, message, module, user_phone, extra_data)

    def log_user_interaction(
        self,
        user_phone: str,
        interaction_type: str,
        message_content: str = None,
        response_content: str = None,
        success: bool = True,
        response_time: float = None,
    ) -> bool:
        """Convenience method to log user interactions"""
        return self.interaction_model.log_interaction(
            user_phone,
            interaction_type,
            message_content,
            response_content,
            success,
            response_time,
        )
