"""Main Flask application for PDF Accessibility Compliance Engine"""
from flask import Flask, jsonify
from flask_cors import CORS
from src.config import Config
from src.routes.health import health_bp
from src.routes.api_v1 import api_v1_bp


def create_app():
    """Application factory pattern"""
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Enable CORS
    CORS(app)
    
    # Register blueprints
    app.register_blueprint(health_bp)
    app.register_blueprint(api_v1_bp, url_prefix=Config.API_PREFIX)
    
    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({"error": "Not found"}), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({"error": "Internal server error"}), 500
    
    return app


# Create the application instance
app = create_app()


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=Config.DEBUG)

# Made with Bob
