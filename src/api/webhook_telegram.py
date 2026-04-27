"""Telegram webhook endpoint."""

import hmac
import logging
import os
from flask import Blueprint, jsonify, request

from src.config import get_settings
from src.channels.telegram import TelegramChannel
from src.core.orchestrator import Orchestrator

logger = logging.getLogger(__name__)

tg_webhook_bp = Blueprint("tg_webhook", __name__)

_channel: TelegramChannel | None = None
_orchestrator: Orchestrator | None = None


def _lazy_init():
    global _channel, _orchestrator
    if _channel is None:
        _channel = TelegramChannel()
        _orchestrator = Orchestrator()


def _verify_telegram_secret() -> bool:
    """Validate X-Telegram-Bot-Api-Secret-Token header (constant-time compare).

    Fail-closed: if TELEGRAM_WEBHOOK_SECRET is not set, ALL requests are rejected.
    """
    secret = os.getenv("TELEGRAM_WEBHOOK_SECRET", "")
    if not secret:
        logger.error(
            "TELEGRAM_WEBHOOK_SECRET not set — rejecting ALL Telegram webhook requests. "
            "Set the variable and re-register the webhook."
        )
        return False
    token = request.headers.get("X-Telegram-Bot-Api-Secret-Token", "")
    return hmac.compare_digest(token.encode(), secret.encode())


@tg_webhook_bp.route("/webhook/telegram", methods=["POST"])
def telegram_webhook():
    cfg = get_settings()
    if not cfg.telegram.enabled:
        return jsonify({"status": "disabled"}), 200

    if not _verify_telegram_secret():
        logger.warning("Telegram webhook rejected — invalid secret token (IP: %s)", request.remote_addr)
        return jsonify({"error": "Forbidden"}), 403

    _lazy_init()
    try:
        payload = request.get_json(silent=True) or {}
        msg = _channel.parse_webhook(payload)
        if not msg:
            return jsonify({"status": "ignored"})

        username = msg.get("username", "")

        if msg["message_type"] == "image":
            image_data = _channel.download_media(msg["image_url"])
            if image_data:
                reply = _orchestrator.handle_image(
                    msg["from_id"], image_data, caption=msg.get("caption", ""),
                    channel="telegram", username=username,
                )
            else:
                reply = "Maaf, gambar tidak bisa diunduh. Coba kirim lagi ya."
        else:
            reply = _orchestrator.handle_text(
                msg["from_id"], msg["body"], channel="telegram", username=username,
            )

        if reply:
            _channel.send_message(msg["from_id"], reply)

        return jsonify({"status": "ok"})
    except Exception as e:
        logger.error("TG webhook error: %s", e, exc_info=True)
        return jsonify({"status": "error", "message": "Internal error"}), 500
