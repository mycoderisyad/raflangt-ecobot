"""Database and delivery operations used by the admin API."""

import json
import uuid
from typing import Any

import psycopg2

from src.channels.telegram import TelegramChannel
from src.database.connection import get_db


class AdminService:
    @staticmethod
    def _user(row: dict[str, Any] | None) -> dict[str, Any] | None:
        if row is None:
            return None
        result = dict(row)
        result["user_id"] = result.pop("phone_number")
        result["role"] = result.get("role") or "warga"
        result["registration_status"] = result.get("registration_status") or "pending"
        result["is_active"] = bool(result.get("is_active"))
        return result

    def dashboard(self) -> dict[str, Any]:
        with get_db() as db:
            totals = (
                db.fetchone(
                    """SELECT COUNT(*) AS total_users,
                          COUNT(*) FILTER (WHERE is_active) AS active_users,
                          COALESCE(SUM(points), 0) AS total_points,
                          COALESCE(SUM(total_messages), 0) AS total_messages,
                          COALESCE(SUM(total_images), 0) AS total_images
                   FROM users"""
                )
                or {}
            )
            roles = db.fetchall(
                "SELECT COALESCE(role, 'warga') AS role, COUNT(*) AS count FROM users GROUP BY role"
            )
            recent = db.fetchall(
                """SELECT phone_number AS user_id, username, last_active, total_messages, role
                   FROM users WHERE last_active IS NOT NULL ORDER BY last_active DESC LIMIT 15"""
            )
        return {
            **totals,
            "role_distribution": {row["role"]: row["count"] for row in roles},
            "recent_activity": recent,
        }

    def analytics(self) -> dict[str, Any]:
        with get_db() as db:
            totals = (
                db.fetchone(
                    """SELECT COUNT(*) AS total_users,
                          COUNT(*) FILTER (WHERE is_active) AS active_users,
                          COALESCE(SUM(points), 0) AS total_points,
                          COALESCE(SUM(total_messages), 0) AS total_messages,
                          COALESCE(SUM(total_images), 0) AS total_images
                   FROM users"""
                )
                or {}
            )
            monthly = db.fetchall(
                """SELECT TO_CHAR(first_seen, 'YYYY-MM') AS month, COUNT(*) AS new_users,
                          SUM(total_messages) AS messages, SUM(total_images) AS images
                   FROM users WHERE first_seen IS NOT NULL
                   GROUP BY TO_CHAR(first_seen, 'YYYY-MM') ORDER BY month DESC LIMIT 12"""
            )
            top_users = db.fetchall(
                "SELECT phone_number AS user_id, points, total_messages, role FROM users ORDER BY points DESC LIMIT 10"
            )
        return {"stats": totals, "monthly_stats": monthly, "top_users": top_users}

    def list_users(self, limit: int, offset: int) -> tuple[list[dict[str, Any]], int]:
        with get_db() as db:
            rows = db.fetchall(
                "SELECT * FROM users ORDER BY last_active DESC NULLS LAST LIMIT %s OFFSET %s",
                (limit, offset),
            )
            count = db.fetchone("SELECT COUNT(*) AS total FROM users") or {"total": 0}
        return [self._user(row) for row in rows], count["total"]

    def get_user(self, user_id: str) -> dict[str, Any] | None:
        with get_db() as db:
            return self._user(
                db.fetchone("SELECT * FROM users WHERE phone_number = %s", (user_id,))
            )

    def create_user(self, data: dict[str, Any]) -> dict[str, Any]:
        with get_db() as db:
            db.execute(
                """INSERT INTO users (phone_number, username, role, points, is_active, registration_status, first_seen)
                   VALUES (%s, %s, %s, %s, %s, 'registered', NOW())""",
                (
                    data["user_id"],
                    data.get("username"),
                    data["role"],
                    data["points"],
                    data["is_active"],
                ),
            )
        return self.get_user(data["user_id"])

    def patch_user(
        self, user_id: str, changes: dict[str, Any]
    ) -> dict[str, Any] | None:
        columns = {"username", "role", "points", "is_active"}
        changes = {key: value for key, value in changes.items() if key in columns}
        if not changes:
            return self.get_user(user_id)
        assignments = ", ".join(f"{column} = %s" for column in changes)
        values = [*changes.values(), user_id]
        with get_db() as db:
            updated = db.execute(
                f"UPDATE users SET {assignments} WHERE phone_number = %s", tuple(values)
            )
        return self.get_user(user_id) if updated else None

    def delete_user(self, user_id: str) -> bool:
        try:
            with get_db() as db:
                return (
                    db.execute("DELETE FROM users WHERE phone_number = %s", (user_id,))
                    > 0
                )
        except psycopg2.IntegrityError:
            raise

    def list_locations(self) -> list[dict[str, Any]]:
        with get_db() as db:
            rows = db.fetchall("SELECT * FROM collection_points ORDER BY name")
        return [self._decode_json(row, "accepted_waste_types") for row in rows]

    @staticmethod
    def _decode_json(row: dict[str, Any], key: str) -> dict[str, Any]:
        value = row.get(key)
        if isinstance(value, str):
            try:
                row[key] = json.loads(value)
            except json.JSONDecodeError:
                row[key] = []
        return row

    def get_location(self, location_id: str) -> dict[str, Any] | None:
        with get_db() as db:
            row = db.fetchone(
                "SELECT * FROM collection_points WHERE id = %s", (location_id,)
            )
        return self._decode_json(row, "accepted_waste_types") if row else None

    def create_location(self, data: dict[str, Any]) -> dict[str, Any]:
        location_id = str(uuid.uuid4())
        with get_db() as db:
            db.execute(
                """INSERT INTO collection_points
                   (id, name, type, latitude, longitude, accepted_waste_types, schedule, contact, description)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                (
                    location_id,
                    data["name"],
                    data["type"],
                    data["latitude"],
                    data["longitude"],
                    json.dumps(data["accepted_waste_types"]),
                    data["schedule"],
                    data.get("contact"),
                    data.get("description"),
                ),
            )
        return self.get_location(location_id)

    def patch_location(
        self, location_id: str, changes: dict[str, Any]
    ) -> dict[str, Any] | None:
        current = self.get_location(location_id)
        if current is None:
            return None
        allowed = {
            "name",
            "type",
            "latitude",
            "longitude",
            "accepted_waste_types",
            "schedule",
            "contact",
            "description",
            "is_active",
        }
        changes = {key: value for key, value in changes.items() if key in allowed}
        if not changes:
            return current
        if "accepted_waste_types" in changes:
            changes["accepted_waste_types"] = json.dumps(
                changes["accepted_waste_types"]
            )
        assignments = ", ".join(f"{column} = %s" for column in changes)
        with get_db() as db:
            db.execute(
                f"UPDATE collection_points SET {assignments}, updated_at=NOW() WHERE id=%s",
                (*changes.values(), location_id),
            )
        return self.get_location(location_id)

    def delete_location(self, location_id: str) -> bool:
        with get_db() as db:
            return (
                db.execute(
                    "DELETE FROM collection_points WHERE id = %s", (location_id,)
                )
                > 0
            )

    def list_schedules(self) -> list[dict[str, Any]]:
        with get_db() as db:
            rows = db.fetchall(
                """SELECT * FROM collection_schedules ORDER BY
                   CASE schedule_day WHEN 'Senin' THEN 1 WHEN 'Selasa' THEN 2 WHEN 'Rabu' THEN 3
                     WHEN 'Kamis' THEN 4 WHEN 'Jumat' THEN 5 WHEN 'Sabtu' THEN 6 WHEN 'Minggu' THEN 7 ELSE 8 END,
                   schedule_time ASC"""
            )
        return [self._schedule(row) for row in rows]

    @staticmethod
    def _schedule(row: dict[str, Any]) -> dict[str, Any]:
        row = AdminService._decode_json(row, "waste_types")
        address = row.get("address") or ""
        if "notes" not in row or row["notes"] is None:
            if " | Notes: " in address:
                row["address"], _, row["notes"] = address.partition(" | Notes: ")
            else:
                row["notes"] = None
        time_parts = (row.get("schedule_time") or "").split("-", 1)
        row["start_time"] = time_parts[0].strip() if time_parts else ""
        row["end_time"] = (
            time_parts[1].strip() if len(time_parts) == 2 else row["start_time"]
        )
        row["collector"] = row.get("contact")
        return row

    def get_schedule(self, schedule_id: int) -> dict[str, Any] | None:
        with get_db() as db:
            row = db.fetchone(
                "SELECT * FROM collection_schedules WHERE id = %s", (schedule_id,)
            )
        return self._schedule(row) if row else None

    def create_schedule(self, data: dict[str, Any]) -> dict[str, Any]:
        schedule_time = f"{data['start_time']}-{data['end_time']}"
        with get_db() as db:
            row = db.fetchone(
                """INSERT INTO collection_schedules
                   (location_name, address, schedule_day, schedule_time, waste_types, contact, notes, is_active)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s) RETURNING id""",
                (
                    data["location_name"],
                    data["address"],
                    data["schedule_day"],
                    schedule_time,
                    json.dumps(data["waste_types"]),
                    data.get("collector"),
                    data.get("notes"),
                    data["is_active"],
                ),
            )
        return self.get_schedule(row["id"])

    def patch_schedule(
        self, schedule_id: int, changes: dict[str, Any]
    ) -> dict[str, Any] | None:
        current = self.get_schedule(schedule_id)
        if current is None:
            return None
        nullable = {"notes", "collector"}
        updates = {
            key: value
            for key, value in changes.items()
            if value is not None or key in nullable
        }
        if "start_time" in updates or "end_time" in updates:
            start = updates.pop("start_time", current["start_time"])
            end = updates.pop("end_time", current["end_time"])
            updates["schedule_time"] = f"{start}-{end}"
        if "waste_types" in updates:
            updates["waste_types"] = json.dumps(updates["waste_types"])
        if "collector" in updates:
            updates["contact"] = updates.pop("collector")
        allowed = {
            "location_name",
            "address",
            "schedule_day",
            "schedule_time",
            "waste_types",
            "contact",
            "notes",
            "is_active",
        }
        updates = {key: value for key, value in updates.items() if key in allowed}
        if updates:
            assignments = ", ".join(f"{column} = %s" for column in updates)
            with get_db() as db:
                db.execute(
                    f"UPDATE collection_schedules SET {assignments}, updated_at=NOW() WHERE id=%s",
                    (*updates.values(), schedule_id),
                )
        return self.get_schedule(schedule_id)

    def delete_schedule(self, schedule_id: int) -> bool:
        with get_db() as db:
            return (
                db.execute(
                    "DELETE FROM collection_schedules WHERE id = %s", (schedule_id,)
                )
                > 0
            )

    def broadcast(self, message: str) -> dict[str, int]:
        with get_db() as db:
            rows = db.fetchall(
                """SELECT phone_number FROM users WHERE is_active=TRUE AND registration_status='registered'
                   AND phone_number ~ '^[0-9]+$'"""
            )
        targets = [row["phone_number"] for row in rows]
        if not targets:
            return {"eligible": 0, "sent": 0, "failed": 0}
        channel = TelegramChannel()
        content = f"📢 **Pengumuman**\n\n{message}"
        sent = sum(channel.send_message(target, content) for target in targets)
        return {"eligible": len(targets), "sent": sent, "failed": len(targets) - sent}

    def broadcast_audience(self) -> int:
        with get_db() as db:
            row = db.fetchone(
                """SELECT COUNT(*) AS total FROM users WHERE is_active=TRUE AND registration_status='registered'
                   AND phone_number ~ '^[0-9]+$'"""
            )
        return row["total"] if row else 0
