"""
Core Configuration Management
"""

import os
from typing import Dict, Any
from dataclasses import dataclass


@dataclass
class DatabaseConfig:
    path: str
    max_connections: int = 10
    timeout: int = 30


@dataclass
class WhatsAppConfig:
    base_url: str
    api_key: str
    session_name: str
    webhook_url: str


@dataclass
class AIConfig:
    enabled: bool
    api_key: str = None
    base_url: str = None
    text_model: str = None
    vision_model: str = None


@dataclass
class EmailConfig:
    api_key: str
    base_url: str
    from_email: str
    to_email: str


@dataclass
class MapsConfig:
    api_key: str
    enabled: bool = True


@dataclass
class AppConfig:
    name: str
    version: str
    debug: bool
    environment: str
    village_name: str
    village_coordinates: str
    admin_phones: list
    coordinator_phones: list


class ConfigManager:
    """Centralized configuration management"""
    
    def __init__(self, environment: str = None):
        self.environment = environment or os.getenv('ENVIRONMENT', 'development')
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration based on environment"""
        
        # Base configuration
        config = {
            'database': DatabaseConfig(
                path=os.getenv('DATABASE_PATH', 'database/ecobot.db')
            ),
            'whatsapp': WhatsAppConfig(
                base_url=os.getenv('WAHA_BASE_URL', 'https://waha.rafgt.my.id/api'),
                api_key=os.getenv('WAHA_API_KEY', ''),
                session_name=os.getenv('WAHA_SESSION_NAME', 'default'),
                webhook_url=os.getenv('WEBHOOK_URL', 'http://localhost:5001/webhook')
            ),
            'ai': AIConfig(
                enabled=os.getenv('AI_ENABLED', 'true' if self.environment == 'production' else 'false').lower() == 'true',
                api_key=os.getenv('LUNOS_API_KEY'),
                base_url=os.getenv('LUNOS_BASE_URL'),
                text_model=os.getenv('LUNOS_TEXT_MODEL'),
                vision_model=os.getenv('LUNOS_VISION_MODEL')
            ),
            'email': EmailConfig(
                api_key=os.getenv('MAILRY_API_KEY', ''),
                base_url=os.getenv('MAILRY_BASE_URL', ''),
                from_email=os.getenv('MAILRY_FROM_EMAIL', ''),
                to_email=os.getenv('MAILRY_TO_EMAIL', '')
            ),
            'maps': MapsConfig(
                api_key=os.getenv('GOOGLE_MAPS_API_KEY', ''),
                enabled=os.getenv('MAPS_ENABLED', 'true' if self.environment == 'production' else 'false').lower() == 'true'
            ),
            'app': AppConfig(
                name=os.getenv('APP_NAME', 'EcoBot'),
                version=os.getenv('APP_VERSION', '1.0.0'),
                debug=os.getenv('DEBUG', 'true' if self.environment == 'development' else 'false').lower() == 'true',
                environment=self.environment,
                village_name=os.getenv('VILLAGE_NAME', 'Desa Cukangkawung'),
                village_coordinates=os.getenv('VILLAGE_COORDINATES', '-6.2088,106.8456'),
                admin_phones=self._parse_phones(os.getenv('ADMIN_PHONE_NUMBERS', '')),
                coordinator_phones=self._parse_phones(os.getenv('COORDINATOR_PHONE_NUMBERS', ''))
            )
        }
        
        return config
    
    def _parse_phones(self, phone_string: str) -> list:
        """Parse phone numbers from comma-separated string"""
        if not phone_string:
            return []
        return [phone.strip() for phone in phone_string.split(',') if phone.strip()]
    
    def get(self, key: str) -> Any:
        """Get configuration value by key"""
        return self.config.get(key)
    
    def get_database_config(self) -> DatabaseConfig:
        return self.config['database']
    
    def get_whatsapp_config(self) -> WhatsAppConfig:
        return self.config['whatsapp']
    
    def get_ai_config(self) -> AIConfig:
        return self.config['ai']
    
    def get_email_config(self) -> EmailConfig:
        return self.config['email']
    
    def get_maps_config(self) -> MapsConfig:
        return self.config['maps']
    
    def get_app_config(self) -> AppConfig:
        return self.config['app']


# Global config instance
config_manager = None


def init_config(environment: str = None) -> ConfigManager:
    """Initialize global configuration"""
    global config_manager
    config_manager = ConfigManager(environment)
    return config_manager


def get_config() -> ConfigManager:
    """Get global configuration instance"""
    global config_manager
    if not config_manager:
        config_manager = ConfigManager()
    return config_manager
