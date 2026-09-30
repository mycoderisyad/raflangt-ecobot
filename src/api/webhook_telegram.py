"""Telegram webhook receiver and shared update processor."""

import hmac
import logging

from fastapi import APIRouter, Header, HTTPException, Request, status

from src.channels.telegram import TelegramChannel
from src.config import get_settings
from src.core.orchestrator import Orchestrator
from src.database.connection import get_db

logger = logging.getLogger(__name__)
router = APIRouter(tags=["telegram"])
_orchestrator: Orchestrator | None = None


def process_update(payload: dict) -> str:
    """Process one Telegram update; return the outcome for webhook and polling callers."""
    global _orchestrator
    update_id = payload.get("update_id")
    if update_id is not None:
        with get_db() as db:
            previous = db.fetchone(
                "SELECT status FROM telegram_updates WHERE update_id = %s", (update_id,)
            )
        if previous and previous["status"] == "processed":
            return "duplicate"

    channel = TelegramChannel()
    message = channel.parse_webhook(payload)
    if not message:
        _mark_processed(update_id)
        return "ignored"

    if _orchestrator is None:
        _orchestrator = Orchestrator()
    if message["message_type"] == "image":
        image_data = channel.download_media(message["image_url"])
        reply = (
            _orchestrator.handle_image(
                message["from_id"],
                image_data,
                caption=message.get("caption", ""),
                username=message.get("username", ""),
            )
            if image_data
            else "Maaf, gambar tidak bisa diunduh. Coba kirim lagi ya."
        )
    else:
        reply = _orchestrator.handle_text(
            message["from_id"],
            message["body"],
            username=message.get("username", ""),
        )
    if reply and not channel.send_message(message["from_id"], reply):
        raise RuntimeError("Telegram gagal mengirim balasan")
    _mark_processed(update_id)
    return "ok"


def _mark_processed(update_id: int | None) -> None:
    if update_id is None:
        return
    with get_db() as db:
        db.execute(
            """INSERT INTO telegram_updates (update_id, status, processed_at)
               VALUES (%s, 'processed', NOW())
               ON CONFLICT (update_id) DO UPDATE SET status='processed', processed_at=NOW()""",
            (update_id,),
        )


@router.post("/webhook/telegram")
def telegram_webhook(
    request: Request,
    payload: dict,
    secret_token: str
    | None = Header(default=None, alias="X-Telegram-Bot-Api-Secret-Token"),
) -> dict[str, str]:
    cfg = get_settings().telegram
    if not cfg.enabled:
        return {"status": "disabled"}
    if cfg.mode != "webhook":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Telegram sedang berjalan dalam mode polling",
        )
    if not cfg.webhook_secret or not hmac.compare_digest(
        secret_token or "", cfg.webhook_secret
    ):
        logger.warning(
            "Telegram webhook rejected from %s",
            request.client.host if request.client else "unknown",
        )
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    try:
        return {"status": process_update(payload)}
    except Exception as exc:
        logger.exception("Telegram update processing failed")
        raise HTTPException(
            status_code=500, detail="Telegram update processing failed"
        ) from exc
