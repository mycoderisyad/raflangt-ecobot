"""User admin API endpoints."""

import logging
from flask import Blueprint, jsonify, request
from src.database.models.user import UserModel

logger = logging.getLogger(__name__)

users_bp = Blueprint("users", __name__, url_prefix="/api")


@users_bp.route("/users", methods=["GET"])
def list_users():
    model = UserModel()
    limit = request.args.get("limit", 100, type=int)
    offset = request.args.get("offset", 0, type=int)
    users = model.list_users(limit=limit, offset=offset)
    return jsonify({"users": users, "total": model.count_users()})


@users_bp.route("/users/<phone>", methods=["GET"])
def get_user(phone: str):
    model = UserModel()
    user = model.get_user(phone)
    if user:
        return jsonify(user)
    return jsonify({"error": "User not found"}), 404
