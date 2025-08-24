"""
Collection Points Model
Mengelola data titik pengumpulan sampah
"""

import logging
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from .base import DatabaseManager

logger = logging.getLogger(__name__)


class CollectionPointModel:
    """Collection point model for database operations"""

    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager

    def create_collection_point(
        self, data: Dict[str, Any], admin_phone: str = None
    ) -> bool:
        """Create new collection point (admin only)"""
        if admin_phone:
            from .user import UserModel

            user_model = UserModel(self.db)
            if not user_model.is_admin(admin_phone):
                return False

        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()

                cursor.execute(
                    """
                    INSERT INTO collection_points 
                    (id, name, type, latitude, longitude, accepted_waste_types, 
                     schedule, contact, description)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        data.get(
                            "id", f"cp_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                        ),
                        data["name"],
                        data["type"],
                        data["latitude"],
                        data["longitude"],
                        json.dumps(data["accepted_waste_types"]),
                        data["schedule"],
                        data.get("contact", ""),
                        data.get("description", ""),
                    ),
                )

                conn.commit()
                return True

        except Exception as e:
            logger.error(f"Error creating collection point: {str(e)}")
            return False

    def get_all_collection_points(self) -> List[Dict[str, Any]]:
        """Get all active collection points"""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT * FROM collection_points 
                    WHERE is_active = 1
                    ORDER BY name
                """
                )

                points = []
                for row in cursor.fetchall():
                    point = dict(row)
                    # Parse JSON fields
                    try:
                        point["accepted_waste_types"] = json.loads(
                            point["accepted_waste_types"]
                        )
                    except:
                        point["accepted_waste_types"] = []
                    points.append(point)

                return points

        except Exception as e:
            logger.error(f"Error getting collection points: {str(e)}")
            return []

    def get_collection_point_by_id(self, point_id: str) -> Optional[Dict[str, Any]]:
        """Get collection point by ID"""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT * FROM collection_points 
                    WHERE id = ? AND is_active = 1
                """,
                    (point_id,),
                )

                row = cursor.fetchone()
                if row:
                    point = dict(row)
                    try:
                        point["accepted_waste_types"] = json.loads(
                            point["accepted_waste_types"]
                        )
                    except:
                        point["accepted_waste_types"] = []
                    return point

                return None

        except Exception as e:
            logger.error(f"Error getting collection point by ID: {str(e)}")
            return None

    def update_collection_point(
        self, point_id: str, data: Dict[str, Any], admin_phone: str = None
    ) -> bool:
        """Update collection point (admin only)"""
        if admin_phone:
            from .user import UserModel

            user_model = UserModel(self.db)
            if not user_model.is_admin(admin_phone):
                return False

        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()

                # Build update query dynamically
                update_fields = []
                params = []

                for key, value in data.items():
                    if key in [
                        "name",
                        "type",
                        "latitude",
                        "longitude",
                        "schedule",
                        "contact",
                        "description",
                    ]:
                        update_fields.append(f"{key} = ?")
                        params.append(value)
                    elif key == "accepted_waste_types":
                        update_fields.append("accepted_waste_types = ?")
                        params.append(json.dumps(value))

                if not update_fields:
                    return False

                update_fields.append("updated_at = CURRENT_TIMESTAMP")
                params.append(point_id)

                query = f"""
                    UPDATE collection_points 
                    SET {', '.join(update_fields)}
                    WHERE id = ?
                """

                cursor.execute(query, params)
                conn.commit()

                return cursor.rowcount > 0

        except Exception as e:
            logger.error(f"Error updating collection point: {str(e)}")
            return False

    def delete_collection_point(self, point_id: str, admin_phone: str = None) -> bool:
        """Soft delete collection point (admin only)"""
        if admin_phone:
            from .user import UserModel

            user_model = UserModel(self.db)
            if not user_model.is_admin(admin_phone):
                return False

        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    UPDATE collection_points 
                    SET is_active = 0, updated_at = CURRENT_TIMESTAMP 
                    WHERE id = ?
                """,
                    (point_id,),
                )

                conn.commit()
                return cursor.rowcount > 0

        except Exception as e:
            logger.error(f"Error deleting collection point: {str(e)}")
            return False

    def get_collection_points_by_waste_type(
        self, waste_type: str
    ) -> List[Dict[str, Any]]:
        """Get collection points that accept specific waste type"""
        try:
            points = self.get_all_collection_points()
            filtered_points = []

            for point in points:
                if waste_type.lower() in [
                    wt.lower() for wt in point["accepted_waste_types"]
                ]:
                    filtered_points.append(point)

            return filtered_points

        except Exception as e:
            logger.error(f"Error filtering collection points by waste type: {str(e)}")
            return []


