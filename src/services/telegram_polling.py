"""Lifecycle-managed Telegram long-polling worker for local development."""

import logging
import threading

from src.api.webhook_telegram import process_update
from src.channels.telegram import TelegramChannel

logger = logging.getLogger(__name__)


class TelegramPollingWorker:
    def __init__(self) -> None:
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        channel = TelegramChannel()
        webhook = channel.get_webhook_info()
        if webhook.get("url"):
            raise RuntimeError(
                "Webhook Telegram masih terpasang. Jalankan `python manage.py telegram:webhook:delete` "
                "sebelum memakai TELEGRAM_MODE=polling."
            )
        self._stop.clear()
        self._thread = threading.Thread(
            target=self._run, daemon=True, name="ecobot-telegram-polling"
        )
        self._thread.start()
        logger.info("Telegram long polling started")

    def stop(self) -> None:
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=40)
        logger.info("Telegram long polling stopped")

    def _run(self) -> None:
        channel = TelegramChannel()
        offset: int | None = None
        delay = 1
        while not self._stop.is_set():
            try:
                updates = channel.get_updates(offset=offset)
                delay = 1
                if not updates:
                    self._stop.wait(0.2)
                for update in updates:
                    try:
                        process_update(update)
                    except Exception:
                        logger.exception(
                            "Telegram polling could not process update_id=%s",
                            update.get("update_id"),
                        )
                        break
                    offset = int(update["update_id"]) + 1
                    if self._stop.is_set():
                        break
            except Exception:
                logger.exception(
                    "Telegram getUpdates failed; retrying in %s seconds", delay
                )
                self._stop.wait(delay)
                delay = min(delay * 2, 30)
