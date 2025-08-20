"""
EcoBot Main Application
Entry point untuk aplikasi EcoBot
"""

import os
import logging
from flask import Flask, request
from dotenv import load_dotenv

from .whatsapp_handler import WhatsAppHandler
from .ai_classifier import AIClassifier
from .education_module import EducationModule
from .maps_integration import MapsIntegration
from .email_notifications import EmailNotifications
from database.models import init_models

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class EcoBot:
    """Main EcoBot application class"""
    
    def __init__(self):
        self.app = Flask(__name__)
        self.app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key')
        
        # Initialize database first
        init_models()
        
        # Initialize components
        self.whatsapp_handler = WhatsAppHandler()
        self.ai_classifier = AIClassifier()
        self.education_module = EducationModule()
        self.maps_integration = MapsIntegration()
        self.email_notifications = EmailNotifications()
        
        # Setup routes
        self.setup_routes()
        
        logger.info("EcoBot initialized successfully")
    
    def setup_routes(self):
        """Setup Flask routes"""
        
        @self.app.route('/')
        def home():
            return {
                "message": "EcoBot is running!",
                "version": "1.0.0",
                "status": "active"
            }
        
        @self.app.route('/webhook', methods=['POST'])
        def webhook():
            """WhatsApp webhook endpoint"""
            try:
                # Process incoming WhatsApp message
                return self.whatsapp_handler.handle_incoming_message(request)
            except Exception as e:
                logger.error(f"Error processing webhook: {str(e)}")
                return {"error": "Internal server error"}, 500
        
        @self.app.route('/health', methods=['GET'])
        def health_check():
            """Health check endpoint"""
            return {
                "status": "healthy",
                "timestamp": str(os.getenv('TIMESTAMP', 'unknown')),
                "components": {
                    "whatsapp": "active",
                    "ai_classifier": "active",
                    "database": "active",
                    "maps": "active",
                    "email": "active"
                }
            }
    
    def run(self, debug=True, port=5000):
        """Run the Flask application"""
        logger.info(f"Starting EcoBot on port {port}")
        self.app.run(debug=debug, port=port, host='0.0.0.0')

def main():
    """Main function to start the application"""
    try:
        # Create and run EcoBot
        ecobot = EcoBot()
        
        # Get configuration from environment
        debug_mode = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
        port = int(os.getenv('PORT', 5001))
        
        print(f"EcoBot - AI-Powered Waste Management Assistant")
        print("=" * 50)
        print(f"Starting server on port {port}")
        print(f"Debug mode: {debug_mode}")
        print(f"Village: {os.getenv('VILLAGE_NAME')}")
        print("=" * 50)
        
        # Run the application
        ecobot.run(debug=debug_mode, port=port)
        
    except KeyboardInterrupt:
        print("\nEcoBot shutting down gracefully...")
    except Exception as e:
        logger.error(f"Failed to start EcoBot: {str(e)}")
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    main()
