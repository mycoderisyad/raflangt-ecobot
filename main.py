#!/usr/bin/env python3
"""
EcoBot - Waste Management Assistant
Production-ready WhatsApp bot for waste management education and classification
"""

import os
import sys
import logging
import argparse
from pathlib import Path
from flask import Flask
from dotenv import load_dotenv

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from core.config import init_config, get_config
from core.utils import LoggerUtils


def setup_logging(environment: str = 'development'):
    """Setup environment-aware logging configuration"""
    log_dir = Path(__file__).parent / 'logs'
    log_dir.mkdir(exist_ok=True)
    
    # Production logging: minimal, errors only to file
    if environment == 'production':
        logging.basicConfig(
            level=logging.ERROR,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_dir / 'app.log'),
            ]
        )
        # Disable debug logging for production
        logging.getLogger('werkzeug').setLevel(logging.ERROR)
        logging.getLogger('urllib3').setLevel(logging.ERROR)
    else:
        # Development logging: detailed, includes console output
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_dir / 'app.log'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        # Reduce noise from external libraries
        logging.getLogger('werkzeug').setLevel(logging.WARNING)
        logging.getLogger('urllib3').setLevel(logging.WARNING)


def create_app(environment: str = None) -> Flask:
    """Create Flask application with environment-aware configuration"""
    
    # Load environment configuration
    load_dotenv()
    
    # Setup logging based on environment
    setup_logging(environment)
    
    # Initialize configuration
    config_manager = init_config(environment)
    app_config = config_manager.get_app_config()
    
    # Create Flask app
    app = Flask(__name__)
    app.config['DEBUG'] = app_config.debug
    
    # Register API blueprints
    from api import health_bp, collection_points_bp, users_bp, webhook_bp
    
    app.register_blueprint(health_bp)
    app.register_blueprint(collection_points_bp)
    app.register_blueprint(users_bp)
    app.register_blueprint(webhook_bp)
    
    # Log app creation
    logger = LoggerUtils.get_logger(__name__)
    
    if environment != 'production':
        logger.info(f"Flask app created for {app_config.environment} environment")
    
    return app


def show_startup_info(app_config, port: int):
    """Show application startup information"""
    if app_config.environment == 'development':
        print("=" * 50)
        print("🤖 EcoBot - Waste Management Assistant")
        print("=" * 50)
        print(f"🌍 Environment: {app_config.environment}")
        print(f"🏘️ Village: {app_config.village_name}")
        print(f"🚀 Server: http://localhost:{port}")
        print("-" * 50)
    else:
        # Production: minimal console output
        print(f"EcoBot started - Environment: {app_config.environment} - Port: {port}")


def run_application(environment: str = 'development'):
    """Launch the application"""
    os.environ['ENVIRONMENT'] = environment
    
    # Create and run app
    app = create_app(environment)
    config_manager = get_config()
    app_config = config_manager.get_app_config()
    
    # Set port based on environment variable or environment type
    port = int(os.getenv('PORT', 8000 if environment == 'production' else 5000))
    
    # Show startup info
    show_startup_info(app_config, port)
    
    # Run Flask app
    app.run(
        host='0.0.0.0',
        port=port,
        debug=app_config.debug
    )


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='EcoBot Launcher',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 main.py                    # Development mode (default)
  python3 main.py --production       # Production mode
        """
    )
    
    parser.add_argument(
        '--production',
        action='store_true',
        help='Run in production mode (default: development)'
    )
    
    args = parser.parse_args()
    
    # Load .env first to get default environment
    load_dotenv()
    
    # Override environment if --production flag is used
    if args.production:
        environment = 'production'
        os.environ['ENVIRONMENT'] = 'production'
    else:
        environment = os.getenv('ENVIRONMENT', 'development')
    
    try:
        run_application(environment)
    except KeyboardInterrupt:
        if environment == 'development':
            print("\n👋 EcoBot stopped")
        else:
            print("EcoBot stopped")
    except Exception as e:
        if environment == 'development':
            print(f"❌ Error: {str(e)}")
        else:
            print(f"Error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
