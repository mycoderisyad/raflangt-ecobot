"""
Users API Endpoints  
Mengelola data pengguna sistem
"""

import logging
from flask import Blueprint, jsonify
from core.api_key_auth import require_api_key
from database.models.base import DatabaseManager
from database.models.user import UserModel

# Create blueprint
users_bp = Blueprint("users", __name__, url_prefix="/api")

logger = logging.getLogger(__name__)


@users_bp.route("/users", methods=["GET"])
@require_api_key
def get_users():
    """Get all users"""
    try:
        db_manager = DatabaseManager()
        user_model = UserModel(db_manager)

        users = user_model.get_all_users()
        return jsonify({"status": "success", "data": users})
    except Exception as e:
        logger.error(f"Error getting users: {str(e)}")
        return jsonify({"status": "error", "message": "Failed to get users"}), 500


@users_bp.route("/users/stats", methods=["GET"])
@require_api_key
def get_user_stats():
    """Get user statistics"""
    try:
        db_manager = DatabaseManager()
        user_model = UserModel(db_manager)

        # Get all users for stats calculation
        users = user_model.get_all_users()

        # Calculate statistics
        total_users = len(users)
        active_users = len([u for u in users if u.get("is_active", 0) == 1])
        total_points = sum(u.get("points", 0) for u in users)
        total_messages = sum(u.get("total_messages", 0) for u in users)
        total_images = sum(u.get("total_images", 0) for u in users)

        # Role distribution
        roles = {}
        for user in users:
            role = user.get("role", "user")
            roles[role] = roles.get(role, 0) + 1

        return jsonify(
            {
                "status": "success",
                "data": {
                    "total_users": total_users,
                    "active_users": active_users,
                    "total_points": total_points,
                    "total_messages": total_messages,
                    "total_images": total_images,
                    "role_distribution": roles,
                },
            }
        )
    except Exception as e:
        logger.error(f"Error getting user stats: {str(e)}")
        return (
            jsonify({"status": "error", "message": "Failed to get user statistics"}),
            500,
        )


@users_bp.route("/users/<phone_number>", methods=["GET"])
@require_api_key
def get_user(phone_number):
    """Get specific user by phone number"""
    try:
        db_manager = DatabaseManager()
        user_model = UserModel(db_manager)

        user = user_model.get_user(phone_number)
        if user:
            return jsonify({"status": "success", "data": user})
        else:
            return jsonify({"status": "error", "message": "User not found"}), 404
    except Exception as e:
        logger.error(f"Error getting user: {str(e)}")
        return jsonify({"status": "error", "message": "Failed to get user"}), 500
