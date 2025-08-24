"""
Role Manager
Manages user roles and feature access permissions
"""

from core.constants import FEATURE_STATUS
from database.models import UserModel, DatabaseManager


class RoleManager:
    """Role management functionality"""

    @staticmethod
    def get_user_role(phone_number: str) -> str:
        """Get user role from database"""
        db = DatabaseManager()
        user_model = UserModel(db)
        return user_model.get_user_role(phone_number)

    @staticmethod
    def has_feature_access(role: str, feature: str) -> bool:
        """Check if role has access to feature"""
        role_features = FEATURE_STATUS.get(role, {})
        return role_features.get(feature, False)
