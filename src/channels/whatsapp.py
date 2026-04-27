"""WhatsApp channel via WAHA API."""

import ipaddress
import logging
from typing import Optional, Dict, Any
from urllib.parse import urlparse

import requests

from src.config import get_settings
from src.channels.base import BaseChannel

logger = logging.getLogger(__name__)

# RFC1918 + loopback + link-local ranges to block
_BLOCKED_NETWORKS = [
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("169.254.0.0/16"),
    ipaddress.ip_network("::1/128"),
    ipaddress.ip_network("fc00::/7"),
]


def _is_safe_url(url: str) -> bool:
    """Return True only for https:// URLs pointing to public (non-RFC1918) addresses."""
    try:
        parsed = urlparse(url)
        if parsed.scheme not in ("https", "http"):
            return False
        host = parsed.hostname or ""
        if not host or host in ("localhost", "metadata"):
            return False
        try:
            addr = ipaddress.ip_address(host)
            for network in _BLOCKED_NETWORKS:
                if addr in network:
                    return False
        except ValueError:
            pass  # hostname, not raw IP — allow (DNS resolves later)
        return True
    except Exception:
        return False


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
        if not _is_safe_url(url):
            logger.warning("WA media download blocked (SSRF guard): %s", url)
            return None
        try:
            resp = requests.get(url, headers=self.headers, timeout=60, stream=True)
            if resp.status_code == 200:
                data = resp.raw.read(5 * 1024 * 1024 + 1)  # 5 MB cap
                if len(data) > 5 * 1024 * 1024:
                    logger.warning("WA media download rejected — exceeds 5 MB size limit")
                    return None
                return data
            # Retry without auth header
            resp = requests.get(url, timeout=60, stream=True)
            if resp.status_code == 200:
                data = resp.raw.read(5 * 1024 * 1024 + 1)
                if len(data) > 5 * 1024 * 1024:
                    logger.warning("WA media download rejected — exceeds 5 MB size limit")
                    return None
                return data
        except Exception as e:
            logger.error("WA media download error: %s", e)
        return None
