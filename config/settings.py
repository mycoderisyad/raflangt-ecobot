"""
Application configuration settings
"""

import os
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Base configuration class"""
    
    # Flask settings
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    FLASK_ENV = os.getenv('FLASK_ENV', 'development')
    DEBUG = False  # Disable debug mode to prevent auto-restart
    
    # Application settings
    APP_NAME = os.getenv('APP_NAME', 'EcoBot')
    APP_VERSION = os.getenv('APP_VERSION', '1.0.0')
    
    # Twilio WhatsApp settings
    TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID')
    TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN')
    TWILIO_WHATSAPP_NUMBER = os.getenv('TWILIO_WHATSAPP_NUMBER')
    
    # Lunos AI API settings (fixed typo)
    LUNOS_API_KEY = os.getenv('LUNOS_API_KEY')
    LUNOS_BASE_URL = os.getenv('LUNOS_BASE_URL', 'https://api.lunos.tech/v1')
    LUNOS_TEXT_MODEL = os.getenv('LUNOS_TEXT_MODEL', 'openai/gpt-4o-mini')
    LUNOS_VISION_MODEL = os.getenv('LUNOS_VISION_MODEL', 'openai/gpt-4o')
    
    # Google Maps settings
    GOOGLE_MAPS_API_KEY = os.getenv('GOOGLE_MAPS_API_KEY')
    
    # Mailry email settings
    MAILRY_API_KEY = os.getenv('MAILRY_API_KEY')
    MAILRY_FROM_EMAIL = os.getenv('MAILRY_FROM_EMAIL', 'noreply@ecobot.id')
    MAILRY_TO_EMAIL = os.getenv('MAILRY_TO_EMAIL', 'admin@desacukangkawung.go.id')
    
    # Database settings
    DATABASE_PATH = os.getenv('DATABASE_PATH', 'database/ecobot.db')
    
    # Village settings
    VILLAGE_NAME = os.getenv('VILLAGE_NAME', 'Desa Cukangkawung')
    VILLAGE_COORDINATES = os.getenv('VILLAGE_COORDINATES', '-6.2088,106.8456')
    
    # File upload settings
    MAX_IMAGE_SIZE_MB = int(os.getenv('MAX_IMAGE_SIZE_MB', 5))
    SUPPORTED_IMAGE_FORMATS = os.getenv('SUPPORTED_IMAGE_FORMATS', 'jpg,jpeg,png,gif').split(',')
    
    # Logging settings
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE = os.getenv('LOG_FILE', 'logs/ecobot.log')
    
    @classmethod
    def validate_required_settings(cls):
        """Validate that required settings are present"""
        required_settings = []
        warnings = []
        
        # Check Twilio settings
        if not cls.TWILIO_ACCOUNT_SID:
            required_settings.append('TWILIO_ACCOUNT_SID')
        if not cls.TWILIO_AUTH_TOKEN:
            required_settings.append('TWILIO_AUTH_TOKEN')
        if not cls.TWILIO_WHATSAPP_NUMBER:
            required_settings.append('TWILIO_WHATSAPP_NUMBER')
        
        # Optional but recommended settings
        if not cls.LUNOS_API_KEY:
            warnings.append('LUNOS_API_KEY not set - using mock AI classification')
        if not cls.GOOGLE_MAPS_API_KEY:
            warnings.append('GOOGLE_MAPS_API_KEY not set - using mock maps')
        if not cls.MAILRY_API_KEY:
            warnings.append('MAILRY_API_KEY not set - using mock email service')
        
        return required_settings, warnings
    
    @classmethod
    def get_config_summary(cls):
        """Get configuration summary for logging"""
        return {
            'app_name': cls.APP_NAME,
            'app_version': cls.APP_VERSION,
            'environment': cls.FLASK_ENV,
            'debug': cls.DEBUG,
            'village_name': cls.VILLAGE_NAME,
            'database_path': cls.DATABASE_PATH,
            'twilio_configured': bool(cls.TWILIO_ACCOUNT_SID),
            'lunos_configured': bool(cls.LUNOS_API_KEY),
            'google_maps_configured': bool(cls.GOOGLE_MAPS_API_KEY),
            'mailry_configured': bool(cls.MAILRY_API_KEY)
        }

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    FLASK_ENV = 'development'

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    FLASK_ENV = 'production'
    
    # Override with more secure defaults for production
    @classmethod
    def validate_production_settings(cls):
        """Additional validation for production"""
        issues = []
        
        if cls.SECRET_KEY == 'dev-secret-key-change-in-production':
            issues.append('SECRET_KEY must be changed for production')
        
        if cls.DEBUG:
            issues.append('DEBUG should be False in production')
        
        return issues

class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    DATABASE_PATH = ':memory:'  # Use in-memory database for tests

# Configuration mapping
config_map = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}

def get_config(config_name=None):
    """Get configuration class based on environment"""
    if config_name is None:
        config_name = os.getenv('FLASK_ENV', 'development')
    
    return config_map.get(config_name, config_map['default'])

def setup_logging(config_class):
    """Setup application logging"""
    # Create logs directory if it doesn't exist
    log_file = config_class.LOG_FILE
    log_dir = os.path.dirname(log_file)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir, exist_ok=True)
    
    # Configure logging
    log_level = getattr(logging, config_class.LOG_LEVEL.upper(), logging.INFO)
    
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    
    # Reduce noise from external libraries
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('requests').setLevel(logging.WARNING)
    
    logger = logging.getLogger(__name__)
    logger.info(f"Logging configured - Level: {config_class.LOG_LEVEL}, File: {log_file}")

# Export current configuration
current_config = get_config()
