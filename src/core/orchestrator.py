"""Main message orchestrator — routes incoming messages through the pipeline."""

import logging
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
    def handle_text(self, phone: str, message: str, channel: str = "whatsapp") -> str:
        """Process a text message and return a reply string."""
        start = time.time()
        normalized = normalize_phone_for_db(phone) if channel == "whatsapp" else phone

        # Ensure user exists
        self.user_model.create_or_update_user(normalized)
        self.user_model.increment_user_stats(normalized, "message")

        # Resolve intent
        ai_cfg = self.settings.ai
        use_ai = bool(ai_cfg.api_key)
        intent_result = resolve_intent(message, use_ai=use_ai)
        intent = intent_result["intent"]
        user_role = self.user_model.get_user_role(normalized)

        # Access control
        feature_map = {
            "statistics": "statistics",
            "report": "report",
        }
        required_feature = feature_map.get(intent)
        if required_feature and required_feature not in FEATURE_ACCESS.get(user_role, set()):
            reply = f"Maaf, fitur {intent} hanya tersedia untuk role yang lebih tinggi. Hubungi admin untuk info lebih lanjut."
            self._log_interaction(normalized, "message", message, reply, time.time() - start)
            return reply

        # Route
        if intent == "report" and user_role in ("koordinator", "admin"):
            reply = self._handle_report(normalized, user_role)
        else:
            # All other intents go through the AI agent with context
            reply = self.agent.process_text(message, normalized, intent=intent)

        self._log_interaction(normalized, "message", message, reply, time.time() - start)
        return reply

    def handle_image(
        self, phone: str, image_data: bytes, caption: str = "", channel: str = "whatsapp"
    ) -> str:
        """Process an image message and return a reply string."""
        start = time.time()
        normalized = normalize_phone_for_db(phone) if channel == "whatsapp" else phone

        self.user_model.create_or_update_user(normalized)
        self.user_model.increment_user_stats(normalized, "image")

        reply = self.agent.process_image(image_data, normalized, caption=caption)

        self._log_interaction(normalized, "image", "[photo]", reply, time.time() - start)
        return reply

    # ------------------------------------------------------------------
    # Specific handlers
    # ------------------------------------------------------------------
    def _handle_report(self, phone: str, role: str) -> str:
        try:
            svc = ReportService()
            result = svc.generate_and_send()
            if result.get("success"):
                return "Laporan telah di-generate dan dikirim ke email admin. Silakan cek inbox. 📧"
            return f"Gagal mengirim laporan: {result.get('error', 'unknown error')}"
        except Exception as e:
            logger.error("Report generation error: %s", e)
            return "Maaf, ada kendala saat membuat laporan. Silakan coba lagi nanti."

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
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
