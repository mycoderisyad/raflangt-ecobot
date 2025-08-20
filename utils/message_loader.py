"""
Message loader utility
Load messages and templates from JSON files
"""

import json
import os
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class MessageLoader:
    """Load and manage messages from JSON files"""
    
    def __init__(self):
        self.data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
        self._cache = {}
    
    def load_json(self, filename: str) -> Dict[str, Any]:
        """Load JSON file with caching"""
        if filename in self._cache:
            return self._cache[filename]
        
        file_path = os.path.join(self.data_dir, filename)
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self._cache[filename] = data
                return data
        except FileNotFoundError:
            logger.error(f"Message file not found: {file_path}")
            return {}
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in {file_path}: {str(e)}")
            return {}
    
    def get_education_messages(self) -> Dict[str, Any]:
        """Load education messages"""
        return self.load_json('education_messages.json')
    
    def get_whatsapp_messages(self) -> Dict[str, Any]:
        """Load WhatsApp messages"""
        return self.load_json('whatsapp_messages.json')
    
    def get_maps_data(self) -> Dict[str, Any]:
        """Load maps data"""
        return self.load_json('maps_data.json')
    
    def get_email_templates(self) -> Dict[str, Any]:
        """Load email templates"""
        return self.load_json('email_templates.json')
    
    def clear_cache(self):
        """Clear message cache"""
        self._cache.clear()
        logger.info("Message cache cleared")

# Global instance
message_loader = MessageLoader()
