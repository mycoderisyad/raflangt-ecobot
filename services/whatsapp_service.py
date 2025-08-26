"""
WhatsApp Service
Handles WhatsApp communication via WAHA API
"""

import requests
import os
import json
import logging
from typing import Dict, Any, Optional
from core.utils import LoggerUtils


class WhatsAppService:
    """WhatsApp communication service"""

    def __init__(self):
        self.api_key = os.getenv("WAHA_API_KEY")
        self.base_url = os.getenv("WAHA_BASE_URL")
        self.session_name = os.getenv("WAHA_SESSION_NAME", "default")
        self.environment = os.getenv("ENVIRONMENT", "development")
        self.logger = logging.getLogger(__name__)

        if not self.api_key and self.environment == "production":
            raise ValueError("WhatsApp API key is required for production")

        self.headers = {"X-Api-Key": self.api_key, "Content-Type": "application/json"}

    def send_message(self, phone_number: str, message: str) -> bool:
        """Send WhatsApp message"""
        try:
            url = f"{self.base_url}/api/sendText"
            payload = {
                "session": self.session_name,
                "chatId": phone_number,
                "text": message,
            }

            # Debug logging
            if self.environment == "development":
                self.logger.info(f"Sending message to URL: {url}")
                self.logger.info(f"Payload: {payload}")

            response = requests.post(
                url, json=payload, headers=self.headers, timeout=30
            )

            if 200 <= response.status_code < 300:
                if self.environment == "development":
                    self.logger.info(f"Message sent successfully to {phone_number}")
                return True
            else:
                self.logger.error(
                    f"Failed to send message: {response.status_code} - Response: {response.text}"
                )
                return False

        except Exception as e:
            self.logger.error(f"Error sending message: {e}")
            return False

    def download_media(
        self, media_url: str, media_info: dict = None
    ) -> Optional[bytes]:
        """Download media from WAHA with multiple URL format attempts"""
        try:
            if not media_url:
                if self.environment == "development":
                    self.logger.warning("No media URL provided")
                return None

            # Try original URL first
            content = self._try_download_url(media_url)
            if content:
                return content

            # If original fails, try alternative URL formats
            if media_info:
                alternative_urls = self._generate_alternative_urls(media_info)

                for url in alternative_urls:
                    content = self._try_download_url(url)
                    if content:
                        if self.environment == "development":
                            self.logger.info(
                                "Successfully downloaded media using alternative URL"
                            )
                        return content

            self.logger.error("All media download attempts failed")
            return None

        except Exception as e:
            LoggerUtils.log_error(self.logger, e, "downloading media")
            return None

    def _try_download_url(self, url: str) -> Optional[bytes]:
        """Try downloading from a specific URL"""
        try:
            # Try multiple header formats for WAHA compatibility
            header_variants = [
                {"X-Api-Key": self.api_key, "Content-Type": "application/json"},
                {"X-API-Key": self.api_key, "Content-Type": "application/json"},
                {"Authorization": f"Bearer {self.api_key}"},
                {"X-Api-Key": self.api_key},
                {"X-API-Key": self.api_key},
            ]

            for headers in header_variants:
                response = requests.get(url, headers=headers, timeout=60)

                if response.status_code == 200:
                    content_size = len(response.content)
                    if content_size > 0:
                        if self.environment == "development":
                            self.logger.info(
                                f"Downloaded {content_size} bytes from {url}"
                            )
                        return response.content
                elif response.status_code == 404:
                    continue  # Try next URL format
                else:
                    # Log non-404 errors as they might indicate other issues
                    if response.status_code in [401, 403]:
                        continue  # Try different headers
                    else:
                        break  # Other errors won't change with different headers

            return None
        except Exception as e:
            if self.environment == "development":
                self.logger.warning(f"Download exception for {url}: {e}")
            return None

    def _generate_alternative_urls(self, media_info: dict) -> list:
        """Generate alternative media download URLs"""
        urls = []

        filename = media_info.get("filename", "")
        message_id = media_info.get("id", "")
        original_url = media_info.get("url", "")

        # Parse filename from original URL if not provided separately
        if not filename and original_url:
            filename = original_url.split("/")[-1]

        # Fix the original URL by inserting session name
        if original_url and self.session_name:
            if (
                "/files/" in original_url
                and f"/{self.session_name}/" not in original_url
            ):
                fixed_url = original_url.replace(
                    "/files/", f"/files/{self.session_name}/"
                )
                urls.append(fixed_url)
                if self.environment == "development":
                    self.logger.info(f"Generated fixed URL with session: {fixed_url}")

        # Standard WAHA file download patterns
        if filename:
            urls.extend(
                [
                    f"{self.base_url}/files/{self.session_name}/{filename}",
                    f"{self.base_url}/{self.session_name}/files/{filename}",
                    f"{self.base_url}/media/{self.session_name}/{filename}",
                    f"{self.base_url}/{self.session_name}/media/{filename}",
                ]
            )

        # Message ID based patterns
        if message_id:
            urls.extend(
                [
                    f"{self.base_url}/messages/{self.session_name}/{message_id}/media",
                    f"{self.base_url}/{self.session_name}/messages/{message_id}/media",
                ]
            )

        return urls

    def parse_webhook_message(
        self, webhook_data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Parse webhook message data with intelligent image detection"""
        try:
            event = webhook_data.get("event")
            payload = webhook_data.get("payload", {})

            # Check if this is a message event
            if event != "message":
                return None

            # Enhanced detection for image messages
            is_image = False
            media_url = None
            media_info = {}

            # Method 1: Direct type check
            if payload.get("type") == "image":
                is_image = True
                media_info = payload.get("media", {})
                media_url = media_info.get("url")

            # Method 2: Check hasMedia flag and mime type
            elif payload.get("hasMedia") or "mimetype" in str(payload):
                is_image = True
                if "mimetype" in payload and "image" in payload.get("mimetype", ""):
                    media_info = {
                        "url": f"https://waha.rafgt.my.id/api/files/default/{payload.get('id', 'unknown')}.jpeg",
                        "mimetype": payload.get("mimetype", "image/jpeg"),
                        "filename": payload.get("id", "unknown") + ".jpeg",
                    }
                    media_url = media_info["url"]
                elif payload.get("media"):
                    media_info = payload.get("media", {})
                    media_url = media_info.get("url")

            # Method 3: Check _data for image indicators
            elif "_data" in payload:
                _data = payload.get("_data", {})
                if "mimetype" in _data and "image" in _data.get("mimetype", ""):
                    is_image = True
                    message_id = payload.get("id", "unknown")
                    media_info = {
                        "url": f"https://waha.rafgt.my.id/api/files/default/{message_id}.jpeg",
                        "mimetype": _data.get("mimetype", "image/jpeg"),
                        "filename": message_id + ".jpeg",
                    }
                    media_url = media_info["url"]

            # Determine message type
            message_type = "image" if is_image else payload.get("type", "text")

            # Development logging only
            if is_image and self.environment == "development":
                self.logger.info(f"Image message detected - URL: {media_url}")

            parsed_data = {
                "from_number": payload.get("from", ""),
                "message_body": payload.get("body", "").strip(),
                "message_type": message_type,
                "media_url": media_url,
                "media_info": media_info,
                "message_id": payload.get("id", ""),
                "timestamp": payload.get("timestamp", ""),
            }

            return parsed_data

        except Exception as e:
            LoggerUtils.log_error(self.logger, e, "parsing webhook message")
            return None
