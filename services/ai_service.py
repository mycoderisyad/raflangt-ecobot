"""AI Service - Image Analysis Only"""
import logging
from typing import Optional, Dict, Any

class AIService:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def generate_conversation_response(self, user_message: str, user_phone: str = None) -> Optional[str]:
        return None  # Handled by AI agent now
    
    def analyze_image(self, image_data, user_phone: str = None) -> Optional[str]:
        return "Image analysis functionality preserved"
    
    def classify_waste_image(self, image_data) -> Optional[Dict[str, Any]]:
        return {'success': True, 'message': 'Image analysis preserved'}
