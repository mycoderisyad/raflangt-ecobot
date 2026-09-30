"""Telegram channel via Bot HTTP API."""

import logging
import json
from typing import Optional, Dict, Any

import requests

from src.config import get_settings
from src.channels.base import BaseChannel
from src.utils.formatting import md_to_telegram_html

logger = logging.getLogger(__name__)

_TG_API = "https://api.telegram.org"


class TelegramChannel(BaseChannel):
    def __init__(self):
        cfg = get_settings().telegram
        self.token = cfg.bot_token
        self._api = f"{_TG_API}/bot{self.token}"

    def _request(self, method: str, *, json_data=None, params=None, timeout=30):
        response = requests.post(
            f"{self._api}/{method}", json=json_data, params=params, timeout=timeout
        )
        response.raise_for_status()
        result = response.json()
        if not result.get("ok"):
            raise RuntimeError(result.get("description", "Telegram API request failed"))
        return result.get("result")

    def get_me(self) -> dict:
        return self._request("getMe")

    def get_webhook_info(self) -> dict:
        return self._request("getWebhookInfo")

    def delete_webhook(self) -> bool:
        return bool(
            self._request("deleteWebhook", json_data={"drop_pending_updates": False})
        )

    def set_webhook(self, url: str, secret: str) -> bool:
        return bool(
            self._request(
                "setWebhook",
                json_data={
                    "url": url,
                    "secret_token": secret,
                    "allowed_updates": ["message"],
                },
            )
        )

    def get_updates(self, offset: int | None = None, timeout: int = 25) -> list[dict]:
        params = {"timeout": timeout, "allowed_updates": json.dumps(["message"])}
        if offset is not None:
            params["offset"] = offset
        return self._request("getUpdates", params=params, timeout=timeout + 10) or []

    def send_message(self, recipient: str, text: str) -> bool:
        try:
            # Convert AI Markdown → Telegram HTML
            html_text = md_to_telegram_html(text)
            resp = requests.post(
                f"{self._api}/sendMessage",
                json={"chat_id": recipient, "text": html_text, "parse_mode": "HTML"},
                timeout=30,
            )
            if resp.status_code == 200 and resp.json().get("ok"):
                return True

            # HTML parse failed → retry as plain text (strip formatting)
            if resp.status_code == 400 and "parse entities" in resp.text:
                logger.warning("TG HTML parse failed, retrying as plain text")
                resp = requests.post(
                    f"{self._api}/sendMessage",
                    json={"chat_id": recipient, "text": text},
                    timeout=30,
                )
                if resp.status_code == 200 and resp.json().get("ok"):
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

        # This bot serves individual residents; group and channel messages are ignored.
        if msg.get("chat", {}).get("type") != "private":
            return None

        chat_id = str(msg["chat"]["id"])
        username = msg.get("from", {}).get("username", "") or ""

        # Photo message
        if "photo" in msg:
            photos = msg["photo"]
            # Pick largest resolution
            file_id = photos[-1]["file_id"]
            return {
                "from_id": chat_id,
                "username": username,
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
            "username": username,
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
            resp = requests.get(
                f"{self._api}/getFile", params={"file_id": file_id}, timeout=30
            )
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
