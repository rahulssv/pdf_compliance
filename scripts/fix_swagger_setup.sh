#!/bin/bash
# Fix Swagger UI setup and restart application

echo "🔧 Fixing Swagger UI setup..."
echo ""

# Step 1: Install dependencies
echo "📦 Installing required dependencies..."
pip install flask-swagger-ui==4.11.1 flasgger==0.9.7.1 pytest-html==3.2.0

# Step 2: Verify files exist
echo ""
echo "✅ Verifying setup files..."

if [ -f "src/routes/swagger.py" ]; then
    echo "  ✓ src/routes/swagger.py exists"
else
    echo "  ✗ src/routes/swagger.py missing!"
    exit 1
fi

if [ -f "static/openapi.yaml" ]; then
    echo "  ✓ static/openapi.yaml exists"
else
    echo "  ✗ static/openapi.yaml missing!"
    exit 1
fi

if grep -q "from src.routes.swagger import swagger_bp" src/app.py; then
    echo "  ✓ Swagger blueprint imported in app.py"
else
    echo "  ✗ Swagger blueprint not imported in app.py!"
    exit 1
fi

if grep -q "app.register_blueprint(swagger_bp" src/app.py; then
    echo "  ✓ Swagger blueprint registered in app.py"
else
    echo "  ✗ Swagger blueprint not registered in app.py!"
    exit 1
fi

# Step 3: Restart application with rebuild
echo ""
echo "🔄 Rebuilding and restarting application..."
echo "  (This is necessary to copy the static folder into the container)"

if command -v docker-compose &> /dev/null; then
    echo "  Using docker-compose..."
    docker-compose down
    echo "  Building new image with static files..."
    docker-compose build --no-cache
    echo "  Starting containers..."
    docker-compose up -d
    
    echo ""
    echo "⏳ Waiting for application to start..."
    sleep 5
    
    # Check if application is running
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        echo "  ✓ Application is running"
    else
        echo "  ✗ Application failed to start"
        echo ""
        echo "Check logs with: docker-compose logs -f"
        exit 1
    fi
else
    echo "  Docker Compose not found. Please restart manually:"
    echo "    python src/app.py"
fi

# Step 4: Test Swagger UI
echo ""
echo "🧪 Testing Swagger UI endpoint..."
sleep 2

response=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/api/docs/)
if [ "$response" = "200" ]; then
    echo "  ✓ Swagger UI is accessible!"
else
    echo "  ✗ Swagger UI returned HTTP $response"
    echo ""
    echo "Troubleshooting:"
    echo "  1. Check application logs: docker-compose logs -f"
    echo "  2. Verify static folder exists: ls -la static/"
    echo "  3. Check Flask static folder config in src/app.py"
fi

echo ""
echo "✅ Setup complete!"
echo ""
echo "📍 Access Swagger UI at: http://localhost:8000/api/docs"
echo "📍 Health check: http://localhost:8000/health"
echo ""
echo "If you still see 404 errors:"
echo "  1. Check logs: docker-compose logs -f"
echo "  2. Verify imports: grep -n swagger src/app.py"
echo "  3. Test static files: curl http://localhost:8000/static/openapi.yaml"