class CollectionScheduleModel:
    """Collection schedule model for database operations"""

    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager

    def create_schedule(self, data: Dict[str, Any], admin_phone: str = None) -> bool:
        """Create new collection schedule (admin only)"""
        if admin_phone:
            from .user import UserModel

            user_model = UserModel(self.db)
            if not user_model.is_admin(admin_phone):
                return False

        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()

                cursor.execute(
                    """
                    INSERT INTO collection_schedules 
                    (location_name, address, schedule_day, schedule_time, waste_types, contact)
                    VALUES (?, ?, ?, ?, ?, ?)
                """,
                    (
                        data["location_name"],
                        data["address"],
                        data["schedule_day"],
                        data["schedule_time"],
                        json.dumps(data["waste_types"]),
                        data.get("contact", ""),
                    ),
                )

                conn.commit()
                return True

        except Exception as e:
            logger.error(f"Error creating schedule: {str(e)}")
            return False

    def get_all_schedules(self) -> List[Dict[str, Any]]:
        """Get all active schedules"""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT  FROM collection_schedules 
                    WHERE is_active = 1
                    ORDER BY location_name, schedule_day
                """
                )

                schedules = []
                for row in cursor.fetchall():
                    schedule = dict(row)
                    try:
                        schedule["waste_types"] = json.loads(schedule["waste_types"])
                    except:
                        schedule["waste_types"] = []
                    schedules.append(schedule)

                return schedules

        except Exception as e:
            logger.error(f"Error getting schedules: {str(e)}")
            return []

    def update_schedule(
        self, schedule_id: int, data: Dict[str, Any], admin_phone: str = None
    ) -> bool:
        """Update collection schedule (admin only)"""
        if admin_phone:
            from .user import UserModel

            user_model = UserModel(self.db)
            if not user_model.is_admin(admin_phone):
                return False

        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()

                # Build update query dynamically
                update_fields = []
                params = []

                for key, value in data.items():
                    if key in [
                        "location_name",
                        "address",
                        "schedule_day",
                        "schedule_time",
                        "contact",
                    ]:
                        update_fields.append(f"{key} = ?")
                        params.append(value)
                    elif key == "waste_types":
                        update_fields.append("waste_types = ?")
                        params.append(json.dumps(value))

                if not update_fields:
                    return False

                update_fields.append("updated_at = CURRENT_TIMESTAMP")
                params.append(schedule_id)

                query = f"""
                    UPDATE collection_schedules 
                    SET {', '.join(update_fields)}
                    WHERE id = ?
                """

                cursor.execute(query, params)
                conn.commit()

                return cursor.rowcount > 0

        except Exception as e:
            logger.error(f"Error updating schedule: {str(e)}")
            return False

    def delete_schedule(self, schedule_id: int, admin_phone: str = None) -> bool:
        """Soft delete collection schedule (admin only)"""
        if admin_phone:
            from .user import UserModel

            user_model = UserModel(self.db)
            if not user_model.is_admin(admin_phone):
                return False

        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    UPDATE collection_schedules 
                    SET is_active = 0, updated_at = CURRENT_TIMESTAMP 
                    WHERE id = ?
                """,
                    (schedule_id,),
                )

                conn.commit()
                return cursor.rowcount > 0

        except Exception as e:
            logger.error(f"Error deleting schedule: {str(e)}")
            return False

    # ========== ADMIN CRUD METHODS ==========

    def add_collection_point(self, data: Dict[str, Any]) -> bool:
        """Add new collection point"""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()

                point_id = f"cp_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                cursor.execute(
                    """
                    INSERT INTO collection_points 
                    (id, name, type, latitude, longitude, accepted_waste_types, 
                     schedule, contact, description, is_active)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        point_id,
                        data["name"],
                        data.get("type", "umum"),
                        data["latitude"],
                        data["longitude"],
                        json.dumps(data["accepted_waste_types"]),
                        data.get("operating_hours", "07:00-16:00"),
                        data.get("contact_info", ""),
                        data.get("address", ""),
                        data.get("is_active", True),
                    ),
                )

                conn.commit()
                return True

        except Exception as e:
            logger.error(f"Error adding collection point: {str(e)}")
            return False

    def get_collection_point(self, point_id: str) -> Optional[Dict[str, Any]]:
        """Get single collection point by ID"""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT  FROM collection_points WHERE id = ?
                """,
                    (point_id,),
                )

                row = cursor.fetchone()
                if row:
                    return dict(row)
                return None

        except Exception as e:
            logger.error(f"Error getting collection point: {str(e)}")
            return None

    def update_collection_point(self, point_id: str, field: str, value: str) -> bool:
        """Update specific field of collection point"""
        try:
            valid_fields = {
                "name": "name",
                "address": "description",
                "hours": "schedule",
                "contact": "contact",
                "status": "is_active",
            }

            if field not in valid_fields:
                return False

            db_field = valid_fields[field]

            # Special handling for status field
            if field == "status":
                value = 1 if value.lower() in ["aktif", "active", "1", "true"] else 0

            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    f"""
                    UPDATE collection_points 
                    SET {db_field} = ?, updated_at = CURRENT_TIMESTAMP 
                    WHERE id = ?
                """,
                    (value, point_id),
                )

                conn.commit()
                return cursor.rowcount > 0

        except Exception as e:
            logger.error(f"Error updating collection point: {str(e)}")
            return False
