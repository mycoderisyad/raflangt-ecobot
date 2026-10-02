"""Resident waste site reports and their Telegram submission drafts."""

from typing import Any

from src.config import get_settings
from src.database.connection import get_db


class SiteReportModel:
    def start_draft(
        self,
        user_phone: str,
        issue_type: str,
        photo_data: bytes | None = None,
        photo_mime: str | None = None,
    ) -> int:
        status = "draft_waiting_location" if photo_data else "draft_waiting_photo"
        with get_db() as db:
            db.execute(
                """UPDATE waste_site_reports
                   SET status='cancelled', photo_data=NULL, photo_mime=NULL, updated_at=NOW()
                   WHERE user_phone=%s AND status IN ('draft_waiting_photo', 'draft_waiting_location')""",
                (user_phone,),
            )
            row = db.fetchone(
                """INSERT INTO waste_site_reports
                   (user_phone, issue_type, status, photo_data, photo_mime)
                   VALUES (%s, %s, %s, %s, %s) RETURNING id""",
                (user_phone, issue_type, status, photo_data, photo_mime),
            )
        return int(row["id"])

    def get_pending(self, user_phone: str) -> dict[str, Any] | None:
        with get_db() as db:
            return db.fetchone(
                """SELECT id, issue_type, status FROM waste_site_reports
                   WHERE user_phone=%s
                     AND status IN ('draft_waiting_photo', 'draft_waiting_location')
                     AND created_at >= NOW() - INTERVAL '24 hours'
                   ORDER BY created_at DESC LIMIT 1""",
                (user_phone,),
            )

    def add_photo(
        self, user_phone: str, report_id: int, photo_data: bytes, photo_mime: str
    ) -> bool:
        with get_db() as db:
            return db.execute(
                """UPDATE waste_site_reports
                   SET photo_data=%s, photo_mime=%s, status='draft_waiting_location', updated_at=NOW()
                   WHERE id=%s AND user_phone=%s AND status='draft_waiting_photo'""",
                (photo_data, photo_mime, report_id, user_phone),
            ) > 0

    def add_location(
        self, user_phone: str, latitude: float, longitude: float
    ) -> dict[str, Any] | None:
        with get_db() as db:
            return db.fetchone(
                """UPDATE waste_site_reports
                   SET latitude=%s, longitude=%s, status='new', updated_at=NOW()
                   WHERE id = (
                       SELECT id FROM waste_site_reports
                       WHERE user_phone=%s AND status='draft_waiting_location'
                         AND created_at >= NOW() - INTERVAL '24 hours'
                       ORDER BY created_at DESC LIMIT 1
                   )
                   RETURNING id, issue_type, latitude, longitude, created_at""",
                (latitude, longitude, user_phone),
            )

    def cancel_pending(self, user_phone: str) -> bool:
        with get_db() as db:
            return db.execute(
                """UPDATE waste_site_reports
                   SET status='cancelled', updated_at=NOW(), photo_data=NULL, photo_mime=NULL
                   WHERE user_phone=%s AND status IN ('draft_waiting_photo', 'draft_waiting_location')""",
                (user_phone,),
            ) > 0

    def list_reports(
        self, status: str | None, limit: int, offset: int
    ) -> tuple[list[dict[str, Any]], int]:
        where = "WHERE status IN ('new', 'acknowledged', 'resolved', 'rejected')"
        params: tuple[Any, ...] = ()
        if status:
            where += " AND status=%s"
            params = (status,)
        with get_db() as db:
            rows = db.fetchall(
                f"""SELECT id, user_phone AS user_id, issue_type, status, latitude, longitude,
                          photo_mime, created_at, updated_at
                   FROM waste_site_reports {where}
                   ORDER BY created_at DESC LIMIT %s OFFSET %s""",
                (*params, limit, offset),
            )
            count = db.fetchone(
                f"SELECT COUNT(*) AS total FROM waste_site_reports {where}", params
            )
        return rows, int((count or {}).get("total", 0))

    def get_photo(self, report_id: int) -> dict[str, Any] | None:
        with get_db() as db:
            return db.fetchone(
                """SELECT photo_data, photo_mime FROM waste_site_reports
                   WHERE id=%s AND status IN ('new', 'acknowledged', 'resolved', 'rejected')""",
                (report_id,),
            )

    def update_status(self, report_id: int, new_status: str) -> dict[str, Any] | None:
        with get_db() as db:
            return db.fetchone(
                """UPDATE waste_site_reports SET status=%s, updated_at=NOW()
                   WHERE id=%s AND status IN ('new', 'acknowledged')
                   RETURNING id, user_phone AS user_id, issue_type, status, latitude,
                             longitude, photo_mime, created_at, updated_at""",
                (new_status, report_id),
            )

    def delete_closed_report(self, report_id: int) -> bool:
        with get_db() as db:
            return db.execute(
                """DELETE FROM waste_site_reports
                   WHERE id=%s AND status IN ('resolved', 'rejected')""",
                (report_id,),
            ) > 0

    def get_coordinator_chat_ids(self) -> list[str]:
        app_config = get_settings().app
        configured_usernames = sorted(
            set(
                app_config.admin_telegram_usernames
                + app_config.coordinator_telegram_usernames
            )
        )
        with get_db() as db:
            rows = db.fetchall(
                """SELECT phone_number FROM users
                   WHERE (role IN ('admin', 'koordinator')
                          OR LOWER(COALESCE(telegram_username, '')) = ANY(%s))
                     AND is_active=TRUE
                     AND registration_status='registered'
                     AND phone_number ~ '^[0-9]+$'""",
                (configured_usernames,),
            )
        return [row["phone_number"] for row in rows]
