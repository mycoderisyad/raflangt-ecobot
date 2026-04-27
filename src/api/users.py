"""User admin API endpoints."""

import hmac
import os
import functools
import logging
from flask import Blueprint, jsonify, request
from src.database.models.user import UserModel

logger = logging.getLogger(__name__)

users_bp = Blueprint("users", __name__, url_prefix="/api")


def _require_api_key(f):
    """Decorator that validates the X-API-Key header against API_SECRET_KEY env."""
    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        secret = os.getenv("API_SECRET_KEY", "")
        if not secret:
            logger.warning("API_SECRET_KEY not set — all admin API requests will be rejected")
            return jsonify({"error": "Server misconfiguration"}), 500
        key = request.headers.get("X-API-Key", "")
        if not hmac.compare_digest(key.encode(), secret.encode()):
            return jsonify({"error": "Unauthorized"}), 401
        return f(*args, **kwargs)
    return wrapper


@users_bp.route("/users", methods=["GET"])
@_require_api_key
def list_users():
    model = UserModel()
    limit = request.args.get("limit", 100, type=int)
    offset = request.args.get("offset", 0, type=int)
    users = model.list_users(limit=limit, offset=offset)
    return jsonify({"users": users, "total": model.count_users()})


@users_bp.route("/users/<phone>", methods=["GET"])
@_require_api_key
def get_user(phone: str):
    model = UserModel()
    user = model.get_user(phone)
    if user:
        return jsonify(user)
    return jsonify({"error": "User not found"}), 404
