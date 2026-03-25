"""Main Flask application for PDF Accessibility Compliance Engine"""
import logging
from flask import Flask, jsonify
from flask_cors import CORS
from src.config import Config
from src.routes.health import health_bp
from src.routes.api_v1 import api_v1_bp

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


def create_app():
    """Application factory pattern"""
    logger.info("🚀 Initializing PDF Accessibility Compliance Engine...")
    
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Enable CORS
    CORS(app)
    logger.info("✅ CORS enabled")
    
    # Register blueprints
    app.register_blueprint(health_bp)
    app.register_blueprint(api_v1_bp, url_prefix=Config.API_PREFIX)
    logger.info(f"✅ Blueprints registered (API prefix: {Config.API_PREFIX})")
    
    # Log Gemini status
    if Config.GEMINI_API_KEY:
        logger.info(f"✅ Gemini API key configured (model: {Config.GEMINI_MODEL})")
    else:
        logger.warning("⚠️ Gemini API key not configured - using fallback responses")
    
    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        logger.warning(f"404 Not Found: {error}")
        return jsonify({"error": "Not found"}), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        logger.error(f"500 Internal Error: {error}")
        return jsonify({"error": "Internal server error"}), 500
    
    logger.info("✅ Application initialized successfully")
    return app


# Create the application instance
app = create_app()


if __name__ == '__main__':
    logger.info("🌐 Starting Flask development server on 0.0.0.0:8000")
    app.run(host='0.0.0.0', port=8000, debug=Config.DEBUG)

