"""System logs & user interactions models — PostgreSQL backed."""

import json
import logging
from typing import Dict, Any, List, Optional

from src.database.connection import get_db

logger = logging.getLogger(__name__)


class UserInteractionModel:

    def log_interaction(
        self,
        user_phone: str,
        interaction_type: str,
        message_content: str = "",
        response_content: str = "",
        success: bool = True,
        response_time: float = 0.0,
    ) -> None:
        with get_db() as db:
            db.execute(
                """INSERT INTO user_interactions
                   (user_phone, interaction_type, message_content, response_content, success, response_time)
                   VALUES (%s, %s, %s, %s, %s, %s)""",
                (user_phone, interaction_type, message_content, response_content, success, response_time),
            )

    def get_stats(self, days: int = 7) -> Dict[str, Any]:
        with get_db() as db:
            row = db.fetchone(
                """SELECT
                     COUNT(DISTINCT user_phone) AS active_users,
                     COUNT(*) AS total_interactions,
                     COUNT(*) FILTER (WHERE interaction_type = 'image') AS images_processed
                   FROM user_interactions
                   WHERE created_at >= NOW() - INTERVAL '%s days'""",
                (days,),
            )
            return dict(row) if row else {}


class SystemLogModel:

    def log(self, level: str, message: str, module: str = "", user_phone: str = "", extra: dict = None) -> None:
        with get_db() as db:
            db.execute(
                """INSERT INTO system_logs (level, message, module, user_phone, extra_data)
                   VALUES (%s, %s, %s, %s, %s)""",
                (level, message, module, user_phone, json.dumps(extra) if extra else None),
            )

    def get_recent(self, limit: int = 50) -> List[Dict[str, Any]]:
        with get_db() as db:
            return db.fetchall("SELECT * FROM system_logs ORDER BY created_at DESC LIMIT %s", (limit,))
