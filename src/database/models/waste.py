"""Waste classification model — PostgreSQL backed."""

import logging
from typing import Dict, Any, List, Optional

from src.database.connection import get_db

logger = logging.getLogger(__name__)


class WasteClassificationModel:

    def save_classification(
        self,
        user_phone: str,
        waste_type: str,
        confidence: float,
        classification_method: str = "ai",
        image_url: Optional[str] = None,
    ) -> None:
        with get_db() as db:
            db.execute(
                """INSERT INTO waste_classifications
                   (user_phone, waste_type, confidence, classification_method, image_url)
                   VALUES (%s, %s, %s, %s, %s)""",
                (user_phone, waste_type, confidence, classification_method, image_url),
            )

    def get_user_classifications(self, user_phone: str, limit: int = 20) -> List[Dict[str, Any]]:
        with get_db() as db:
            return db.fetchall(
                """SELECT * FROM waste_classifications
                   WHERE user_phone = %s ORDER BY created_at DESC LIMIT %s""",
                (user_phone, limit),
            )

    def get_statistics(self, days: int = 7) -> Dict[str, Any]:
        with get_db() as db:
            row = db.fetchone(
                """SELECT
                     COUNT(*) AS total,
                     COUNT(*) FILTER (WHERE waste_type = 'ORGANIK') AS organic,
                     COUNT(*) FILTER (WHERE waste_type = 'ANORGANIK') AS inorganic,
                     COUNT(*) FILTER (WHERE waste_type = 'B3') AS b3
                   FROM waste_classifications
                   WHERE created_at >= NOW() - INTERVAL '%s days'""",
                (days,),
            )
            return dict(row) if row else {}
