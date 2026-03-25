"""Health check endpoint"""
from flask import Blueprint, jsonify

health_bp = Blueprint('health', __name__)


@health_bp.route('/health', methods=['GET'])
def health_check():
    """
    Health check endpoint
    Returns 200 OK with status information
    """
    return jsonify({
        "status": "ok",
        "service": "PDF Accessibility Compliance Engine",
        "version": "1.0.0"
    }), 200

