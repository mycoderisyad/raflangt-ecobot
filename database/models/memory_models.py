"""
Real Memory Models for AI Agent
Provides real memory functionality using database tables
"""
import json
import logging
from typing import Dict, List, Any
from datetime import datetime
from core.database_manager import get_database_manager

logger = logging.getLogger(__name__)


class RealMemoryModel:
    """Real memory model for storing user facts using database"""

    def __init__(self):
        self.logger = logger
        self.db_manager = get_database_manager()

    def get_all_user_facts(self, user_phone: str) -> Dict[str, Any]:
        """Get all facts for a user from database"""
        try:
            query = """
                SELECT memory_key, memory_value, updated_at 
                FROM user_memory 
                WHERE user_phone = ? 
                ORDER BY updated_at DESC
            """
            results = self.db_manager.execute_query(query, (user_phone,))
            
            facts = {}
            for row in results:
                facts[row['memory_key']] = {
                    'value': row['memory_value'],
                    'updated_at': row['updated_at']
                }
            
            return facts
        except Exception as e:
            logger.error(f"Error getting user facts: {str(e)}")
            return {}

    def save_user_fact(self, user_phone: str, key: str, value: str):
        """Save a user fact to database"""
        try:
            # Check if fact already exists
            check_query = "SELECT id FROM user_memory WHERE user_phone = ? AND memory_key = ?"
            existing = self.db_manager.execute_query(check_query, (user_phone, key))
            
            if existing:
                # Update existing fact
                update_query = """
                    UPDATE user_memory 
                    SET memory_value = ?, updated_at = CURRENT_TIMESTAMP 
                    WHERE user_phone = ? AND memory_key = ?
                """
                self.db_manager.execute_update(update_query, (value, user_phone, key))
                logger.info(f"Updated fact for {user_phone}: {key} = {value}")
            else:
                # Insert new fact
                insert_query = """
                    INSERT INTO user_memory (user_phone, memory_key, memory_value, created_at, updated_at)
                    VALUES (?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                """
                self.db_manager.execute_update(insert_query, (user_phone, key, value))
                logger.info(f"Saved new fact for {user_phone}: {key} = {value}")
                
        except Exception as e:
            logger.error(f"Error saving user fact: {str(e)}")

    def get_user_fact(self, user_phone: str, key: str) -> str:
        """Get specific user fact from database"""
        try:
            query = "SELECT memory_value FROM user_memory WHERE user_phone = ? AND memory_key = ?"
            results = self.db_manager.execute_query(query, (user_phone, key))
            
            if results:
                return results[0]['memory_value']
            return None
        except Exception as e:
            logger.error(f"Error getting user fact: {str(e)}")
            return None

    def delete_user_fact(self, user_phone: str, key: str) -> bool:
        """Delete specific user fact from database"""
        try:
            query = "DELETE FROM user_memory WHERE user_phone = ? AND memory_key = ?"
            result = self.db_manager.execute_update(query, (user_phone, key))
            return result > 0
        except Exception as e:
            logger.error(f"Error deleting user fact: {str(e)}")
            return False


class RealConversationModel:
    """Real conversation model for storing conversation history using database"""

    def __init__(self):
        self.logger = logger
        self.db_manager = get_database_manager()

    def get_recent_conversation(
        self, user_phone: str, limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get recent conversation history from database"""
        try:
            query = """
                SELECT message_role, message_content, created_at
                FROM conversation_history 
                WHERE user_phone = ? 
                ORDER BY created_at DESC 
                LIMIT ?
            """
            results = self.db_manager.execute_query(query, (user_phone, limit))
            
            # Convert to expected format and reverse order (oldest first)
            conversations = []
            for row in reversed(results):
                conversations.append({
                    'role': row['message_role'],
                    'content': row['message_content'],
                    'timestamp': row['created_at']
                })
            
            return conversations
        except Exception as e:
            logger.error(f"Error getting conversation history: {str(e)}")
            return []

    def add_message(self, user_phone: str, role: str, content: str):
        """Add a message to conversation history in database"""
        try:
            query = """
                INSERT INTO conversation_history (user_phone, message_role, message_content, created_at)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            """
            self.db_manager.execute_update(query, (user_phone, role, content))
            logger.info(f"Saved message for {user_phone}: {role} - {content[:50]}...")
            
        except Exception as e:
            logger.error(f"Error saving message: {str(e)}")

    def get_conversation_count(self, user_phone: str) -> int:
        """Get total conversation count for a user"""
        try:
            query = "SELECT COUNT(*) as count FROM conversation_history WHERE user_phone = ?"
            results = self.db_manager.execute_query(query, (user_phone,))
            
            if results:
                return results[0]['count']
            return 0
        except Exception as e:
            logger.error(f"Error getting conversation count: {str(e)}")
            return 0

    def clear_old_conversations(self, user_phone: str, keep_days: int = 30):
        """Clear old conversations older than specified days"""
        try:
            query = """
                DELETE FROM conversation_history 
                WHERE user_phone = ? 
                AND created_at < datetime('now', '-{} days')
            """.format(keep_days)
            
            result = self.db_manager.execute_update(query, (user_phone,))
            logger.info(f"Cleared {result} old conversations for {user_phone}")
            
        except Exception as e:
            logger.error(f"Error clearing old conversations: {str(e)}")

    def get_conversation_summary(self, user_phone: str, days: int = 7) -> Dict[str, Any]:
        """Get conversation summary for the last N days"""
        try:
            query = """
                SELECT 
                    COUNT(*) as total_messages,
                    COUNT(CASE WHEN message_role = 'user' THEN 1 END) as user_messages,
                    COUNT(CASE WHEN message_role = 'assistant' THEN 1 END) as bot_messages,
                    MIN(created_at) as first_message,
                    MAX(created_at) as last_message
                FROM conversation_history 
                WHERE user_phone = ? 
                AND created_at >= datetime('now', '-{} days')
            """.format(days)
            
            results = self.db_manager.execute_query(query, (user_phone,))
            
            if results:
                return results[0]
            return {}
            
        except Exception as e:
            logger.error(f"Error getting conversation summary: {str(e)}")
            return {}

    def get_conversation_topics(self, user_phone: str, limit: int = 10) -> List[str]:
        """Get most common conversation topics based on keywords"""
        try:
            query = """
                SELECT message_content
                FROM conversation_history 
                WHERE user_phone = ? 
                AND message_role = 'user'
                ORDER BY created_at DESC 
                LIMIT ?
            """
            results = self.db_manager.execute_query(query, (user_phone, limit))
            
            # Simple keyword extraction (can be enhanced with NLP)
            topics = []
            for row in results:
                content = row['message_content'].lower()
                if 'sampah' in content or 'waste' in content:
                    topics.append('Waste Management')
                elif 'jadwal' in content or 'schedule' in content:
                    topics.append('Collection Schedule')
                elif 'lokasi' in content or 'location' in content:
                    topics.append('Collection Points')
                elif 'organik' in content or 'organic' in content:
                    topics.append('Organic Waste')
                elif 'daur ulang' in content or 'recycle' in content:
                    topics.append('Recycling')
                elif 'foto' in content or 'image' in content:
                    topics.append('Image Analysis')
                elif 'poin' in content or 'points' in content:
                    topics.append('Reward Points')
            
            # Return unique topics
            return list(set(topics))
            
        except Exception as e:
            logger.error(f"Error getting conversation topics: {str(e)}")
            return []


def get_memory_models():
    """Get real memory model instances"""
    return RealMemoryModel(), RealConversationModel()
