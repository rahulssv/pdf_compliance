"""Swagger UI integration for API documentation and testing"""
from flask import Blueprint
from flask_swagger_ui import get_swaggerui_blueprint

# Swagger UI configuration
SWAGGER_URL = '/api/docs'  # URL for exposing Swagger UI
API_URL = '/static/openapi.yaml'  # URL for OpenAPI spec

# Create Swagger UI blueprint
swagger_bp = get_swaggerui_blueprint(
    SWAGGER_URL,
    API_URL,
    config={
        'app_name': "PDF Accessibility Compliance API",
        'defaultModelsExpandDepth': -1,  # Hide models by default
        'displayRequestDuration': True,  # Show request duration
        'filter': True,  # Enable filtering
        'tryItOutEnabled': True,  # Enable "Try it out" by default
        'persistAuthorization': True,  # Persist authorization data
        'displayOperationId': False,
        'docExpansion': 'list',  # Expand operations list
        'defaultModelExpandDepth': 3,
        'showExtensions': True,
        'showCommonExtensions': True,
    }
)

