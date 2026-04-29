# Quick Start: API Testing Setup

## 🚀 Get Started in 5 Minutes

### Step 1: Install Dependencies
```bash
pip install flask-swagger-ui flasgger pytest-html
```

### Step 2: Update app.py

Add these lines to [`src/app.py`](src/app.py) after the existing blueprint imports:

```python
# Add this import at the top with other route imports
from src.routes.swagger import swagger_bp

# Add this after other blueprint registrations (around line 49)
app.register_blueprint(swagger_bp, url_prefix='/api/docs')
logger.info("✅ Swagger UI available at /api/docs")
```

### Step 3: Start Your Application
```bash
docker-compose up --build -d
```

### Step 4: Access Swagger UI
Open your browser to:
```
http://localhost:8000/api/docs
```

### Step 5: Run Tests
```bash
# Run all tests
pytest tests/test_api_comprehensive.py -v

# Run specific test suite
./scripts/run_api_tests.sh v1      # Test v1 endpoints only
./scripts/run_api_tests.sh v2      # Test v2 endpoints only
./scripts/run_api_tests.sh report  # Generate HTML report
```

---

## 📊 Testing Options

### Quick Health Check
```bash
curl http://localhost:8000/health
```

### Test Specific Endpoint
```bash
# Test v1 scan
curl -X POST http://localhost:8000/api/v1/scan \
  -H "Content-Type: application/json" \
  -d '{"fileUrls": ["docs/fixtures/accessible_guide.pdf"]}'

# Test v2 analyze
curl -X POST http://localhost:8000/api/v2/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "fileUrl": "docs/fixtures/accessible_guide.pdf",
    "options": {"detectPII": false}
  }'
```

### Run Test Suites
```bash
# All tests
./scripts/run_api_tests.sh

# Quick tests (health + v1)
./scripts/run_api_tests.sh quick

# API v1 only
./scripts/run_api_tests.sh v1

# API v2 only
./scripts/run_api_tests.sh v2

# Compare v1 vs v2
./scripts/run_api_tests.sh comparison

# Performance tests
./scripts/run_api_tests.sh performance

# Generate HTML report
./scripts/run_api_tests.sh report
```

---

## 📝 What You Get

### 1. **Swagger UI** (Interactive API Documentation)
- **URL**: http://localhost:8000/api/docs
- **Features**:
  - Test all endpoints directly in browser
  - View request/response schemas
  - Try different parameters
  - See example responses
  - Export API spec

### 2. **Comprehensive Test Suite** (500+ test cases)
- **Location**: [`tests/test_api_comprehensive.py`](tests/test_api_comprehensive.py)
- **Coverage**:
  - ✅ All v1 endpoints (3 endpoints)
  - ✅ All v2 endpoints (17 endpoints)
  - ✅ Error handling
  - ✅ Input validation
  - ✅ Response validation
  - ✅ Performance tests
  - ✅ v1 vs v2 comparison

### 3. **Test Reports**
```bash
# Generate HTML report
pytest tests/test_api_comprehensive.py --html=report.html --self-contained-html

# Generate coverage report
pytest tests/test_api_comprehensive.py --cov=src --cov-report=html

# View reports
open report.html
open htmlcov/index.html
```

---

## 🎯 API Endpoints Overview

### API v1 (Legacy)
| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/api/v1/scan` | Scan PDFs for issues |
| POST | `/api/v1/remediate` | Get remediation guidance |
| POST | `/api/v1/dashboard` | Generate dashboard |

### API v2 (Current)
| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/api/v2/analyze` | Analyze document |
| POST | `/api/v2/analyze/upload` | Analyze uploaded file |
| POST | `/api/v2/analyze/batch` | Batch analysis |
| POST | `/api/v2/pii/detect` | Detect PII |
| POST | `/api/v2/pages/analyze` | Analyze page range |
| POST | `/api/v2/scan/page/<n>` | Scan single page |
| POST | `/api/v2/pages/extract` | Extract page content |
| POST | `/api/v2/pages/summary` | Get pages summary |
| POST | `/api/v2/remediate/auto` | Auto-remediate |
| POST | `/api/v2/remediate/auto/download` | Download remediated PDF |
| POST | `/api/v2/remediate/guidance` | Get guidance |
| POST | `/api/v2/reports/generate` | Generate report |
| POST | `/api/v2/validation/check` | Validate AI output |
| GET | `/api/v2/prompts/performance` | Get prompt metrics |

---

## 🔧 Troubleshooting

### Application Not Running
```bash
# Check if running
curl http://localhost:8000/health

# Start application
docker-compose up -d

# Check logs
docker-compose logs -f
```

### Tests Failing
```bash
# Check test file paths
ls -la docs/fixtures/

# Run single test for debugging
pytest tests/test_api_comprehensive.py::TestHealth::test_health_check -v

# Run with verbose output
pytest tests/test_api_comprehensive.py -vv
```

### Swagger UI Not Loading
1. Ensure [`src/routes/swagger.py`](src/routes/swagger.py) exists
2. Check that swagger blueprint is registered in [`src/app.py`](src/app.py)
3. Verify `static/openapi.yaml` exists
4. Restart application

---

## 📚 Additional Resources

- **Comprehensive Guide**: [`docs/API_TESTING_COMPREHENSIVE_GUIDE.md`](docs/API_TESTING_COMPREHENSIVE_GUIDE.md)
- **API v2 Specification**: [`docs/API_V2_SPECIFICATION.md`](docs/API_V2_SPECIFICATION.md)
- **Testing Guide**: [`docs/TESTING_GUIDE.md`](docs/TESTING_GUIDE.md)

---

## 🎓 Next Steps

1. **Explore Swagger UI**: Test endpoints interactively
2. **Run Test Suite**: Validate all endpoints
3. **Generate Reports**: Create test and coverage reports
4. **Set Up CI/CD**: Integrate tests into your pipeline
5. **Create Custom Tests**: Add project-specific test cases

---

## 💡 Pro Tips

### Test Specific Scenarios
```python
# Add custom test to tests/test_api_comprehensive.py
def test_my_custom_scenario():
    response = requests.post(
        f"{BASE_URL}/api/v2/analyze",
        json={"fileUrl": "my_test.pdf", "options": {}}
    )
    assert response.status_code == 200
```

### Use Environment Variables
```bash
# Set custom base URL
export API_BASE_URL=https://staging.example.com
pytest tests/test_api_comprehensive.py -v
```

### Parallel Testing
```bash
# Install pytest-xdist
pip install pytest-xdist

# Run tests in parallel
pytest tests/test_api_comprehensive.py -n 4
```

### Watch Mode
```bash
# Install pytest-watch
pip install pytest-watch

# Auto-run tests on file changes
ptw tests/test_api_comprehensive.py
```

---

## ✅ Success Checklist

- [ ] Dependencies installed
- [ ] Swagger blueprint registered in app.py
- [ ] Application running on port 8000
- [ ] Swagger UI accessible at /api/docs
- [ ] Health check passing
- [ ] Test suite running successfully
- [ ] Reports generated

**You're all set! Happy testing! 🎉**