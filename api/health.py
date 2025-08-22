"""
Health API Endpoints
Health check dan status sistem
"""

import logging
from flask import Blueprint, jsonify
from core.config import get_config

# Create blueprint
health_bp = Blueprint('health', __name__, url_prefix='/')

logger = logging.getLogger(__name__)

@health_bp.route('/', methods=['GET'])
def root():
    """Root endpoint"""
    config_manager = get_config()
    app_config = config_manager.get_app_config()
    
    return jsonify({
        'status': 'healthy',
        'service': app_config.name,
        'version': app_config.version,
        'environment': app_config.environment
    })

@health_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    config_manager = get_config()
    app_config = config_manager.get_app_config()
    
    return jsonify({
        'status': 'healthy',
        'service': app_config.name,
        'version': app_config.version,
        'environment': app_config.environment
    })
