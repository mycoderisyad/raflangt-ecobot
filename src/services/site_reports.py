"""Telegram report workflow for illegal dumps and full waste collection sites."""

import logging
import re

from src.config import get_settings
from src.database.models.site_report import SiteReportModel

logger = logging.getLogger(__name__)
MAX_REPORT_PHOTO_BYTES = 6 * 1024 * 1024

_REPORT_WORD = re.compile(r"^\s*/?(?:(?:aku|saya)\s+)?(?:(?:mau|ingin)\s+)?(?:lapor(?:kan)?|melapor(?:kan)?|report)\b", re.I)
_FULL_SITE = re.compile(r"\b(tps|tpa|tempat sampah|tempat penampungan|bak sampah)\b.*\b(penuh|meluap|overload)\b|\b(penuh|meluap|overload)\b.*\b(tps|tpa|tempat sampah|tempat penampungan|bak sampah)\b", re.I)
_ILLEGAL_DUMP = re.compile(r"\b(liar|ilegal|sembarangan|tumpukan sampah|pembuangan liar)\b", re.I)
_REPORT_REQUEST = _REPORT_WORD


def parse_report_issue(text: str) -> str | None:
    if not _REPORT_WORD.search(text):
        return None
    if _FULL_SITE.search(text):
        return "full_site"
    if _ILLEGAL_DUMP.search(text):
        return "illegal_dump"
    return "unknown"


def is_report_request(text: str) -> bool:
    return bool(_REPORT_REQUEST.search(text))


def detect_image_mime(data: bytes) -> str:
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if data.startswith(b"GIF8"):
        return "image/gif"
    if data.startswith(b"RIFF") and data[8:12] == b"WEBP":
        return "image/webp"
    return "image/jpeg"


class SiteReportService:
    def __init__(self):
        self.model = SiteReportModel()

    def begin(self, user_phone: str, issue_type: str, photo: bytes | None = None) -> str:
        if photo and len(photo) > MAX_REPORT_PHOTO_BYTES:
            return "Ukuran foto laporan maksimal 6 MB. Kirim foto yang lebih kecil ya."
        mime = detect_image_mime(photo) if photo else None
        try:
            self.model.start_draft(user_phone, issue_type, photo, mime)
        except Exception:
            logger.exception("Could not start site report for %s", user_phone)
            return "Laporan belum bisa disimpan sekarang. Coba lagi sebentar ya."
        return self._location_prompt() if photo else self._photo_prompt()

    def receive_photo(self, user_phone: str, photo: bytes) -> str | None:
        try:
            pending = self.model.get_pending(user_phone)
        except Exception:
            logger.exception("Could not load pending site report for %s", user_phone)
            return "Laporan belum bisa diproses sekarang. Coba kirim lagi sebentar ya."
        if not pending:
            return None
        if pending["status"] == "draft_waiting_location":
            return self._location_prompt()
        if len(photo) > MAX_REPORT_PHOTO_BYTES:
            return "Ukuran foto laporan maksimal 6 MB. Kirim foto yang lebih kecil ya."
        try:
            saved = self.model.add_photo(
                user_phone,
                int(pending["id"]),
                photo,
                detect_image_mime(photo),
            )
        except Exception:
            logger.exception("Could not store report photo for %s", user_phone)
            return "Foto laporan belum bisa disimpan. Coba kirim lagi sebentar ya."
        return self._location_prompt() if saved else self._photo_prompt()

    def receive_location(self, user_phone: str, latitude: float, longitude: float) -> str:
        try:
            pending = self.model.get_pending(user_phone)
        except Exception:
            logger.exception("Could not load pending site report for %s", user_phone)
            return "Laporan belum bisa diproses sekarang. Coba lagi sebentar ya."
        if not pending:
            return "Belum ada laporan yang menunggu lokasi. Kirim `lapor sampah liar` atau `lapor TPS penuh` dulu ya."
        if pending["status"] == "draft_waiting_photo":
            return "Laporannya belum ada foto. Kirim foto dulu, lalu bagikan lokasi titiknya."
        try:
            report = self.model.add_location(user_phone, latitude, longitude)
        except Exception:
            logger.exception("Could not save report location for %s", user_phone)
            return "Lokasi laporan belum bisa disimpan. Kirim ulang lokasi titiknya ya."
        if not report:
            return "Lokasi belum tersimpan. Kirim ulang lokasi titiknya ya."
        self._notify_coordinators(report)
        return (
            f"Laporan **#{report['id']}** sudah masuk ke pengurus dengan status *baru*. Makasih sudah bantu jaga lingkungan 🙏"
        )

    def cancel(self, user_phone: str) -> str:
        try:
            if self.model.cancel_pending(user_phone):
                return "Draft laporan dibatalkan."
        except Exception:
            logger.exception("Could not cancel site report for %s", user_phone)
            return "Draft laporan belum bisa dibatalkan sekarang."
        return "Tidak ada draft laporan yang perlu dibatalkan."

    def update_status(self, report_id: int, status: str) -> dict | None:
        report = self.model.update_status(report_id, status)
        if report:
            self._notify_reporter(report, status)
        return report

    def _notify_coordinators(self, report: dict) -> None:
        cfg = get_settings().telegram
        if not cfg.enabled:
            return
        try:
            from src.channels.telegram import TelegramChannel

            issue = "TPS penuh" if report["issue_type"] == "full_site" else "Sampah liar"
            maps = f"https://maps.google.com/?q={report['latitude']},{report['longitude']}"
            message = f"Laporan baru #{report['id']} — {issue}\n{maps}"
            channel = TelegramChannel()
            photo = self.model.get_photo(int(report["id"]))
            for chat_id in self.model.get_coordinator_chat_ids():
                if photo and hasattr(channel, "send_photo"):
                    channel.send_photo(
                        chat_id,
                        bytes(photo["photo_data"]),
                        message,
                        photo["photo_mime"] or "image/jpeg",
                    )
                else:
                    channel.send_message(chat_id, message)
        except Exception:
            logger.exception("Could not notify coordinators for site report %s", report["id"])

    @staticmethod
    def _notify_reporter(report: dict, status: str) -> None:
        cfg = get_settings().telegram
        if not cfg.enabled:
            return
        labels = {"acknowledged": "sedang ditindaklanjuti", "resolved": "sudah selesai ditangani", "rejected": "tidak dapat ditindaklanjuti"}
        try:
            from src.channels.telegram import TelegramChannel

            TelegramChannel().send_message(
                report["user_id"],
                f"Pembaruan laporan **#{report['id']}**: {labels[status]}.",
            )
        except Exception:
            logger.exception("Could not notify reporter for site report %s", report["id"])

    @staticmethod
    def _photo_prompt() -> str:
        return "Siap, kirim foto yang jelas dari titik sampah itu. Setelah foto, bagikan lokasi lewat lampiran Telegram → Lokasi. Ketik `batal` kalau mau berhenti."

    @staticmethod
    def _location_prompt() -> str:
        return "Fotonya tersimpan. Sekarang bagikan lokasi titiknya lewat lampiran Telegram → Lokasi. Ketik `batal` kalau mau berhenti."
