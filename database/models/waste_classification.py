"""
Waste Classification Model
Mengelola data klasifikasi sampah
"""

import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from .base import DatabaseManager

logger = logging.getLogger(__name__)

class WasteClassificationModel:
    """Waste classification model for database operations"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
    
    def save_classification(self, user_phone: str, image_data: bytes = None, 
                          classification_result: Dict[str, Any] = None,
                          waste_type: str = None, confidence: float = None,
                          classification_method: str = 'ai', image_url: str = None) -> bool:
        """Save waste classification result - supports both new and legacy formats"""
        try:
            # Handle new format with classification_result dict
            if classification_result:
                waste_type = classification_result.get('waste_type')
                confidence = classification_result.get('confidence', 0.0)
                classification_method = classification_result.get('classification_method', 'ai')
            
            # Validate required fields
            if not waste_type or confidence is None:
                logger.error("Missing required classification data")
                return False
            
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO waste_classifications 
                    (user_phone, waste_type, confidence, image_url, classification_method)
                    VALUES (?, ?, ?, ?, ?)
                ''', (user_phone, waste_type, confidence, image_url, classification_method))
                
                conn.commit()
                return True
                
        except Exception as e:
            logger.error(f"Error saving classification: {str(e)}")
            return False
    
    def get_user_classifications(self, user_phone: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get user's recent classifications"""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT  FROM waste_classifications 
                    WHERE user_phone = ? 
                    ORDER BY created_at DESC 
                    LIMIT ?
                ''', (user_phone, limit))
                
                return [dict(row) for row in cursor.fetchall()]
                
        except Exception as e:
            logger.error(f"Error getting user classifications: {str(e)}")
            return []
    
    def get_classification_stats(self, days: int = 7) -> Dict[str, Any]:
        """Get classification statistics for the last N days"""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                
                # Date range
                start_date = datetime.now() - timedelta(days=days)
                
                # Total classifications
                cursor.execute('''
                    SELECT COUNT() as total 
                    FROM waste_classifications 
                    WHERE created_at >= ?
                ''', (start_date,))
                total = cursor.fetchone()['total']
                
                # Classifications by waste type
                cursor.execute('''
                    SELECT waste_type, COUNT() as count 
                    FROM waste_classifications 
                    WHERE created_at >= ?
                    GROUP BY waste_type
                    ORDER BY count DESC
                ''', (start_date,))
                by_type = {row['waste_type']: row['count'] for row in cursor.fetchall()}
                
                # Classifications by method
                cursor.execute('''
                    SELECT classification_method, COUNT() as count 
                    FROM waste_classifications 
                    WHERE created_at >= ?
                    GROUP BY classification_method
                ''', (start_date,))
                by_method = {row['classification_method']: row['count'] for row in cursor.fetchall()}
                
                # Average confidence
                cursor.execute('''
                    SELECT AVG(confidence) as avg_confidence 
                    FROM waste_classifications 
                    WHERE created_at >= ?
                ''', (start_date,))
                avg_confidence = cursor.fetchone()['avg_confidence'] or 0
                
                # Daily breakdown
                cursor.execute('''
                    SELECT DATE(created_at) as date, COUNT() as count 
                    FROM waste_classifications 
                    WHERE created_at >= ?
                    GROUP BY DATE(created_at)
                    ORDER BY date DESC
                ''', (start_date,))
                daily = {row['date']: row['count'] for row in cursor.fetchall()}
                
                return {
                    'total_classifications': total,
                    'by_waste_type': by_type,
                    'by_method': by_method,
                    'average_confidence': round(avg_confidence, 3),
                    'daily_breakdown': daily,
                    'period_days': days
                }
                
        except Exception as e:
            logger.error(f"Error getting classification stats: {str(e)}")
            return {}
    
    def get_top_users(self, limit: int = 10, days: int = 30) -> List[Dict[str, Any]]:
        """Get most active users in classification"""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                
                start_date = datetime.now() - timedelta(days=days)
                
                cursor.execute('''
                    SELECT user_phone, COUNT() as classification_count,
                           AVG(confidence) as avg_confidence
                    FROM waste_classifications 
                    WHERE created_at >= ?
                    GROUP BY user_phone
                    ORDER BY classification_count DESC
                    LIMIT ?
                ''', (start_date, limit))
                
                return [dict(row) for row in cursor.fetchall()]
                
        except Exception as e:
            logger.error(f"Error getting top users: {str(e)}")
            return []
    
    def delete_user_classifications(self, user_phone: str, admin_phone: str = None) -> bool:
        """Delete all classifications for a user (admin only)"""
        if admin_phone:
            from .user import UserModel
            user_model = UserModel(self.db)
            if not user_model.is_admin(admin_phone):
                return False
        
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    DELETE FROM waste_classifications 
                    WHERE user_phone = ?
                ''', (user_phone,))
                
                conn.commit()
                return True
                
        except Exception as e:
            logger.error(f"Error deleting user classifications: {str(e)}")
            return False
