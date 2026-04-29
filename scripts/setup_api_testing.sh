#!/bin/bash
# Setup script for API testing tools

echo "🚀 Setting up API testing environment..."

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip install flask-swagger-ui==4.11.1 flasgger==0.9.7.1 pytest-html==3.2.0

# Create static directory for OpenAPI spec
echo "📁 Creating static directory..."
mkdir -p static

# Copy OpenAPI spec to static folder
if [ -f "docs/openapi.yaml" ]; then
    echo "📄 Copying OpenAPI spec..."
    cp docs/openapi.yaml static/
else
    echo "⚠️  OpenAPI spec not found at docs/openapi.yaml"
    echo "   You'll need to create it manually or extract from the guide"
fi

# Update requirements.txt
echo "📝 Updating requirements.txt..."
if ! grep -q "flask-swagger-ui" requirements.txt; then
    echo "flask-swagger-ui==4.11.1" >> requirements.txt
fi
if ! grep -q "flasgger" requirements.txt; then
    echo "flasgger==0.9.7.1" >> requirements.txt
fi
if ! grep -q "pytest-html" requirements.txt; then
    echo "pytest-html==3.2.0" >> requirements.txt
fi

echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Update src/app.py to register Swagger blueprint"
echo "2. Start your application: docker-compose up --build"
echo "3. Access Swagger UI at: http://localhost:8000/api/docs"
echo "4. Run tests: pytest tests/test_api_comprehensive.py -v"

