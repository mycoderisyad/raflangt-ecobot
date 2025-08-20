#!/usr/bin/env python3
"""
EcoBot Startup Script
"""

import os
import sys

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ecobot.main import main
from config.settings import get_config, setup_logging

def check_environment():
    """Check if environment is properly configured"""
    print("Checking environment...")
    
    # Check if .env file exists
    env_file = '.env'
    if not os.path.exists(env_file):
        print(f"Warning: {env_file} file not found")
        print("Please copy .env.example to .env and configure your API keys")
        return False
    
    # Check database (not required anymore - auto-initialized)
    print("Database will be auto-initialized if needed")
    
    print("Environment check passed")
    return True

def start_ecobot():
    """Start EcoBot application"""
    try:
        # Get configuration
        config = get_config()
        
        # Setup logging
        setup_logging(config)
        
        # Check environment
        if not check_environment():
            print("\nEnvironment check failed. Please fix issues above.")
            return 1
        
        # Validate configuration
        required_settings, warnings = config.validate_required_settings()
        
        if required_settings:
            print(f"\nMissing required settings: {', '.join(required_settings)}")
            print("Please configure these in your .env file")
            return 1
        
        if warnings:
            print(f"\nWarnings:")
            for warning in warnings:
                print(f"  - {warning}")
            print()
        
        print("Starting EcoBot...")
        print("Press Ctrl+C to stop")
        print("-" * 50)
        
        # Start the application
        main()
        
    except KeyboardInterrupt:
        print("\nEcoBot stopped by user")
        return 0
    except Exception as e:
        print(f"\nFailed to start EcoBot: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(start_ecobot())
