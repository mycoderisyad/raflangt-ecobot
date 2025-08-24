"""
Database Models Package
Main entry point untuk semua database models
"""

from .base import DatabaseManager
from .user import UserModel
from .waste_classification import WasteClassificationModel
from .collection import CollectionPointModel, CollectionScheduleModel
from .system import UserInteractionModel, SystemLogModel

__all__ = [
    "DatabaseManager",
    "UserModel",
    "WasteClassificationModel",
    "CollectionPointModel",
    "CollectionScheduleModel",
    "UserInteractionModel",
    "SystemLogModel",
]

# Single instance database manager untuk digunakan di seluruh aplikasi
db_manager = None


def init_models(db_path: str = None):
    """Initialize database manager and all models"""
    global db_manager
    if not db_manager:
        db_manager = DatabaseManager(db_path)
        db_manager.init_database()
    return db_manager


def get_db_manager():
    """Get the global database manager instance"""
    global db_manager
    if not db_manager:
        raise RuntimeError("Database not initialized. Call init_models() first.")
    return db_manager


# Model instances untuk kemudahan akses
def get_user_model():
    """Get UserModel instance"""
    return UserModel(get_db_manager())


def get_waste_classification_model():
    """Get WasteClassificationModel instance"""
    return WasteClassificationModel(get_db_manager())


def get_collection_point_model():
    """Get CollectionPointModel instance"""
    return CollectionPointModel(get_db_manager())


def get_collection_schedule_model():
    """Get CollectionScheduleModel instance"""
    return CollectionScheduleModel(get_db_manager())


def get_user_interaction_model():
    """Get UserInteractionModel instance"""
    return UserInteractionModel(get_db_manager())


def get_system_log_model():
    """Get SystemLogModel instance"""
    return SystemLogModel(get_db_manager())
