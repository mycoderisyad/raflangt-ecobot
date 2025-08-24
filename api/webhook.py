"""
Webhook API Endpoints
WhatsApp webhook handling
"""

import logging
from flask import Blueprint, jsonify, request
from core.application_handler import ApplicationHandler
from core.utils import LoggerUtils

# Create blueprint
webhook_bp = Blueprint("webhook", __name__, url_prefix="/")

logger = logging.getLogger(__name__)

# Initialize application handler at module level
app_handler = ApplicationHandler()


@webhook_bp.route("/webhook", methods=["POST"])
def webhook():
    """WhatsApp webhook endpoint"""
    try:
        result = app_handler.handle_incoming_message(request)
        return jsonify(result)
    except Exception as e:
        # Get environment for error handling
        import os

        environment = os.getenv("ENVIRONMENT", "development")

        # Log error internally but return generic response in production
        if environment == "production":
            logger.error(f"Webhook processing error: {str(e)}")
            return jsonify({"status": "error", "message": "Internal server error"}), 500
        else:
            # Development: show detailed error
            LoggerUtils.log_error(logger, e, "webhook processing")
            return jsonify({"status": "error", "message": str(e)}), 500
