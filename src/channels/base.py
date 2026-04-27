"""Abstract messaging channel interface."""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any


class BaseChannel(ABC):
    """All messaging channels implement this interface."""

    @abstractmethod
    def send_message(self, recipient: str, text: str) -> bool:
        ...

    @abstractmethod
    def parse_webhook(self, payload: dict) -> Optional[Dict[str, Any]]:
        """Parse raw webhook payload into a normalised message dict.

        Returns None if the event should be ignored.
        Expected keys: from_id, message_type ('text'|'image'), body, image_url, caption
        """
        ...

    @abstractmethod
    def download_media(self, url: str) -> Optional[bytes]:
        ...
