"""Telegram channel via Bot HTTP API."""

import logging
from typing import Optional, Dict, Any

import requests

from src.config import get_settings
from src.channels.base import BaseChannel

logger = logging.getLogger(__name__)

_TG_API = "https://api.telegram.org"


class TelegramChannel(BaseChannel):

    def __init__(self):
        cfg = get_settings().telegram
        self.token = cfg.bot_token
        self._api = f"{_TG_API}/bot{self.token}"

    def send_message(self, recipient: str, text: str) -> bool:
        try:
            resp = requests.post(
                f"{self._api}/sendMessage",
                json={"chat_id": recipient, "text": text, "parse_mode": "Markdown"},
                timeout=30,
            )
            if resp.status_code == 200:
                return True
            logger.error("TG send failed %s: %s", resp.status_code, resp.text)
            return False
        except Exception as e:
            logger.error("TG send error: %s", e)
            return False

    def parse_webhook(self, payload: dict) -> Optional[Dict[str, Any]]:
        """Parse Telegram update into normalised message dict."""
        msg = payload.get("message")
        if not msg:
            return None

        chat_id = str(msg["chat"]["id"])
        # Photo message
        if "photo" in msg:
            photos = msg["photo"]
            # Pick largest resolution
            file_id = photos[-1]["file_id"]
            return {
                "from_id": chat_id,
                "message_type": "image",
                "body": msg.get("caption", ""),
                "caption": msg.get("caption", ""),
                "image_url": file_id,  # Will be resolved via get_file
                "media_info": {"file_id": file_id},
            }

        text = msg.get("text", "").strip()
        if not text:
            return None

        return {
            "from_id": chat_id,
            "message_type": "text",
            "body": text,
            "caption": "",
            "image_url": "",
        }

    def download_media(self, file_id: str) -> Optional[bytes]:
        """Download a file from Telegram by file_id."""
        if not file_id:
            return None
        try:
            # Step 1: get file path
            resp = requests.get(f"{self._api}/getFile", params={"file_id": file_id}, timeout=30)
            if resp.status_code != 200:
                return None
            file_path = resp.json().get("result", {}).get("file_path")
            if not file_path:
                return None
            # Step 2: download
            dl_url = f"{_TG_API}/file/bot{self.token}/{file_path}"
            dl_resp = requests.get(dl_url, timeout=60)
            if dl_resp.status_code == 200:
                return dl_resp.content
        except Exception as e:
            logger.error("TG media download error: %s", e)
        return None
