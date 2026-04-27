"""User model — PostgreSQL backed."""

import os
import logging
from typing import Optional, Dict, Any, List

from src.database.connection import get_db

logger = logging.getLogger(__name__)


class UserModel:

    def __init__(self):
        self._admin_phones = self._load_phones("ADMIN_PHONE_NUMBERS")
        self._coordinator_phones = self._load_phones("COORDINATOR_PHONE_NUMBERS")

    # ------------------------------------------------------------------
    # Phone helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _load_phones(env_key: str) -> List[str]:
        raw = os.getenv(env_key, "")
        return [p.strip().replace("@c.us", "").lstrip("+") for p in raw.split(",") if p.strip()]

    @staticmethod
    def _bare(phone: str) -> str:
        return phone.replace("@c.us", "").replace("@s.whatsapp.net", "").lstrip("+").strip()

    # ------------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------------
    def get_user(self, phone: str) -> Optional[Dict[str, Any]]:
        with get_db() as db:
            return db.fetchone("SELECT * FROM users WHERE phone_number = %s", (phone,))

    def create_or_update_user(self, phone: str) -> None:
        with get_db() as db:
            db.execute(
                """INSERT INTO users (phone_number, registration_status)
                   VALUES (%s, 'registered')
                   ON CONFLICT (phone_number) DO UPDATE
                   SET last_active = NOW()""",
                (phone,),
            )

    def get_user_role(self, phone: str) -> str:
        bare = self._bare(phone)
        if bare in self._admin_phones:
            return "admin"
        if bare in self._coordinator_phones:
            return "koordinator"
        user = self.get_user(phone)
        if user:
            return user.get("role", "warga")
        return "warga"

    def increment_user_stats(self, phone: str, stat_type: str) -> None:
        col = "total_messages" if stat_type == "message" else "total_images"
        with get_db() as db:
            db.execute(
                f"UPDATE users SET {col} = {col} + 1, last_active = NOW() WHERE phone_number = %s",
                (phone,),
            )

    def complete_registration(self, phone: str, name: str, address: str) -> bool:
        with get_db() as db:
            rows = db.execute(
                """UPDATE users SET name = %s, address = %s, registration_status = 'registered'
                   WHERE phone_number = %s""",
                (name, address, phone),
            )
            return rows > 0

    def list_users(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        with get_db() as db:
            return db.fetchall(
                "SELECT * FROM users ORDER BY last_active DESC LIMIT %s OFFSET %s",
                (limit, offset),
            )

    def count_users(self) -> int:
        with get_db() as db:
            row = db.fetchone("SELECT COUNT(*) AS cnt FROM users")
            return row["cnt"] if row else 0

    def update_user_role(self, phone: str, role: str) -> bool:
        with get_db() as db:
            return db.execute("UPDATE users SET role = %s WHERE phone_number = %s", (role, phone)) > 0

    def delete_user(self, phone: str) -> bool:
        with get_db() as db:
            return db.execute("DELETE FROM users WHERE phone_number = %s", (phone,)) > 0
