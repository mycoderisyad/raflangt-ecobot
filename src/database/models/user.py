"""User model — PostgreSQL backed."""

import json
import os
import logging
from typing import Optional, Dict, Any, List

from src.database.connection import get_db

logger = logging.getLogger(__name__)


class UserModel:

    def __init__(self):
        self._admin_phones = self._load_phones("ADMIN_PHONE_NUMBERS")
        self._coordinator_phones = self._load_phones("COORDINATOR_PHONE_NUMBERS")
        self._admin_tg_usernames = self._load_list("ADMIN_TELEGRAM_USERNAMES", lower=True)
        self._coordinator_tg_usernames = self._load_list("COORDINATOR_TELEGRAM_USERNAMES", lower=True)

    # ------------------------------------------------------------------
    # Phone helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _load_phones(env_key: str) -> List[str]:
        raw = os.getenv(env_key, "")
        return [p.strip().replace("@c.us", "").lstrip("+") for p in raw.split(",") if p.strip()]

    @staticmethod
    def _load_list(env_key: str, lower: bool = False) -> List[str]:
        raw = os.getenv(env_key, "")
        items = [v.strip().lstrip("@") for v in raw.split(",") if v.strip()]
        return [v.lower() for v in items] if lower else items

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

    def get_user_role(self, phone: str, telegram_username: str = "") -> str:
        bare = self._bare(phone)
        tg_lower = telegram_username.lower().lstrip("@") if telegram_username else ""
        # Check admin
        if bare in self._admin_phones:
            return "admin"
        if tg_lower and tg_lower in self._admin_tg_usernames:
            return "admin"
        # Check coordinator
        if bare in self._coordinator_phones:
            return "koordinator"
        if tg_lower and tg_lower in self._coordinator_tg_usernames:
            return "koordinator"
        # Fallback to DB role
        user = self.get_user(phone)
        if user:
            return user.get("role", "warga")
        return "warga"

    _STAT_COLUMNS = {"message": "total_messages", "image": "total_images"}

    def increment_user_stats(self, phone: str, stat_type: str) -> None:
        col = self._STAT_COLUMNS.get(stat_type)
        if col is None:
            logger.warning("Unknown stat_type: %s", stat_type)
            return
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

    def get_all_active_phones(self) -> List[str]:
        with get_db() as db:
            rows = db.fetchall(
                "SELECT phone_number FROM users WHERE is_active = TRUE AND registration_status = 'registered'"
            )
            return [r["phone_number"] for r in rows]

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

    # ------------------------------------------------------------------
    # Username
    # ------------------------------------------------------------------
    def set_username(self, phone: str, username: str) -> bool:
        with get_db() as db:
            return db.execute(
                "UPDATE users SET username = %s WHERE phone_number = %s",
                (username.strip(), phone),
            ) > 0

    def get_username(self, phone: str) -> Optional[str]:
        user = self.get_user(phone)
        return user.get("username") if user else None

    # ------------------------------------------------------------------
    # Preferences (JSONB)
    # ------------------------------------------------------------------
    def get_preferences(self, phone: str) -> Dict[str, Any]:
        user = self.get_user(phone)
        if not user:
            return {"reminder_enabled": True}
        prefs = user.get("preferences")
        if isinstance(prefs, str):
            try:
                prefs = json.loads(prefs)
            except (json.JSONDecodeError, TypeError):
                prefs = {}
        return prefs or {"reminder_enabled": True}

    def set_preference(self, phone: str, key: str, value: Any) -> bool:
        prefs = self.get_preferences(phone)
        prefs[key] = value
        with get_db() as db:
            return db.execute(
                "UPDATE users SET preferences = %s WHERE phone_number = %s",
                (json.dumps(prefs), phone),
            ) > 0

    def get_reminder_enabled_phones(self) -> List[str]:
        """Return phone numbers of active users who have reminders enabled."""
        with get_db() as db:
            rows = db.fetchall(
                """SELECT phone_number FROM users
                   WHERE is_active = TRUE
                     AND registration_status = 'registered'
                     AND (preferences IS NULL OR (preferences->>'reminder_enabled')::text != 'false')"""
            )
            return [r["phone_number"] for r in rows]
