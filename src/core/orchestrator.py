"""Main message orchestrator — routes incoming messages through the pipeline."""

import logging
import re
import time
from typing import Dict, Any, Optional

from src.config import get_settings
from src.core.constants import FEATURE_ACCESS
from src.core.intent_resolver import resolve_intent
from src.ai.agent import Agent
from src.database.models.user import UserModel
from src.database.models.waste import WasteClassificationModel
from src.database.models.system import UserInteractionModel
from src.services.report import ReportService
from src.core.rate_limiter import is_rate_limited
from src.utils.phone import normalize_phone_for_db

logger = logging.getLogger(__name__)


class Orchestrator:
    """Stateless orchestrator — processes one message at a time."""

    def __init__(self):
        self.settings = get_settings()
        self.agent = Agent()
        self.user_model = UserModel()
        self.waste_model = WasteClassificationModel()
        self.interaction_model = UserInteractionModel()

    # ------------------------------------------------------------------
    # Entry points (called by channel webhooks)
    # ------------------------------------------------------------------
    def handle_text(
        self, phone: str, message: str, channel: str = "whatsapp", username: str = "",
    ) -> str:
        """Process a text message and return a reply string."""
        start = time.time()
        normalized = normalize_phone_for_db(phone) if channel == "whatsapp" else phone

        if is_rate_limited(normalized):
            return "Kamu mengirim pesan terlalu cepat. Tunggu sebentar ya. ⏳"

        # Ensure user exists
        self.user_model.create_or_update_user(normalized)
        self.user_model.increment_user_stats(normalized, "message")

        # Resolve intent
        ai_cfg = self.settings.ai
        use_ai = bool(ai_cfg.api_key)
        intent_result = resolve_intent(message, use_ai=use_ai)
        intent = intent_result["intent"]
        user_role = self.user_model.get_user_role(normalized, telegram_username=username)

        # Access control
        feature_map = {
            "statistics": "statistics",
            "report": "report",
            "broadcast": "broadcast",
        }
        required_feature = feature_map.get(intent)
        if required_feature and required_feature not in FEATURE_ACCESS.get(user_role, set()):
            reply = f"Maaf, fitur {intent} hanya tersedia untuk role yang lebih tinggi. Hubungi admin untuk info lebih lanjut."
            self._log_interaction(normalized, "message", message, reply, time.time() - start)
            return reply

        # Route
        if intent == "report" and user_role in ("koordinator", "admin"):
            reply = self._handle_report(normalized, user_role)
        elif intent == "statistics" and user_role in ("koordinator", "admin"):
            reply = self._handle_statistics()
        elif intent == "broadcast" and user_role == "admin":
            reply = self._handle_broadcast(message, channel)
        elif intent == "settings":
            reply = self._handle_settings(normalized, message, user_role)
        else:
            # All other intents go through the AI agent with context
            reply = self.agent.process_text(message, normalized, intent=intent)

        # First-time username prompt
        reply = self._maybe_prompt_username(normalized, reply)

        self._log_interaction(normalized, "message", message, reply, time.time() - start)
        return reply

    def handle_image(
        self, phone: str, image_data: bytes, caption: str = "",
        channel: str = "whatsapp", username: str = "",
    ) -> str:
        """Process an image message and return a reply string."""
        start = time.time()
        normalized = normalize_phone_for_db(phone) if channel == "whatsapp" else phone

        if is_rate_limited(normalized):
            return "Kamu mengirim pesan terlalu cepat. Tunggu sebentar ya. ⏳"

        self.user_model.create_or_update_user(normalized)
        self.user_model.increment_user_stats(normalized, "image")

        reply = self.agent.process_image(image_data, normalized, caption=caption)

        # Extract and save waste classification from AI response
        self._save_classification(normalized, reply)

        self._log_interaction(normalized, "image", "[photo]", reply, time.time() - start)
        return reply

    # ------------------------------------------------------------------
    # Specific handlers
    # ------------------------------------------------------------------
    def _handle_statistics(self) -> str:
        try:
            total_users = self.user_model.count_users()
            int_stats = self.interaction_model.get_stats(days=7)
            waste_stats = self.waste_model.get_statistics(days=7)

            active = int_stats.get("active_users", 0) if int_stats else 0
            interactions = int_stats.get("total_interactions", 0) if int_stats else 0
            images = int_stats.get("images_processed", 0) if int_stats else 0

            w_total = waste_stats.get("total", 0) if waste_stats else 0
            w_organic = waste_stats.get("organic", 0) if waste_stats else 0
            w_inorganic = waste_stats.get("inorganic", 0) if waste_stats else 0
            w_b3 = waste_stats.get("b3", 0) if waste_stats else 0

            return (
                f"**Statistik EcoBot (7 Hari Terakhir)**\n\n"
                f"**Pengguna**\n"
                f"- Total terdaftar: {total_users}\n"
                f"- Aktif (7 hari): {active}\n\n"
                f"**Interaksi**\n"
                f"- Total pesan: {interactions}\n"
                f"- Foto diproses: {images}\n\n"
                f"**Klasifikasi Sampah**\n"
                f"- Organik: {w_organic}\n"
                f"- Anorganik: {w_inorganic}\n"
                f"- B3: {w_b3}\n"
                f"- Total: {w_total}"
            )
        except Exception as e:
            logger.error("Statistics error: %s", e)
            return "Maaf, gagal mengambil data statistik. Coba lagi nanti."

    def _handle_report(self, phone: str, role: str) -> str:
        try:
            svc = ReportService()
            result = svc.generate_and_send()
            if result.get("success"):
                return "Laporan telah di-generate dan dikirim ke email admin. Silakan cek inbox. 📧"
            logger.error("Report send failed: %s", result.get("error"))
            return "Maaf, laporan gagal dikirim. Pastikan konfigurasi email sudah benar. 🙏"
        except Exception as e:
            logger.error("Report generation error: %s", e)
            return "Maaf, ada kendala saat membuat laporan. Silakan coba lagi nanti."

    def _handle_settings(self, phone: str, message: str, role: str) -> str:
        """Handle user settings: username, reminder toggle, profile view."""
        try:
            lower = message.strip().lower()
            user = self.user_model.get_user(phone)
            prefs = self.user_model.get_preferences(phone)

            # --- Set username ---
            import re as _re
            name_match = _re.search(
                r"(?:nama|username|name)[:\s]+(.+)", lower
            )
            if name_match:
                new_name = name_match.group(1).strip().title()
                if len(new_name) < 2 or len(new_name) > 50:
                    return "Username harus antara 2-50 karakter."
                self.user_model.set_username(phone, new_name)
                return f"Username berhasil diubah menjadi **{new_name}**"

            # --- Toggle reminder ---
            if any(w in lower for w in ("reminder on", "aktifkan reminder", "nyalakan reminder")):
                self.user_model.set_preference(phone, "reminder_enabled", True)
                return "Reminder jadwal pengumpulan sampah telah **diaktifkan**."
            if any(w in lower for w in ("reminder off", "matikan reminder", "nonaktifkan reminder")):
                self.user_model.set_preference(phone, "reminder_enabled", False)
                return "Reminder jadwal pengumpulan sampah telah **dinonaktifkan**."

            # --- Show settings menu / profile ---
            username = (user.get("username") or "-") if user else "-"
            reminder_status = "Aktif" if prefs.get("reminder_enabled", True) else "Nonaktif"
            total_msg = (user.get("total_messages") or 0) if user else 0
            total_img = (user.get("total_images") or 0) if user else 0
            points = (user.get("points") or 0) if user else 0

            lines = [
                "**Profil & Pengaturan**\n",
                f"**Username:** {username}",
                f"**Role:** {role}",
                f"**Pesan:** {total_msg}  |  **Foto:** {total_img}  |  **Poin:** {points}",
                f"**Reminder:** {reminder_status}\n",
                "**Cara mengubah:**",
                "- Kirim `setting nama: [nama kamu]` untuk set username",
                "- Kirim `setting reminder on` / `setting reminder off`",
            ]

            return "\n".join(lines)
        except Exception as e:
            logger.error("Settings error: %s", e)
            return "Maaf, gagal memproses pengaturan. Coba lagi nanti."

    def _handle_broadcast(self, message: str, channel: str) -> str:
        """Broadcast a message to all active users."""
        try:
            # Extract the actual broadcast content (remove trigger keywords)
            import re as _re
            content = _re.sub(
                r"^\s*(broadcast|pengumuman|umumkan|siarkan)[:\s]*",
                "", message, count=1, flags=_re.IGNORECASE,
            ).strip()
            if not content or len(content) < 5:
                return (
                    "Untuk broadcast, kirim pesan dengan format:\n"
                    "**broadcast: [isi pesan]**\n\n"
                    "Contoh: broadcast: Jadwal pengumpulan sampah besok dipindah ke jam 10."
                )

            phones = self.user_model.get_all_active_phones()
            if not phones:
                return "Tidak ada user aktif untuk menerima broadcast."

            sent = 0
            cfg = self.settings

            if cfg.telegram.enabled:
                from src.channels.telegram import TelegramChannel
                tg = TelegramChannel()
                for phone in phones:
                    if phone.isdigit():  # Telegram chat IDs
                        if tg.send_message(phone, f"📢 **Pengumuman**\n\n{content}"):
                            sent += 1

            if cfg.whatsapp.enabled:
                from src.channels.whatsapp import WhatsAppChannel
                wa = WhatsAppChannel()
                for phone in phones:
                    if "@" in phone:  # WhatsApp format
                        if wa.send_message(phone, f"📢 *Pengumuman*\n\n{content}"):
                            sent += 1

            return f"Broadcast terkirim ke {sent}/{len(phones)} user."
        except Exception as e:
            logger.error("Broadcast error: %s", e)
            return "Maaf, broadcast gagal dikirim. Coba lagi nanti."

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    _prompted_users: set = set()  # track already-prompted users (in-memory per process)

    def _maybe_prompt_username(self, phone: str, reply: str) -> str:
        """Append a gentle username prompt if the user hasn't set one yet."""
        if phone in self._prompted_users:
            return reply
        try:
            user = self.user_model.get_user(phone)
            if user and user.get("username"):
                self._prompted_users.add(phone)
                return reply
            # Only prompt once per process lifetime
            self._prompted_users.add(phone)
            return (
                reply + "\n\n---\n"
                "Btw, kamu belum set username. "
                "Kirim `setting nama: [nama kamu]` untuk mengatur profil kamu."
            )
        except Exception:
            return reply

    # Regex patterns with word boundaries to avoid false positives
    _WASTE_PATTERNS = {
        "B3": re.compile(r"\b(b3|berbahaya\s+dan\s+beracun|limbah\s*b3|bahan\s+berbahaya|hazardous)\b", re.I),
        "ANORGANIK": re.compile(r"\b(anorganik|anorganic|inorganic|non[- ]?organik)\b", re.I),
        "ORGANIK": re.compile(r"\b(organik|organic)\b", re.I),
    }

    def _save_classification(self, phone: str, reply: str) -> None:
        """Extract waste type(s) from AI reply and save to waste_classifications."""
        try:
            lower = reply.lower()

            # Determine confidence from keywords
            if any(w in lower for w in ("tinggi", "high", "sangat yakin")):
                confidence = 0.9
            elif any(w in lower for w in ("sedang", "medium", "cukup yakin")):
                confidence = 0.7
            elif any(w in lower for w in ("rendah", "low", "kurang yakin")):
                confidence = 0.5
            else:
                confidence = 0.6

            # Detect all mentioned waste types using word-boundary regex
            detected = []
            for waste_type in ("B3", "ANORGANIK", "ORGANIK"):
                pattern = self._WASTE_PATTERNS[waste_type]
                if waste_type == "ORGANIK":
                    # Only match "organik" that is NOT preceded by "an" to avoid overlap
                    matches = pattern.findall(reply)
                    real = [m for m in matches if not re.search(r"an\s*$", reply[:reply.lower().find(m.lower())][-3:])]
                    if real:
                        detected.append(waste_type)
                elif pattern.search(reply):
                    detected.append(waste_type)

            if not detected:
                logger.debug("No waste type detected in AI reply for %s", phone)
                return

            for waste_type in detected:
                self.waste_model.save_classification(
                    user_phone=phone,
                    waste_type=waste_type,
                    confidence=confidence,
                    classification_method="ai",
                )
                logger.info("Saved classification: %s (%.1f) for %s", waste_type, confidence, phone)
        except Exception as e:
            logger.error("Error saving classification: %s", e)

    def _log_interaction(
        self, phone: str, itype: str, msg: str, reply: str, elapsed: float
    ) -> None:
        try:
            self.interaction_model.log_interaction(
                user_phone=phone,
                interaction_type=itype,
                message_content=msg[:500],
                response_content=reply[:500],
                success=True,
                response_time=round(elapsed, 3),
            )
        except Exception as e:
            logger.error("Error logging interaction: %s", e)
