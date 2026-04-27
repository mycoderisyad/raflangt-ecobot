"""Conversation history & user memory models — PostgreSQL backed."""

import logging
from typing import Dict, Any, List, Optional

from src.database.connection import get_db

logger = logging.getLogger(__name__)


class ConversationModel:

    def get_recent(self, user_phone: str, limit: int = 20) -> List[Dict[str, Any]]:
        with get_db() as db:
            rows = db.fetchall(
                """SELECT message_role, message_content, created_at
                   FROM conversation_history
                   WHERE user_phone = %s
                   ORDER BY created_at DESC
                   LIMIT %s""",
                (user_phone, limit),
            )
        return list(reversed(rows))

    def add_message(self, user_phone: str, role: str, content: str) -> None:
        with get_db() as db:
            db.execute(
                """INSERT INTO conversation_history (user_phone, message_role, message_content)
                   VALUES (%s, %s, %s)""",
                (user_phone, role, content),
            )

    def get_count(self, user_phone: str) -> int:
        with get_db() as db:
            row = db.fetchone(
                "SELECT COUNT(*) AS cnt FROM conversation_history WHERE user_phone = %s",
                (user_phone,),
            )
            return row["cnt"] if row else 0

    def clear_old(self, user_phone: str, keep_days: int = 30) -> int:
        with get_db() as db:
            return db.execute(
                """DELETE FROM conversation_history
                   WHERE user_phone = %s AND created_at < NOW() - INTERVAL '%s days'""",
                (user_phone, keep_days),
            )


class MemoryModel:

    def get_all_facts(self, user_phone: str) -> Dict[str, Any]:
        with get_db() as db:
            rows = db.fetchall(
                """SELECT memory_key, memory_value, updated_at
                   FROM user_memory WHERE user_phone = %s ORDER BY updated_at DESC""",
                (user_phone,),
            )
        return {r["memory_key"]: {"value": r["memory_value"], "updated_at": str(r["updated_at"])} for r in rows}

    def save_fact(self, user_phone: str, key: str, value: str) -> None:
        with get_db() as db:
            db.execute(
                """INSERT INTO user_memory (user_phone, memory_key, memory_value)
                   VALUES (%s, %s, %s)
                   ON CONFLICT (user_phone, memory_key)
                   DO UPDATE SET memory_value = EXCLUDED.memory_value, updated_at = NOW()""",
                (user_phone, key, value),
            )

    def get_fact(self, user_phone: str, key: str) -> Optional[str]:
        with get_db() as db:
            row = db.fetchone(
                "SELECT memory_value FROM user_memory WHERE user_phone = %s AND memory_key = %s",
                (user_phone, key),
            )
            return row["memory_value"] if row else None

    def delete_fact(self, user_phone: str, key: str) -> bool:
        with get_db() as db:
            return db.execute(
                "DELETE FROM user_memory WHERE user_phone = %s AND memory_key = %s",
                (user_phone, key),
            ) > 0
