"""Main AI agent — handles text and multimodal conversations."""

import base64
import logging
from typing import Dict, Any, List, Optional

from src.config import get_settings
from src.ai.provider import chat_completion, chat_completion_with_image
from src.ai.prompts.system import build_system_prompt
from src.ai.prompts.context import build_db_context
from src.database.models.conversation import ConversationModel, MemoryModel
from src.database.models.user import UserModel

logger = logging.getLogger(__name__)

FALLBACK_RESPONSE = (
    "Maaf, ada kendala saat memproses pesanmu. Silakan coba lagi dalam beberapa saat. 🙏"
)


class Agent:
    """Stateless AI agent — all state lives in the database."""

    def __init__(self):
        self.settings = get_settings()
        self.user_model = UserModel()
        self.conversation = ConversationModel()
        self.memory = MemoryModel()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def process_text(self, message: str, user_phone: str, intent: str = "chat") -> str:
        """Process a text message and return the AI response."""
        try:
            user = self.user_model.get_user(user_phone)
            user_role = self.user_model.get_user_role(user_phone)
            user_name = self._resolve_display_name(user_phone, user, user_role)

            # Build context
            db_context = build_db_context(intent)
            system_prompt = build_system_prompt(
                user_name=user_name,
                user_role=user_role,
                intent=intent,
                db_context=db_context,
                village_name=self.settings.app.village_name,
            )

            # Build messages
            messages = self._build_messages(system_prompt, user_phone, message)

            # Call AI
            reply = chat_completion(messages, temperature=0.7, max_tokens=400)

            # Persist
            self._save_turn(user_phone, message, reply)
            self._try_extract_facts(user_phone, message, reply)

            return reply
        except Exception as e:
            logger.error("Agent text processing error: %s", e, exc_info=True)
            return FALLBACK_RESPONSE

    def process_image(self, image_data: bytes, user_phone: str, caption: str = "") -> str:
        """Process an image message (waste classification) and return the AI response."""
        try:
            user = self.user_model.get_user(user_phone)
            user_role = self.user_model.get_user_role(user_phone)
            user_name = self._resolve_display_name(user_phone, user, user_role)

            system_prompt = build_system_prompt(
                user_name=user_name,
                user_role=user_role,
                intent="image_analysis",
                village_name=self.settings.app.village_name,
            )

            # Encode image to base64 data URL
            b64 = base64.b64encode(image_data).decode("utf-8")
            mime = _detect_mime(image_data)
            data_url = f"data:{mime};base64,{b64}"

            # Build multimodal message
            user_content: List[Dict[str, Any]] = [
                {"type": "image_url", "image_url": {"url": data_url}},
            ]
            if caption:
                user_content.insert(0, {"type": "text", "text": caption})
            else:
                user_content.insert(0, {"type": "text", "text": "Tolong analisis gambar ini."})

            history = self._get_history(user_phone)
            messages = [{"role": "system", "content": system_prompt}]
            messages.extend(history)
            messages.append({"role": "user", "content": user_content})

            reply = chat_completion_with_image(messages, temperature=0.5, max_tokens=500)

            self._save_turn(user_phone, "[Mengirim foto]", reply)
            return reply
        except Exception as e:
            logger.error("Agent image processing error: %s", e, exc_info=True)
            return FALLBACK_RESPONSE

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------
    def _build_messages(
        self, system_prompt: str, user_phone: str, current_message: str
    ) -> List[Dict[str, str]]:
        messages = [{"role": "system", "content": system_prompt}]
        messages.extend(self._get_history(user_phone))
        messages.append({"role": "user", "content": current_message})
        return messages

    def _get_history(self, user_phone: str) -> List[Dict[str, str]]:
        rows = self.conversation.get_recent(user_phone, limit=20)
        return [{"role": r["message_role"], "content": r["message_content"]} for r in rows]

    def _save_turn(self, user_phone: str, user_msg: str, assistant_msg: str) -> None:
        try:
            self.conversation.add_message(user_phone, "user", user_msg)
            self.conversation.add_message(user_phone, "assistant", assistant_msg)
            # Auto-trim to prevent unbounded growth (keep last 60 messages)
            self.conversation.trim(user_phone, max_messages=60)
        except Exception as e:
            logger.error("Error saving conversation turn: %s", e)

    def _resolve_display_name(self, user_phone: str, user: Optional[dict], role: str) -> str:
        if user and user.get("name") and user["name"].strip().lower() not in ("", "none", "null"):
            return user["name"]
        facts = self.memory.get_all_facts(user_phone)
        if "user_name" in facts:
            return facts["user_name"]["value"]
        if "user_alias" in facts:
            return facts["user_alias"]["value"]
        # Generate stable alias
        digits = "".join(c for c in user_phone if c.isdigit())
        alias = f"eco{digits[-4:]}" if len(digits) >= 4 else "Teman"
        try:
            self.memory.save_fact(user_phone, "user_alias", alias)
        except Exception:
            pass
        return alias

    def _try_extract_facts(self, user_phone: str, user_msg: str, reply: str) -> None:
        """Lightweight fact extraction — full NER can be added later."""
        lower = user_msg.lower()
        # Simple name extraction
        for prefix in ("nama saya ", "namaku ", "panggil saya ", "saya "):
            if prefix in lower:
                idx = lower.index(prefix) + len(prefix)
                name_candidate = user_msg[idx:].split(",")[0].split(".")[0].strip()
                if 2 <= len(name_candidate) <= 50:
                    self.memory.save_fact(user_phone, "user_name", name_candidate)
                    break


def _detect_mime(data: bytes) -> str:
    if data[:8].startswith(b"\x89PNG"):
        return "image/png"
    if data[:3] == b"\xff\xd8\xff":
        return "image/jpeg"
    if data[:4] == b"GIF8":
        return "image/gif"
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "image/webp"
    return "image/jpeg"
