"""
Collection Points API Endpoints
Mengelola data titik pengumpulan sampah
"""

import logging
from flask import Blueprint, jsonify
from database.models.base import DatabaseManager
from database.models.collection import CollectionPointModel

# Create blueprint
collection_points_bp = Blueprint('collection_points', __name__, url_prefix='/api')

logger = logging.getLogger(__name__)

@collection_points_bp.route('/collection-points', methods=['GET'])
def get_collection_points():
    """Get all collection points"""
    try:
        db_manager = DatabaseManager()
        collection_model = CollectionPointModel(db_manager)
        
        collection_points = collection_model.get_all_collection_points()
        return jsonify({
            'status': 'success',
            'data': collection_points
        })
    except Exception as e:
        logger.error(f"Error getting collection points: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to get collection points'
        }), 500

@collection_points_bp.route('/collection-points/<point_id>', methods=['GET'])
def get_collection_point(point_id):
    """Get specific collection point by ID"""
    try:
        db_manager = DatabaseManager()
        collection_model = CollectionPointModel(db_manager)
        
        point = collection_model.get_collection_point_by_id(point_id)
        if point:
            return jsonify({
                'status': 'success',
                'data': point
            })
        else:
            return jsonify({
                'status': 'error',
                'message': 'Collection point not found'
            }), 404
    except Exception as e:
        logger.error(f"Error getting collection point: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to get collection point'
        }), 500

@collection_points_bp.route('/collection-points/nearby', methods=['GET'])
def get_nearby_collection_points():
    """Get nearby collection points (future enhancement)"""
    return jsonify({
        'status': 'success',
        'message': 'Nearby search not implemented yet',
        'data': []
    }), 501
