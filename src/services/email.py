"""Email service via Resend API."""

import logging
from typing import Optional

import resend

from src.config import get_settings

logger = logging.getLogger(__name__)


def _init_resend() -> bool:
    cfg = get_settings().email
    if not cfg.resend_api_key:
        logger.warning("RESEND_API_KEY not configured — email disabled")
        return False
    resend.api_key = cfg.resend_api_key
    return True


def send_email(
    subject: str,
    html: str,
    to: Optional[str] = None,
    attachments: Optional[list] = None,
) -> dict:
    """Send an email via Resend. Returns {"success": bool, "error": str|None}."""
    if not _init_resend():
        return {"success": False, "error": "Email not configured"}

    cfg = get_settings().email
    recipient = to or cfg.to_email
    if not recipient:
        return {"success": False, "error": "No recipient email configured"}

    try:
        params = {
            "from_": cfg.from_email or "EcoBot <noreply@ecobot.id>",
            "to": [recipient],
            "subject": subject,
            "html": html,
        }
        if attachments:
            params["attachments"] = attachments

        resp = resend.Emails.send(params)
        logger.info("Email sent: %s", resp)
        return {"success": True, "error": None, "id": resp.get("id")}
    except Exception as e:
        logger.error("Email send error: %s", e)
        return {"success": False, "error": str(e)}
