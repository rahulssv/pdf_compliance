#!/bin/bash
# Script to run comprehensive API tests

echo "🧪 Running API Tests..."
echo ""

# Check if application is running
echo "🔍 Checking if application is running..."
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ Application is running"
else
    echo "❌ Application is not running!"
    echo "   Start it with: docker-compose up -d"
    exit 1
fi

# Run tests with different options based on arguments
case "$1" in
    "quick")
        echo "🏃 Running quick tests (health + v1 only)..."
        pytest tests/test_api_comprehensive.py::TestHealth -v
        pytest tests/test_api_comprehensive.py::TestAPIv1 -v
        ;;
    "v1")
        echo "📋 Running API v1 tests..."
        pytest tests/test_api_comprehensive.py::TestAPIv1 -v
        ;;
    "v2")
        echo "📋 Running API v2 tests..."
        pytest tests/test_api_comprehensive.py::TestAPIv2Analysis -v
        pytest tests/test_api_comprehensive.py::TestAPIv2PII -v
        pytest tests/test_api_comprehensive.py::TestAPIv2Pages -v
        pytest tests/test_api_comprehensive.py::TestAPIv2Remediation -v
        pytest tests/test_api_comprehensive.py::TestAPIv2Reports -v
        pytest tests/test_api_comprehensive.py::TestAPIv2Validation -v
        ;;
    "comparison")
        echo "🔄 Running v1 vs v2 comparison tests..."
        pytest tests/test_api_comprehensive.py::TestAPIComparison -v
        ;;
    "performance")
        echo "⚡ Running performance tests..."
        pytest tests/test_api_comprehensive.py::TestPerformance -v
        ;;
    "report")
        echo "📊 Running all tests with HTML report..."
        pytest tests/test_api_comprehensive.py -v \
            --html=test_report.html \
            --self-contained-html \
            --cov=src \
            --cov-report=html
        echo ""
        echo "✅ Reports generated:"
        echo "   - Test report: test_report.html"
        echo "   - Coverage report: htmlcov/index.html"
        ;;
    "coverage")
        echo "📊 Running tests with coverage..."
        pytest tests/test_api_comprehensive.py -v \
            --cov=src \
            --cov-report=term-missing \
            --cov-report=html
        ;;
    *)
        echo "🧪 Running all tests..."
        pytest tests/test_api_comprehensive.py -v
        ;;
esac

echo ""
echo "✅ Tests complete!"

