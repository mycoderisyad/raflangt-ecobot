"""WhatsApp webhook endpoint."""

import logging
from flask import Blueprint, jsonify, request

from src.config import get_settings
from src.channels.whatsapp import WhatsAppChannel
from src.core.orchestrator import Orchestrator

logger = logging.getLogger(__name__)

wa_webhook_bp = Blueprint("wa_webhook", __name__)

_channel: WhatsAppChannel | None = None
_orchestrator: Orchestrator | None = None


def _lazy_init():
    global _channel, _orchestrator
    if _channel is None:
        _channel = WhatsAppChannel()
        _orchestrator = Orchestrator()


@wa_webhook_bp.route("/webhook/whatsapp", methods=["POST"])
def whatsapp_webhook():
    cfg = get_settings()
    if not cfg.whatsapp.enabled:
        return jsonify({"status": "disabled"}), 200

    _lazy_init()
    try:
        payload = request.get_json(silent=True) or {}
        msg = _channel.parse_webhook(payload)
        if not msg:
            return jsonify({"status": "ignored"})

        if msg["message_type"] == "image":
            image_data = _channel.download_media(msg["image_url"])
            if image_data:
                reply = _orchestrator.handle_image(msg["from_id"], image_data, caption=msg.get("caption", ""))
            else:
                reply = "Maaf, gambar tidak bisa diunduh. Coba kirim lagi ya."
        else:
            reply = _orchestrator.handle_text(msg["from_id"], msg["body"])

        if reply:
            _channel.send_message(msg["from_id"], reply)

        return jsonify({"status": "ok"})
    except Exception as e:
        logger.error("WA webhook error: %s", e, exc_info=True)
        return jsonify({"status": "error", "message": "Internal error"}), 500
