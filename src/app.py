"""Main Flask application for PDF Accessibility Compliance Engine"""
import logging
from pathlib import Path

from flask import Flask, jsonify, render_template
from flask_cors import CORS
from src.config import Config
from src.routes.health import health_bp
from src.routes.api_v1 import api_v1_bp
from src.routes.api_v2 import api_v2_bp

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
    
    repo_root = Path(__file__).resolve().parent.parent
    app = Flask(
        __name__,
        template_folder=str(repo_root / "templates"),
        static_folder=str(repo_root / "static"),
    )
    app.config.from_object(Config)
    
    # Enable CORS
    CORS(app)
    logger.info("✅ CORS enabled")
    
    # Register blueprints
    app.register_blueprint(health_bp)
    app.register_blueprint(api_v1_bp, url_prefix=Config.API_PREFIX)
    app.register_blueprint(api_v2_bp, url_prefix=Config.API_V2_PREFIX)
    logger.info(f"✅ Blueprints registered (API prefix: {Config.API_PREFIX})")

    @app.route("/", methods=["GET"])
    def index():
        """Serve basic interactive UI."""
        return render_template("index.html")
    
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
