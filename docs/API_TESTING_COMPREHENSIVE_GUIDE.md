# Comprehensive API Testing Guide

## Table of Contents
1. [Overview](#overview)
2. [Testing Tools Comparison](#testing-tools-comparison)
3. [Recommended Approach: Swagger/OpenAPI](#recommended-approach-swaggeropenapi)
4. [Alternative: Postman](#alternative-postman)
5. [Alternative: pytest + requests](#alternative-pytest--requests)
6. [Setting Up Swagger UI](#setting-up-swagger-ui)
7. [API Endpoint Inventory](#api-endpoint-inventory)
8. [Test Scenarios by Endpoint](#test-scenarios-by-endpoint)
9. [Authentication & Environment Management](#authentication--environment-management)
10. [Best Practices](#best-practices)
11. [CI/CD Integration](#cicd-integration)

---

## Overview

Your application has **two API versions** with distinct endpoints:
- **API v1** (`/api/v1`): 3 endpoints (scan, remediate, dashboard)
- **API v2** (`/api/v2`): 15+ endpoints with advanced features

**Testing Goals:**
- Validate all HTTP methods (GET, POST)
- Test request/response schemas
- Verify error handling
- Compare v1 vs v2 behavior
- Performance testing
- Generate comprehensive reports

---

## Testing Tools Comparison

| Tool | Pros | Cons | Best For |
|------|------|------|----------|
| **Swagger/OpenAPI** | Auto-generated docs, interactive testing, schema validation | Requires OpenAPI spec | API documentation + testing |
| **Postman** | User-friendly, collections, environments, CI/CD | Desktop app, learning curve | Manual + automated testing |
| **pytest + requests** | Code-based, version control, CI/CD native | Requires coding | Automated regression testing |
| **Thunder Client** | VSCode extension, lightweight | Limited features | Quick ad-hoc testing |
| **Bruno** | Git-friendly, open source | Newer tool | Team collaboration |

**Recommendation:** Use **Swagger UI + pytest** combination for comprehensive coverage.

---

## Recommended Approach: Swagger/OpenAPI

### Why Swagger?
1. **Interactive Documentation**: Test endpoints directly in browser
2. **Schema Validation**: Automatic request/response validation
3. **Version Comparison**: Side-by-side v1 vs v2 testing
4. **No Additional Setup**: Runs within your Flask app
5. **Standards-Based**: OpenAPI 3.0 specification

---

## Setting Up Swagger UI

### Step 1: Install Dependencies

```bash
pip install flask-swagger-ui flasgger
```

Add to `requirements.txt`:
```
flask-swagger-ui==4.11.1
flasgger==0.9.7.1
```

### Step 2: Create OpenAPI Specification

Create `docs/openapi.yaml`:

```yaml
openapi: 3.0.0
info:
  title: PDF Accessibility Compliance API
  description: Comprehensive API for PDF accessibility analysis and remediation
  version: 2.0.0
  contact:
    name: API Support
    email: support@example.com

servers:
  - url: http://localhost:8000
    description: Local development
  - url: https://api.production.com
    description: Production

tags:
  - name: Health
    description: Health check endpoints
  - name: API v1
    description: Legacy API endpoints
  - name: API v2 - Analysis
    description: Document analysis endpoints
  - name: API v2 - PII
    description: PII detection endpoints
  - name: API v2 - Pages
    description: Page-level operations
  - name: API v2 - Remediation
    description: Auto-remediation endpoints
  - name: API v2 - Reports
    description: Report generation
  - name: API v2 - Validation
    description: AI validation endpoints

paths:
  /health:
    get:
      tags:
        - Health
      summary: Health check
      responses:
        '200':
          description: Service is healthy
          content:
            application/json:
              schema:
                type: object
                properties:
                  status:
                    type: string
                    example: healthy

  # API v1 Endpoints
  /api/v1/scan:
    post:
      tags:
        - API v1
      summary: Scan PDF files for accessibility issues
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              required:
                - fileUrls
              properties:
                fileUrls:
                  type: array
                  items:
                    type: string
                  example: ["/path/to/file.pdf"]
      responses:
        '200':
          description: Scan completed successfully
        '400':
          description: Invalid request
        '500':
          description: Server error

  /api/v1/remediate:
    post:
      tags:
        - API v1
      summary: Provide remediation guidance
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              required:
                - fileUrls
              properties:
                fileUrls:
                  type: array
                  items:
                    type: string
      responses:
        '200':
          description: Remediation guidance provided

  /api/v1/dashboard:
    post:
      tags:
        - API v1
      summary: Generate compliance dashboard
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              required:
                - fileUrls
              properties:
                fileUrls:
                  type: array
                  items:
                    type: string
      responses:
        '200':
          description: Dashboard generated

  # API v2 Endpoints
  /api/v2/analyze:
    post:
      tags:
        - API v2 - Analysis
      summary: Analyze PDF document
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              required:
                - fileUrl
              properties:
                fileUrl:
                  type: string
                  example: "/path/to/document.pdf"
                options:
                  type: object
                  properties:
                    detectPII:
                      type: boolean
                      default: false
                    piiSensitivity:
                      type: string
                      enum: [low, medium, high]
                      default: medium
                    pageLevel:
                      type: boolean
                      default: false
                    autoRemediate:
                      type: boolean
                      default: false
                    validateAI:
                      type: boolean
                      default: true
                    requireGeminiRemediation:
                      type: boolean
                      default: false
      responses:
        '200':
          description: Analysis completed
          content:
            application/json:
              schema:
                type: object
                properties:
                  success:
                    type: boolean
                  complianceScore:
                    type: number
                  issues:
                    type: array
                  recommendations:
                    type: array

  /api/v2/analyze/upload:
    post:
      tags:
        - API v2 - Analysis
      summary: Analyze uploaded PDF
      requestBody:
        required: true
        content:
          multipart/form-data:
            schema:
              type: object
              required:
                - file
              properties:
                file:
                  type: string
                  format: binary
                options:
                  type: string
                  description: JSON string of options
      responses:
        '200':
          description: Analysis completed

  /api/v2/analyze/batch:
    post:
      tags:
        - API v2 - Analysis
      summary: Batch analyze multiple PDFs
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              required:
                - fileUrls
              properties:
                fileUrls:
                  type: array
                  items:
                    type: string
                options:
                  type: object
      responses:
        '200':
          description: Batch analysis completed

  /api/v2/pii/detect:
    post:
      tags:
        - API v2 - PII
      summary: Detect PII in document
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              required:
                - fileUrl
              properties:
                fileUrl:
                  type: string
                sensitivity:
                  type: string
                  enum: [low, medium, high]
                redact:
                  type: boolean
      responses:
        '200':
          description: PII detection completed

  /api/v2/pages/analyze:
    post:
      tags:
        - API v2 - Pages
      summary: Analyze specific pages
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              required:
                - fileUrl
              properties:
                fileUrl:
                  type: string
                pageRange:
                  type: object
                  properties:
                    start:
                      type: integer
                    end:
                      type: integer
      responses:
        '200':
          description: Page analysis completed

  /api/v2/scan/page/{page_number}:
    post:
      tags:
        - API v2 - Pages
      summary: Scan single page
      parameters:
        - name: page_number
          in: path
          required: true
          schema:
            type: integer
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              required:
                - fileUrl
              properties:
                fileUrl:
                  type: string
      responses:
        '200':
          description: Page scanned

  /api/v2/pages/extract:
    post:
      tags:
        - API v2 - Pages
      summary: Extract page content
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              required:
                - fileUrl
                - pageNumber
              properties:
                fileUrl:
                  type: string
                pageNumber:
                  type: integer
                format:
                  type: string
                  enum: [text, json, pdf]
      responses:
        '200':
          description: Page extracted

  /api/v2/pages/summary:
    post:
      tags:
        - API v2 - Pages
      summary: Get pages summary
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              required:
                - fileUrl
              properties:
                fileUrl:
                  type: string
                pageRange:
                  type: object
      responses:
        '200':
          description: Summary generated

  /api/v2/remediate/auto:
    post:
      tags:
        - API v2 - Remediation
      summary: Auto-remediate issues
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              required:
                - fileUrl
              properties:
                fileUrl:
                  type: string
                issues:
                  type: array
                includeAIGuidance:
                  type: boolean
                requireGemini:
                  type: boolean
      responses:
        '200':
          description: Remediation completed

  /api/v2/remediate/auto/download:
    post:
      tags:
        - API v2 - Remediation
      summary: Download remediated PDF
      requestBody:
        required: true
        content:
          multipart/form-data:
            schema:
              type: object
              properties:
                file:
                  type: string
                  format: binary
                issues:
                  type: string
      responses:
        '200':
          description: PDF downloaded
          content:
            application/pdf:
              schema:
                type: string
                format: binary

  /api/v2/remediate/guidance:
    post:
      tags:
        - API v2 - Remediation
      summary: Get remediation guidance
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              required:
                - issueType
              properties:
                issueType:
                  type: string
                issueDescription:
                  type: string
                standard:
                  type: string
                requireGemini:
                  type: boolean
      responses:
        '200':
          description: Guidance provided

  /api/v2/reports/generate:
    post:
      tags:
        - API v2 - Reports
      summary: Generate compliance report
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              required:
                - analysisData
              properties:
                analysisData:
                  type: object
                format:
                  type: string
                  enum: [json, pdf, html, csv, markdown]
                sections:
                  type: array
                  items:
                    type: string
      responses:
        '200':
          description: Report generated

  /api/v2/validation/check:
    post:
      tags:
        - API v2 - Validation
      summary: Validate AI output
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              properties:
                aiOutput:
                  type: object
                analysisResult:
                  type: object
                context:
                  type: object
                fallbackResponse:
                  type: object
      responses:
        '200':
          description: Validation completed

  /api/v2/prompts/performance:
    get:
      tags:
        - API v2 - Validation
      summary: Get prompt performance metrics
      parameters:
        - name: promptName
          in: query
          schema:
            type: string
      responses:
        '200':
          description: Performance metrics retrieved

components:
  schemas:
    Error:
      type: object
      properties:
        success:
          type: boolean
          example: false
        error:
          type: string
```

### Step 3: Integrate Swagger into Flask App

Create `src/routes/swagger.py`:

```python
"""Swagger UI integration"""
from flask import Blueprint
from flask_swagger_ui import get_swaggerui_blueprint

SWAGGER_URL = '/api/docs'
API_URL = '/static/openapi.yaml'

swagger_bp = get_swaggerui_blueprint(
    SWAGGER_URL,
    API_URL,
    config={
        'app_name': "PDF Accessibility Compliance API",
        'defaultModelsExpandDepth': -1,
        'displayRequestDuration': True,
        'filter': True,
        'tryItOutEnabled': True
    }
)
```

### Step 4: Update app.py

Add to [`src/app.py`](src/app.py):

```python
# Add after other imports
from src.routes.swagger import swagger_bp

# Add after other blueprint registrations
app.register_blueprint(swagger_bp, url_prefix='/api/docs')
logger.info("✅ Swagger UI available at /api/docs")
```

### Step 5: Copy OpenAPI spec to static folder

```bash
mkdir -p static
cp docs/openapi.yaml static/
```

### Step 6: Access Swagger UI

Start your application and navigate to:
```
http://localhost:8000/api/docs
```

---

## Alternative: Postman

### Setup Steps

1. **Install Postman**: Download from https://www.postman.com/downloads/

2. **Import OpenAPI Spec**:
   - File → Import → Upload `docs/openapi.yaml`
   - Postman auto-generates collection

3. **Create Environments**:

**Local Environment:**
```json
{
  "name": "Local",
  "values": [
    {"key": "base_url", "value": "http://localhost:8000", "enabled": true},
    {"key": "api_v1_prefix", "value": "/api/v1", "enabled": true},
    {"key": "api_v2_prefix", "value": "/api/v2", "enabled": true},
    {"key": "test_pdf_path", "value": "/path/to/test.pdf", "enabled": true}
  ]
}
```

**Production Environment:**
```json
{
  "name": "Production",
  "values": [
    {"key": "base_url", "value": "https://api.production.com", "enabled": true},
    {"key": "api_v1_prefix", "value": "/api/v1", "enabled": true},
    {"key": "api_v2_prefix", "value": "/api/v2", "enabled": true}
  ]
}
```

4. **Create Collection Structure**:

```
PDF Compliance API
├── Health
│   └── GET /health
├── API v1
│   ├── POST /api/v1/scan
│   ├── POST /api/v1/remediate
│   └── POST /api/v1/dashboard
└── API v2
    ├── Analysis
    │   ├── POST /api/v2/analyze
    │   ├── POST /api/v2/analyze/upload
    │   └── POST /api/v2/analyze/batch
    ├── PII
    │   └── POST /api/v2/pii/detect
    ├── Pages
    │   ├── POST /api/v2/pages/analyze
    │   ├── POST /api/v2/scan/page/:page_number
    │   ├── POST /api/v2/pages/extract
    │   └── POST /api/v2/pages/summary
    ├── Remediation
    │   ├── POST /api/v2/remediate/auto
    │   ├── POST /api/v2/remediate/auto/download
    │   └── POST /api/v2/remediate/guidance
    ├── Reports
    │   └── POST /api/v2/reports/generate
    └── Validation
        ├── POST /api/v2/validation/check
        └── GET /api/v2/prompts/performance
```

5. **Add Test Scripts**:

Example for `/api/v2/analyze`:

```javascript
// Pre-request Script
pm.environment.set("timestamp", new Date().toISOString());

// Tests
pm.test("Status code is 200", function () {
    pm.response.to.have.status(200);
});

pm.test("Response has success field", function () {
    var jsonData = pm.response.json();
    pm.expect(jsonData).to.have.property('success');
});

pm.test("Response time is less than 5000ms", function () {
    pm.expect(pm.response.responseTime).to.be.below(5000);
});

pm.test("Compliance score is present", function () {
    var jsonData = pm.response.json();
    pm.expect(jsonData).to.have.property('complianceScore');
    pm.expect(jsonData.complianceScore).to.be.a('number');
});

// Save response for next request
pm.environment.set("last_analysis", JSON.stringify(pm.response.json()));
```

6. **Run Collection**:
   - Collection Runner → Select collection → Run
   - Export results as JSON/HTML

---

## Alternative: pytest + requests

### Setup

Create `tests/test_api_comprehensive.py`:

```python
"""Comprehensive API testing suite"""
import pytest
import requests
import json
from pathlib import Path

BASE_URL = "http://localhost:8000"
TEST_PDF = "docs/fixtures/accessible_guide.pdf"

class TestAPIv1:
    """Test API v1 endpoints"""
    
    def test_v1_scan(self):
        """Test /api/v1/scan endpoint"""
        response = requests.post(
            f"{BASE_URL}/api/v1/scan",
            json={"fileUrls": [TEST_PDF]}
        )
        assert response.status_code == 200
        data = response.json()
        assert "success" in data or "error" not in data
    
    def test_v1_scan_invalid_input(self):
        """Test scan with invalid input"""
        response = requests.post(
            f"{BASE_URL}/api/v1/scan",
            json={"fileUrls": []}
        )
        assert response.status_code == 400
    
    def test_v1_remediate(self):
        """Test /api/v1/remediate endpoint"""
        response = requests.post(
            f"{BASE_URL}/api/v1/remediate",
            json={"fileUrls": [TEST_PDF]}
        )
        assert response.status_code == 200
    
    def test_v1_dashboard(self):
        """Test /api/v1/dashboard endpoint"""
        response = requests.post(
            f"{BASE_URL}/api/v1/dashboard",
            json={"fileUrls": [TEST_PDF]}
        )
        assert response.status_code == 200


class TestAPIv2Analysis:
    """Test API v2 analysis endpoints"""
    
    def test_v2_analyze_basic(self):
        """Test basic document analysis"""
        response = requests.post(
            f"{BASE_URL}/api/v2/analyze",
            json={
                "fileUrl": TEST_PDF,
                "options": {
                    "detectPII": False,
                    "pageLevel": False,
                    "autoRemediate": False
                }
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") is True
        assert "complianceScore" in data
        assert "issues" in data
    
    def test_v2_analyze_with_pii(self):
        """Test analysis with PII detection"""
        response = requests.post(
            f"{BASE_URL}/api/v2/analyze",
            json={
                "fileUrl": TEST_PDF,
                "options": {
                    "detectPII": True,
                    "piiSensitivity": "high"
                }
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "piiDetected" in data
    
    def test_v2_analyze_upload(self):
        """Test multipart upload analysis"""
        with open(TEST_PDF, 'rb') as f:
            files = {'file': f}
            data = {'options': json.dumps({"detectPII": True})}
            response = requests.post(
                f"{BASE_URL}/api/v2/analyze/upload",
                files=files,
                data=data
            )
        assert response.status_code == 200
    
    def test_v2_analyze_batch(self):
        """Test batch analysis"""
        response = requests.post(
            f"{BASE_URL}/api/v2/analyze/batch",
            json={
                "fileUrls": [TEST_PDF, TEST_PDF],
                "options": {}
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data.get("results", [])) == 2


class TestAPIv2Pages:
    """Test API v2 page-level endpoints"""
    
    def test_pages_analyze(self):
        """Test page range analysis"""
        response = requests.post(
            f"{BASE_URL}/api/v2/pages/analyze",
            json={
                "fileUrl": TEST_PDF,
                "pageRange": {"start": 1, "end": 2}
            }
        )
        assert response.status_code == 200
    
    def test_scan_single_page(self):
        """Test single page scan"""
        response = requests.post(
            f"{BASE_URL}/api/v2/scan/page/1",
            json={"fileUrl": TEST_PDF}
        )
        assert response.status_code == 200
    
    def test_extract_page_text(self):
        """Test page text extraction"""
        response = requests.post(
            f"{BASE_URL}/api/v2/pages/extract",
            json={
                "fileUrl": TEST_PDF,
                "pageNumber": 1,
                "format": "text"
            }
        )
        assert response.status_code == 200
    
    def test_pages_summary(self):
        """Test pages summary"""
        response = requests.post(
            f"{BASE_URL}/api/v2/pages/summary",
            json={"fileUrl": TEST_PDF}
        )
        assert response.status_code == 200


class TestAPIv2Remediation:
    """Test API v2 remediation endpoints"""
    
    def test_auto_remediate(self):
        """Test auto-remediation"""
        response = requests.post(
            f"{BASE_URL}/api/v2/remediate/auto",
            json={
                "fileUrl": TEST_PDF,
                "issues": [],
                "includeAIGuidance": True
            }
        )
        assert response.status_code == 200
    
    def test_download_remediated_pdf(self):
        """Test remediated PDF download"""
        with open(TEST_PDF, 'rb') as f:
            files = {'file': f}
            response = requests.post(
                f"{BASE_URL}/api/v2/remediate/auto/download",
                files=files
            )
        assert response.status_code == 200
        assert response.headers['Content-Type'] == 'application/pdf'
    
    def test_remediation_guidance(self):
        """Test remediation guidance"""
        response = requests.post(
            f"{BASE_URL}/api/v2/remediate/guidance",
            json={
                "issueType": "missing_alt_text",
                "issueDescription": "Image lacks alt text"
            }
        )
        assert response.status_code == 200


class TestAPIv2Reports:
    """Test API v2 report generation"""
    
    def test_generate_json_report(self):
        """Test JSON report generation"""
        analysis_data = {
            "complianceScore": 85,
            "issues": [],
            "recommendations": []
        }
        response = requests.post(
            f"{BASE_URL}/api/v2/reports/generate",
            json={
                "analysisData": analysis_data,
                "format": "json"
            }
        )
        assert response.status_code == 200
    
    def test_generate_pdf_report(self):
        """Test PDF report generation"""
        analysis_data = {
            "complianceScore": 85,
            "issues": [],
            "recommendations": []
        }
        response = requests.post(
            f"{BASE_URL}/api/v2/reports/generate",
            json={
                "analysisData": analysis_data,
                "format": "pdf"
            }
        )
        assert response.status_code == 200
        assert 'application/pdf' in response.headers.get('Content-Type', '')


class TestAPIv2Validation:
    """Test API v2 validation endpoints"""
    
    def test_validation_check(self):
        """Test AI validation"""
        response = requests.post(
            f"{BASE_URL}/api/v2/validation/check",
            json={
                "aiOutput": {"result": "test"},
                "context": {}
            }
        )
        assert response.status_code == 200
    
    def test_prompt_performance(self):
        """Test prompt performance metrics"""
        response = requests.get(
            f"{BASE_URL}/api/v2/prompts/performance"
        )
        assert response.status_code == 200


class TestAPIComparison:
    """Compare v1 and v2 behavior"""
    
    def test_scan_comparison(self):
        """Compare v1 scan vs v2 analyze"""
        # v1 scan
        v1_response = requests.post(
            f"{BASE_URL}/api/v1/scan",
            json={"fileUrls": [TEST_PDF]}
        )
        
        # v2 analyze
        v2_response = requests.post(
            f"{BASE_URL}/api/v2/analyze",
            json={"fileUrl": TEST_PDF, "options": {}}
        )
        
        assert v1_response.status_code == 200
        assert v2_response.status_code == 200
        
        # v2 should have more detailed response
        v2_data = v2_response.json()
        assert "complianceScore" in v2_data
        assert "recommendations" in v2_data


# Performance tests
class TestPerformance:
    """Performance and load testing"""
    
    def test_response_time_analyze(self):
        """Test analyze endpoint response time"""
        import time
        start = time.time()
        response = requests.post(
            f"{BASE_URL}/api/v2/analyze",
            json={"fileUrl": TEST_PDF, "options": {}}
        )
        duration = time.time() - start
        
        assert response.status_code == 200
        assert duration < 10.0  # Should complete within 10 seconds
    
    def test_concurrent_requests(self):
        """Test concurrent request handling"""
        import concurrent.futures
        
        def make_request():
            return requests.get(f"{BASE_URL}/health")
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_request) for _ in range(10)]
            results = [f.result() for f in futures]
        
        assert all(r.status_code == 200 for r in results)
```

### Run Tests

```bash
# Run all tests
pytest tests/test_api_comprehensive.py -v

# Run specific test class
pytest tests/test_api_comprehensive.py::TestAPIv2Analysis -v

# Run with coverage
pytest tests/test_api_comprehensive.py --cov=src --cov-report=html

# Generate report
pytest tests/test_api_comprehensive.py --html=report.html --self-contained-html
```

---

## API Endpoint Inventory

### API v1 (3 endpoints)

| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/api/v1/scan` | Scan PDFs for issues |
| POST | `/api/v1/remediate` | Get remediation guidance |
| POST | `/api/v1/dashboard` | Generate dashboard |

### API v2 (17 endpoints)

| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/api/v2/analyze` | Analyze document |
| POST | `/api/v2/analyze/upload` | Analyze uploaded file |
| POST | `/api/v2/analyze/batch` | Batch analysis |
| POST | `/api/v2/pii/detect` | Detect PII |
| POST | `/api/v2/pages/analyze` | Analyze page range |
| POST | `/api/v2/scan/pages` | Scan pages (compat) |
| POST | `/api/v2/scan/page/<n>` | Scan single page |
| POST | `/api/v2/pages/extract` | Extract page content |
| POST | `/api/v2/extract/page/<n>` | Extract page (compat) |
| POST | `/api/v2/pages/summary` | Get pages summary |
| POST | `/api/v2/remediate/auto` | Auto-remediate |
| POST | `/api/v2/remediate/auto/download` | Download remediated PDF |
| POST | `/api/v2/remediate/guidance` | Get guidance |
| POST | `/api/v2/reports/generate` | Generate report |
| POST | `/api/v2/validation/check` | Validate AI output |
| GET | `/api/v2/prompts/performance` | Get prompt metrics |
| GET | `/health` | Health check |

---

## Test Scenarios by Endpoint

### Critical Test Cases

#### 1. `/api/v2/analyze` - Document Analysis
- ✅ Valid PDF with issues
- ✅ Valid PDF without issues
- ✅ Invalid file path
- ✅ With PII detection enabled
- ✅ With page-level analysis
- ✅ With auto-remediation
- ✅ With AI validation
- ✅ All options combined
- ✅ Large file (>10MB)
- ✅ Corrupted PDF

#### 2. `/api/v2/analyze/upload` - Multipart Upload
- ✅ Valid PDF upload
- ✅ Missing file
- ✅ Invalid file type
- ✅ With options JSON
- ✅ Large file upload
- ✅ Multiple concurrent uploads

#### 3. `/api/v2/remediate/auto/download` - PDF Download
- ✅ Successful download
- ✅ Verify PDF integrity
- ✅ Check filename format
- ✅ With custom issues
- ✅ Empty issues array

#### 4. `/api/v2/pii/detect` - PII Detection
- ✅ Low sensitivity
- ✅ Medium sensitivity
- ✅ High sensitivity
- ✅ With redaction enabled
- ✅ Document without PII
- ✅ Document with multiple PII types

---

## Authentication & Environment Management

### Environment Variables

Create `.env.test`:

```bash
# API Configuration
API_BASE_URL=http://localhost:8000
API_V1_PREFIX=/api/v1
API_V2_PREFIX=/api/v2

# Test Data
TEST_PDF_PATH=docs/fixtures/accessible_guide.pdf
TEST_PDF_MISSING_ALT=docs/fixtures/missing_alttext.pdf
TEST_PDF_UNTAGGED=docs/fixtures/untagged_report3.pdf

# Gemini API (for AI features)
GEMINI_API_KEY=your_test_api_key

# Test Configuration
ENABLE_PERFORMANCE_TESTS=true
MAX_RESPONSE_TIME_MS=5000
CONCURRENT_REQUESTS=10
```

### Load Environment in Tests

```python
import os
from dotenv import load_dotenv

load_dotenv('.env.test')

BASE_URL = os.getenv('API_BASE_URL', 'http://localhost:8000')
TEST_PDF = os.getenv('TEST_PDF_PATH')
```

---

## Best Practices

### 1. Test Organization

```
tests/
├── conftest.py              # Shared fixtures
├── test_api_v1.py          # v1 endpoints
├── test_api_v2_analysis.py # v2 analysis
├── test_api_v2_pages.py    # v2 pages
├── test_api_v2_remediation.py
├── test_api_v2_reports.py
├── test_api_comparison.py  # v1 vs v2
├── test_performance.py     # Load tests
└── test_integration.py     # End-to-end
```

### 2. Shared Fixtures

Create `tests/conftest.py`:

```python
import pytest
import requests

@pytest.fixture(scope="session")
def base_url():
    return "http://localhost:8000"

@pytest.fixture(scope="session")
def test_pdf_path():
    return "docs/fixtures/accessible_guide.pdf"

@pytest.fixture
def api_client(base_url):
    """Reusable API client"""
    class APIClient:
        def __init__(self, base_url):
            self.base_url = base_url
            self.session = requests.Session()
        
        def post(self, endpoint, **kwargs):
            return self.session.post(f"{self.base_url}{endpoint}", **kwargs)
        
        def get(self, endpoint, **kwargs):
            return self.session.get(f"{self.base_url}{endpoint}", **kwargs)
    
    return APIClient(base_url)

@pytest.fixture
def sample_analysis_data():
    """Sample analysis data for testing"""
    return {
        "complianceScore": 85,
        "wcagLevel": "AA",
        "issues": [
            {
                "description": "Missing alt text",
                "severity": "high",
                "page": 1
            }
        ],
        "recommendations": []
    }
```

### 3. Test Data Management

```python
# Use parametrize for multiple test cases
@pytest.mark.parametrize("sensitivity,expected_count", [
    ("low", 0),
    ("medium", 5),
    ("high", 10)
])
def test_pii_sensitivity_levels(api_client, test_pdf_path, sensitivity, expected_count):
    response = api_client.post(
        "/api/v2/pii/detect",
        json={
            "fileUrl": test_pdf_path,
            "sensitivity": sensitivity
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data.get("findings", [])) >= expected_count
```

### 4. Error Handling Tests

```python
def test_error_responses():
    """Test all error scenarios"""
    test_cases = [
        {
            "endpoint": "/api/v2/analyze",
            "payload": {},  # Missing fileUrl
            "expected_status": 400,
            "expected_error": "fileUrl is required"
        },
        {
            "endpoint": "/api/v2/analyze",
            "payload": {"fileUrl": "/nonexistent.pdf"},
            "expected_status": 500,
            "expected_error": "File not found"
        }
    ]
    
    for case in test_cases:
        response = requests.post(
            f"{BASE_URL}{case['endpoint']}",
            json=case['payload']
        )
        assert response.status_code == case['expected_status']
        assert case['expected_error'] in response.json().get('error', '')
```

### 5. Response Validation

```python
from jsonschema import validate

ANALYZE_RESPONSE_SCHEMA = {
    "type": "object",
    "required": ["success", "complianceScore", "issues"],
    "properties": {
        "success": {"type": "boolean"},
        "complianceScore": {"type": "number", "minimum": 0, "maximum": 100},
        "issues": {"type": "array"},
        "recommendations": {"type": "array"}
    }
}

def test_response_schema():
    response = requests.post(
        f"{BASE_URL}/api/v2/analyze",
        json={"fileUrl": TEST_PDF, "options": {}}
    )
    data = response.json()
    validate(instance=data, schema=ANALYZE_RESPONSE_SCHEMA)
```

---

## CI/CD Integration

### GitHub Actions Workflow

Create `.github/workflows/api-tests.yml`:

```yaml
name: API Tests

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      app:
        image: python:3.11
        ports:
          - 8000:8000
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-cov requests
      
      - name: Start application
        run: |
          python src/app.py &
          sleep 10
      
      - name: Run API tests
        run: |
          pytest tests/test_api_comprehensive.py -v --cov=src --cov-report=xml
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          file: ./coverage.xml
      
      - name: Generate test report
        if: always()
        run: |
          pytest tests/test_api_comprehensive.py --html=report.html --self-contained-html
      
      - name: Upload test report
        if: always()
        uses: actions/upload-artifact@v3
        with:
          name: test-report
          path: report.html
```

---

## Quick Start Commands

### 1. Start Application
```bash
docker-compose up --build -d
```

### 2. Access Swagger UI
```bash
open http://localhost:8000/api/docs
```

### 3. Run pytest Tests
```bash
pytest tests/test_api_comprehensive.py -v --html=report.html
```

### 4. Run Postman Collection
```bash
newman run postman_collection.json -e local_environment.json --reporters cli,html
```

### 5. Generate Coverage Report
```bash
pytest --cov=src --cov-report=html
open htmlcov/index.html
```

---

## Troubleshooting

### Common Issues

1. **Connection Refused**
   ```bash
   # Check if app is running
   curl http://localhost:8000/health
   
   # Check Docker logs
   docker-compose logs -f
   ```

2. **File Not Found Errors**
   ```bash
   # Use absolute paths
   pwd
   # Update TEST_PDF_PATH in tests
   ```

3. **Timeout Errors**
   ```bash
   # Increase timeout in tests
   response = requests.post(url, json=data, timeout=30)
   ```

4. **Schema Validation Failures**
   ```bash
   # Check response structure
   print(json.dumps(response.json(), indent=2))
   ```

---

## Summary

**Recommended Testing Stack:**
1. **Swagger UI** - Interactive testing & documentation
2. **pytest + requests** - Automated regression tests
3. **Postman** - Manual testing & team collaboration
4. **GitHub Actions** - CI/CD automation

**Next Steps:**
1. Implement Swagger UI integration
2. Create comprehensive pytest suite
3. Set up Postman collections
4. Configure CI/CD pipeline
5. Generate test coverage reports

This approach provides complete coverage of all endpoints across both API versions with automated testing, documentation, and reporting capabilities.