"""
Database package initialization
"""

# Import new modular models directly from models folder
from .models import (
    init_models,
    get_db_manager,
    get_user_model,
    get_waste_classification_model,
    get_collection_point_model,
    get_collection_schedule_model,
    get_user_interaction_model,
    get_system_log_model
)

# Import classes directly for backward compatibility
from .models.base import DatabaseManager as _DatabaseManager
from .models.user import UserModel as _UserModel  
from .models.waste_classification import WasteClassificationModel as _WasteClassificationModel
from .models.system import UserInteractionModel as _UserInteractionModel

# Backward compatibility wrappers
class DatabaseManager:
    """Backward compatibility wrapper for DatabaseManager"""
    
    def __init__(self, db_path: str = None):
        self._db_manager = init_models(db_path)
    
    def get_connection(self):
        """Get database connection"""
        return self._db_manager.get_connection()
    
    def init_database(self):
        """Initialize database with required tables"""
        return self._db_manager.init_database()
    
    def execute_query(self, query: str, params: tuple = None):
        """Execute a query and return results"""
        return self._db_manager.execute_query(query, params)


class UserModel:
    """Backward compatibility wrapper for UserModel"""
    
    def __init__(self, db_manager=None):
        if db_manager is None:
            # Get the global database manager
            self._db_manager = get_db_manager()
        else:
            # Use provided database manager
            self._db_manager = db_manager._db_manager if hasattr(db_manager, '_db_manager') else db_manager
        
        # Create the actual model instance
        self._model = _UserModel(self._db_manager)
    
    def create_user(self, phone_number: str, name: str = None) -> bool:
        return self._model.create_user(phone_number, name)
    
    def get_user(self, phone_number: str):
        return self._model.get_user(phone_number)
    
    def update_user_role(self, phone_number: str, new_role: str, admin_phone: str = None) -> bool:
        return self._model.update_user_role(phone_number, new_role, admin_phone)
    
    def is_admin(self, phone_number: str) -> bool:
        return self._model.is_admin(phone_number)
    
    def is_koordinator(self, phone_number: str) -> bool:
        return self._model.is_koordinator(phone_number)
    
    def get_all_users(self, admin_phone: str = None):
        return self._model.get_all_users(admin_phone)
    
    # Legacy methods untuk backward compatibility
    def create_or_update_user(self, phone_number: str):
        """Legacy method - creates user if doesn't exist"""
        self._model.create_user(phone_number)
        return self._model.get_user(phone_number)
    
    def increment_user_stats(self, phone_number: str, stat_type: str):
        """Legacy method - increment user statistics"""
        if stat_type == 'message':
            self._model.increment_message_count(phone_number)
        elif stat_type == 'image':
            self._model.increment_image_count(phone_number)
    
    def get_user_stats(self, phone_number: str):
        """Legacy method - get user statistics"""
        return self._model.get_user(phone_number)
    
    def get_user_role(self, phone_number: str) -> str:
        """Legacy method - get user role"""
        user = self._model.get_user(phone_number)
        return user['role'] if user else 'warga'
    
    def add_user_points(self, phone_number: str, points: int) -> bool:
        """Legacy method - add points to user"""
        return self._model.add_points(phone_number, points)


class WasteClassificationModel:
    """Backward compatibility wrapper for WasteClassificationModel"""
    
    def __init__(self, db_manager=None):
        if db_manager is None:
            self._db_manager = get_db_manager()
        else:
            self._db_manager = db_manager._db_manager if hasattr(db_manager, '_db_manager') else db_manager
        
        self._model = _WasteClassificationModel(self._db_manager)
    
    def save_classification(self, user_phone: str, image_data=None, classification_result=None, 
                          waste_type=None, confidence=None, classification_method='ai', image_url=None):
        """Save waste classification - supports both new and legacy formats"""
        if classification_result:
            # New format
            return self._model.save_classification(user_phone, image_data, classification_result)
        else:
            # Legacy format
            legacy_result = {
                'waste_type': waste_type,
                'confidence': confidence,
                'classification_method': classification_method
            }
            return self._model.save_classification(user_phone, image_data or b'', legacy_result)
    
    def get_user_classifications(self, user_phone: str, limit: int = 10):
        return self._model.get_user_classifications(user_phone, limit)
    
    def get_classification_stats(self, admin_phone=None, days: int = 30):
        if admin_phone:
            return self._model.get_classification_stats(admin_phone, days)
        else:
            return self._model.get_classification_stats(days=days)


class UserInteractionModel:
    """Backward compatibility wrapper for UserInteractionModel"""
    
    def __init__(self, db_manager=None):
        if db_manager is None:
            self._db_manager = get_db_manager()
        else:
            self._db_manager = db_manager._db_manager if hasattr(db_manager, '_db_manager') else db_manager
        
        self._model = _UserInteractionModel(self._db_manager)
    
    def log_interaction(self, user_phone: str, interaction_type: str, 
                       message_content: str = None, response_content: str = None,
                       success: bool = True, response_time: float = None) -> bool:
        return self._model.log_interaction(user_phone, interaction_type, message_content, 
                                         response_content, success, response_time)
    
    def get_user_interactions(self, user_phone: str, limit: int = 50):
        return self._model.get_user_interactions(user_phone, limit)
    
    def get_interaction_stats(self, days: int = 7):
        return self._model.get_interaction_stats(days)


# Legacy aliases
InteractionModel = UserInteractionModel

# StatisticsModel for backward compatibility
class StatisticsModel:
    def __init__(self, db_manager=None):
        if db_manager is None:
            self._db_manager = get_db_manager()
        else:
            self._db_manager = db_manager._db_manager if hasattr(db_manager, '_db_manager') else db_manager
        
        self.user_model = _UserModel(self._db_manager)
        self.waste_model = _WasteClassificationModel(self._db_manager)
        self.interaction_model = _UserInteractionModel(self._db_manager)
    
    def update_daily_stats(self, date=None):
        return True
    
    def get_daily_stats(self, date=None):
        return self.interaction_model.get_interaction_stats(days=1)

# Legacy function aliases
init_database = init_models

__all__ = [
    'DatabaseManager',
    'UserModel', 
    'WasteClassificationModel',
    'UserInteractionModel',
    'InteractionModel',
    'StatisticsModel',
    'init_models',
    'init_database',  # Legacy
    'get_db_manager',
    'get_user_model',
    'get_waste_classification_model',
    'get_collection_point_model',
    'get_collection_schedule_model',
    'get_user_interaction_model',
    'get_system_log_model'
]
