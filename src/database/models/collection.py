"""Collection points & schedules models — PostgreSQL backed."""

import json
import logging
from typing import Dict, Any, List, Optional

from src.database.connection import get_db

logger = logging.getLogger(__name__)


class CollectionPointModel:

    def get_all_active(self) -> List[Dict[str, Any]]:
        with get_db() as db:
            return db.fetchall("SELECT * FROM collection_points WHERE is_active = TRUE ORDER BY name")

    def get_by_id(self, point_id: str) -> Optional[Dict[str, Any]]:
        with get_db() as db:
            return db.fetchone("SELECT * FROM collection_points WHERE id = %s", (point_id,))

    def create(self, data: Dict[str, Any]) -> None:
        with get_db() as db:
            db.execute(
                """INSERT INTO collection_points
                   (id, name, type, latitude, longitude, accepted_waste_types, schedule, contact, description)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                (
                    data["id"], data["name"], data["type"],
                    data["latitude"], data["longitude"],
                    json.dumps(data.get("accepted_waste_types", [])),
                    data["schedule"], data.get("contact"), data.get("description"),
                ),
            )

    def update(self, point_id: str, data: Dict[str, Any]) -> bool:
        with get_db() as db:
            return db.execute(
                """UPDATE collection_points
                   SET name=%s, type=%s, latitude=%s, longitude=%s,
                       accepted_waste_types=%s, schedule=%s, contact=%s, description=%s,
                       updated_at=NOW()
                   WHERE id=%s""",
                (
                    data["name"], data["type"], data["latitude"], data["longitude"],
                    json.dumps(data.get("accepted_waste_types", [])),
                    data["schedule"], data.get("contact"), data.get("description"),
                    point_id,
                ),
            ) > 0

    def delete(self, point_id: str) -> bool:
        with get_db() as db:
            return db.execute("DELETE FROM collection_points WHERE id = %s", (point_id,)) > 0


class CollectionScheduleModel:

    def get_all_active(self) -> List[Dict[str, Any]]:
        with get_db() as db:
            return db.fetchall(
                "SELECT * FROM collection_schedules WHERE is_active = TRUE ORDER BY schedule_day, schedule_time"
            )

    def get_by_day(self, day: str) -> List[Dict[str, Any]]:
        with get_db() as db:
            return db.fetchall(
                "SELECT * FROM collection_schedules WHERE schedule_day = %s AND is_active = TRUE",
                (day,),
            )

    def create(self, data: Dict[str, Any]) -> None:
        with get_db() as db:
            db.execute(
                """INSERT INTO collection_schedules
                   (location_name, address, schedule_day, schedule_time, waste_types, contact)
                   VALUES (%s, %s, %s, %s, %s, %s)""",
                (
                    data["location_name"], data["address"],
                    data["schedule_day"], data["schedule_time"],
                    json.dumps(data.get("waste_types", [])),
                    data.get("contact"),
                ),
            )

    def update(self, schedule_id: int, data: Dict[str, Any]) -> bool:
        with get_db() as db:
            return db.execute(
                """UPDATE collection_schedules
                   SET location_name=%s, address=%s, schedule_day=%s, schedule_time=%s,
                       waste_types=%s, contact=%s, updated_at=NOW()
                   WHERE id=%s""",
                (
                    data["location_name"], data["address"],
                    data["schedule_day"], data["schedule_time"],
                    json.dumps(data.get("waste_types", [])),
                    data.get("contact"),
                    schedule_id,
                ),
            ) > 0

    def delete(self, schedule_id: int) -> bool:
        with get_db() as db:
            return db.execute("DELETE FROM collection_schedules WHERE id = %s", (schedule_id,)) > 0
