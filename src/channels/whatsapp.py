"""WhatsApp channel via WAHA API."""

import logging
from typing import Optional, Dict, Any

import requests

from src.config import get_settings
from src.channels.base import BaseChannel

logger = logging.getLogger(__name__)


class WhatsAppChannel(BaseChannel):

    def __init__(self):
        cfg = get_settings().whatsapp
        self.base_url = cfg.base_url.rstrip("/")
        self.api_key = cfg.api_key
        self.session_name = cfg.session_name
        self.headers = {"X-Api-Key": self.api_key, "Content-Type": "application/json"}

    def send_message(self, recipient: str, text: str) -> bool:
        try:
            url = f"{self.base_url}/api/sendText"
            payload = {"session": self.session_name, "chatId": recipient, "text": text}
            resp = requests.post(url, json=payload, headers=self.headers, timeout=30)
            if 200 <= resp.status_code < 300:
                return True
            logger.error("WA send failed %s: %s", resp.status_code, resp.text)
            return False
        except Exception as e:
            logger.error("WA send error: %s", e)
            return False

    def parse_webhook(self, payload: dict) -> Optional[Dict[str, Any]]:
        """Parse WAHA webhook into normalised message dict."""
        event = payload.get("event", "")
        if event not in ("message", "message.any"):
            return None

        body_payload = payload.get("payload", {})
        from_id = body_payload.get("from", "")
        if not from_id:
            return None

        # Determine message type
        has_media = body_payload.get("hasMedia", False)
        msg_type = body_payload.get("type", "chat")

        if has_media and msg_type == "image":
            return {
                "from_id": from_id,
                "message_type": "image",
                "body": body_payload.get("body", ""),
                "caption": body_payload.get("caption", body_payload.get("body", "")),
                "image_url": body_payload.get("mediaUrl", ""),
                "media_info": body_payload,
            }

        text = body_payload.get("body", "").strip()
        if not text:
            return None

        return {
            "from_id": from_id,
            "message_type": "text",
            "body": text,
            "caption": "",
            "image_url": "",
        }

    def download_media(self, url: str) -> Optional[bytes]:
        if not url:
            return None
        try:
            resp = requests.get(url, headers=self.headers, timeout=60)
            if resp.status_code == 200:
                return resp.content
            # Try without auth header
            resp = requests.get(url, timeout=60)
            if resp.status_code == 200:
                return resp.content
        except Exception as e:
            logger.error("WA media download error: %s", e)
        return None
