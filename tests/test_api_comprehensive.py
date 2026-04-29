"""Comprehensive API testing suite for v1 and v2 endpoints"""
import pytest
import requests
import json
from pathlib import Path
import os

# Configuration
BASE_URL = os.getenv('API_BASE_URL', 'http://localhost:8000')
TEST_PDF = "docs/fixtures/accessible_guide.pdf"
TEST_PDF_MISSING_ALT = "docs/fixtures/missing_alttext.pdf"
TEST_PDF_UNTAGGED = "docs/fixtures/untagged_report3.pdf"


class TestHealth:
    """Test health check endpoint"""
    
    def test_health_check(self):
        """Test /health endpoint"""
        response = requests.get(f"{BASE_URL}/health")
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "healthy"


class TestAPIv1:
    """Test API v1 endpoints"""
    
    def test_v1_scan_valid(self):
        """Test /api/v1/scan with valid input"""
        response = requests.post(
            f"{BASE_URL}/api/v1/scan",
            json={"fileUrls": [TEST_PDF]}
        )
        assert response.status_code == 200
        data = response.json()
        # Should not have error field on success
        assert "error" not in data or data.get("success") is True
    
    def test_v1_scan_empty_array(self):
        """Test scan with empty fileUrls array"""
        response = requests.post(
            f"{BASE_URL}/api/v1/scan",
            json={"fileUrls": []}
        )
        assert response.status_code == 400
        data = response.json()
        assert "error" in data
    
    def test_v1_scan_missing_field(self):
        """Test scan without fileUrls field"""
        response = requests.post(
            f"{BASE_URL}/api/v1/scan",
            json={}
        )
        assert response.status_code == 400
        data = response.json()
        assert "error" in data
        assert "fileUrls" in data["error"]
    
    def test_v1_scan_invalid_type(self):
        """Test scan with non-array fileUrls"""
        response = requests.post(
            f"{BASE_URL}/api/v1/scan",
            json={"fileUrls": "not-an-array"}
        )
        assert response.status_code == 400
    
    def test_v1_remediate_valid(self):
        """Test /api/v1/remediate endpoint"""
        response = requests.post(
            f"{BASE_URL}/api/v1/remediate",
            json={"fileUrls": [TEST_PDF]}
        )
        assert response.status_code == 200
    
    def test_v1_remediate_invalid(self):
        """Test remediate with invalid input"""
        response = requests.post(
            f"{BASE_URL}/api/v1/remediate",
            json={"fileUrls": []}
        )
        assert response.status_code == 400
    
    def test_v1_dashboard_valid(self):
        """Test /api/v1/dashboard endpoint"""
        response = requests.post(
            f"{BASE_URL}/api/v1/dashboard",
            json={"fileUrls": [TEST_PDF]}
        )
        assert response.status_code == 200
    
    def test_v1_dashboard_multiple_files(self):
        """Test dashboard with multiple files"""
        response = requests.post(
            f"{BASE_URL}/api/v1/dashboard",
            json={"fileUrls": [TEST_PDF, TEST_PDF_MISSING_ALT]}
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
                    "autoRemediate": False,
                    "validateAI": False
                }
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") is True
        assert "complianceScore" in data
        assert "issues" in data
        assert isinstance(data["issues"], list)
    
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
        # PII detection should add piiDetected field
        assert "piiDetected" in data or "success" in data
    
    def test_v2_analyze_page_level(self):
        """Test analysis with page-level details"""
        response = requests.post(
            f"{BASE_URL}/api/v2/analyze",
            json={
                "fileUrl": TEST_PDF,
                "options": {
                    "pageLevel": True
                }
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "pageAnalyses" in data or "success" in data
    
    def test_v2_analyze_auto_remediate(self):
        """Test analysis with auto-remediation"""
        response = requests.post(
            f"{BASE_URL}/api/v2/analyze",
            json={
                "fileUrl": TEST_PDF,
                "options": {
                    "autoRemediate": True
                }
            }
        )
        assert response.status_code == 200
        data = response.json()
        if data.get("success"):
            assert "remediationResults" in data or "autoRemediatedPdfAvailable" in data
    
    def test_v2_analyze_all_options(self):
        """Test analysis with all options enabled"""
        response = requests.post(
            f"{BASE_URL}/api/v2/analyze",
            json={
                "fileUrl": TEST_PDF,
                "options": {
                    "detectPII": True,
                    "piiSensitivity": "medium",
                    "pageLevel": True,
                    "autoRemediate": True,
                    "validateAI": True,
                    "requireGeminiRemediation": False
                }
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") is True
    
    def test_v2_analyze_missing_file_url(self):
        """Test analyze without fileUrl"""
        response = requests.post(
            f"{BASE_URL}/api/v2/analyze",
            json={"options": {}}
        )
        assert response.status_code == 400
    
    def test_v2_analyze_upload(self):
        """Test multipart upload analysis"""
        if not Path(TEST_PDF).exists():
            pytest.skip(f"Test file not found: {TEST_PDF}")
        
        with open(TEST_PDF, 'rb') as f:
            files = {'file': f}
            data = {'options': json.dumps({"detectPII": True})}
            response = requests.post(
                f"{BASE_URL}/api/v2/analyze/upload",
                files=files,
                data=data
            )
        assert response.status_code == 200
        result = response.json()
        assert result.get("success") is True
    
    def test_v2_analyze_upload_no_file(self):
        """Test upload without file"""
        response = requests.post(
            f"{BASE_URL}/api/v2/analyze/upload",
            data={'options': json.dumps({})}
        )
        assert response.status_code == 400
    
    def test_v2_analyze_batch(self):
        """Test batch analysis"""
        response = requests.post(
            f"{BASE_URL}/api/v2/analyze/batch",
            json={
                "fileUrls": [TEST_PDF, TEST_PDF_MISSING_ALT],
                "options": {"detectPII": False}
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "results" in data
        assert len(data["results"]) == 2
    
    def test_v2_analyze_batch_empty(self):
        """Test batch with empty array"""
        response = requests.post(
            f"{BASE_URL}/api/v2/analyze/batch",
            json={"fileUrls": [], "options": {}}
        )
        assert response.status_code == 400


class TestAPIv2PII:
    """Test API v2 PII detection endpoints"""
    
    def test_pii_detect_basic(self):
        """Test basic PII detection"""
        response = requests.post(
            f"{BASE_URL}/api/v2/pii/detect",
            json={
                "fileUrl": TEST_PDF,
                "sensitivity": "medium",
                "redact": False
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "findings" in data or "success" in data
    
    @pytest.mark.parametrize("sensitivity", ["low", "medium", "high"])
    def test_pii_sensitivity_levels(self, sensitivity):
        """Test different PII sensitivity levels"""
        response = requests.post(
            f"{BASE_URL}/api/v2/pii/detect",
            json={
                "fileUrl": TEST_PDF,
                "sensitivity": sensitivity,
                "redact": False
            }
        )
        assert response.status_code == 200
    
    def test_pii_with_redaction(self):
        """Test PII detection with redaction"""
        response = requests.post(
            f"{BASE_URL}/api/v2/pii/detect",
            json={
                "fileUrl": TEST_PDF,
                "sensitivity": "high",
                "redact": True
            }
        )
        assert response.status_code == 200
        data = response.json()
        if data.get("success") and data.get("findings"):
            assert "redactedContent" in data


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
        data = response.json()
        assert "pageAnalyses" in data or "success" in data
    
    def test_pages_analyze_no_range(self):
        """Test page analysis without range (all pages)"""
        response = requests.post(
            f"{BASE_URL}/api/v2/pages/analyze",
            json={"fileUrl": TEST_PDF}
        )
        assert response.status_code == 200
    
    def test_scan_single_page(self):
        """Test single page scan"""
        response = requests.post(
            f"{BASE_URL}/api/v2/scan/page/1",
            json={"fileUrl": TEST_PDF}
        )
        assert response.status_code == 200
        data = response.json()
        assert "issues" in data or "success" in data
    
    def test_scan_invalid_page(self):
        """Test scan with invalid page number"""
        response = requests.post(
            f"{BASE_URL}/api/v2/scan/page/9999",
            json={"fileUrl": TEST_PDF}
        )
        assert response.status_code in [400, 500]
    
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
        data = response.json()
        assert "text" in data or "content" in data
    
    def test_extract_page_json(self):
        """Test page JSON extraction"""
        response = requests.post(
            f"{BASE_URL}/api/v2/pages/extract",
            json={
                "fileUrl": TEST_PDF,
                "pageNumber": 1,
                "format": "json"
            }
        )
        assert response.status_code == 200
    
    def test_extract_page_pdf(self):
        """Test page PDF extraction"""
        response = requests.post(
            f"{BASE_URL}/api/v2/pages/extract",
            json={
                "fileUrl": TEST_PDF,
                "pageNumber": 1,
                "format": "pdf"
            }
        )
        assert response.status_code == 200
        # Should return PDF binary
        assert 'application/pdf' in response.headers.get('Content-Type', '')
    
    def test_pages_summary(self):
        """Test pages summary"""
        response = requests.post(
            f"{BASE_URL}/api/v2/pages/summary",
            json={"fileUrl": TEST_PDF}
        )
        assert response.status_code == 200
        data = response.json()
        assert "totalPages" in data or "summary" in data


class TestAPIv2Remediation:
    """Test API v2 remediation endpoints"""
    
    def test_auto_remediate_basic(self):
        """Test basic auto-remediation"""
        response = requests.post(
            f"{BASE_URL}/api/v2/remediate/auto",
            json={
                "fileUrl": TEST_PDF,
                "issues": [],
                "includeAIGuidance": False,
                "requireGemini": False
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "remediationResults" in data or "success" in data
    
    def test_auto_remediate_with_ai_guidance(self):
        """Test auto-remediation with AI guidance"""
        response = requests.post(
            f"{BASE_URL}/api/v2/remediate/auto",
            json={
                "fileUrl": TEST_PDF,
                "issues": [],
                "includeAIGuidance": True,
                "requireGemini": False
            }
        )
        assert response.status_code == 200
    
    def test_auto_remediate_with_issues(self):
        """Test auto-remediation with specific issues"""
        issues = [
            {
                "description": "Document language is not declared",
                "standard": "WCAG 2.1 SC 3.1.1"
            }
        ]
        response = requests.post(
            f"{BASE_URL}/api/v2/remediate/auto",
            json={
                "fileUrl": TEST_PDF,
                "issues": issues,
                "includeAIGuidance": False
            }
        )
        assert response.status_code == 200
    
    def test_download_remediated_pdf_upload(self):
        """Test remediated PDF download via upload"""
        if not Path(TEST_PDF).exists():
            pytest.skip(f"Test file not found: {TEST_PDF}")
        
        with open(TEST_PDF, 'rb') as f:
            files = {'file': f}
            response = requests.post(
                f"{BASE_URL}/api/v2/remediate/auto/download",
                files=files
            )
        assert response.status_code == 200
        assert 'application/pdf' in response.headers.get('Content-Type', '')
        # Check filename
        content_disp = response.headers.get('Content-Disposition', '')
        assert 'auto_remediated.pdf' in content_disp
    
    def test_download_remediated_pdf_with_issues(self):
        """Test remediated PDF download with issues"""
        if not Path(TEST_PDF).exists():
            pytest.skip(f"Test file not found: {TEST_PDF}")
        
        issues = json.dumps([
            {"description": "Missing alt text", "standard": "WCAG 2.1"}
        ])
        
        with open(TEST_PDF, 'rb') as f:
            files = {'file': f}
            data = {'issues': issues}
            response = requests.post(
                f"{BASE_URL}/api/v2/remediate/auto/download",
                files=files,
                data=data
            )
        assert response.status_code == 200
        assert 'application/pdf' in response.headers.get('Content-Type', '')
    
    def test_download_remediated_pdf_json(self):
        """Test remediated PDF download via JSON"""
        response = requests.post(
            f"{BASE_URL}/api/v2/remediate/auto/download",
            json={
                "fileUrl": TEST_PDF,
                "issues": []
            }
        )
        assert response.status_code == 200
        assert 'application/pdf' in response.headers.get('Content-Type', '')
    
    def test_remediation_guidance(self):
        """Test remediation guidance"""
        response = requests.post(
            f"{BASE_URL}/api/v2/remediate/guidance",
            json={
                "issueType": "missing_alt_text",
                "issueDescription": "Image lacks alternative text",
                "standard": "WCAG 2.1",
                "requireGemini": False
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "guidance" in data or "template" in data
    
    def test_remediation_guidance_minimal(self):
        """Test remediation guidance with minimal input"""
        response = requests.post(
            f"{BASE_URL}/api/v2/remediate/guidance",
            json={"issueType": "missing_alt_text"}
        )
        assert response.status_code == 200


class TestAPIv2Reports:
    """Test API v2 report generation"""
    
    def get_sample_analysis_data(self):
        """Helper to get sample analysis data"""
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
            "recommendations": [
                {
                    "title": "Add alt text",
                    "description": "Add descriptive alt text to images"
                }
            ]
        }
    
    def test_generate_json_report(self):
        """Test JSON report generation"""
        response = requests.post(
            f"{BASE_URL}/api/v2/reports/generate",
            json={
                "analysisData": self.get_sample_analysis_data(),
                "format": "json"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") is True
        assert "report" in data
    
    def test_generate_pdf_report(self):
        """Test PDF report generation"""
        response = requests.post(
            f"{BASE_URL}/api/v2/reports/generate",
            json={
                "analysisData": self.get_sample_analysis_data(),
                "format": "pdf"
            }
        )
        assert response.status_code == 200
        assert 'application/pdf' in response.headers.get('Content-Type', '')
    
    def test_generate_html_report(self):
        """Test HTML report generation"""
        response = requests.post(
            f"{BASE_URL}/api/v2/reports/generate",
            json={
                "analysisData": self.get_sample_analysis_data(),
                "format": "html"
            }
        )
        assert response.status_code == 200
        assert 'text/html' in response.headers.get('Content-Type', '')
    
    def test_generate_csv_report(self):
        """Test CSV report generation"""
        response = requests.post(
            f"{BASE_URL}/api/v2/reports/generate",
            json={
                "analysisData": self.get_sample_analysis_data(),
                "format": "csv"
            }
        )
        assert response.status_code == 200
        assert 'text/csv' in response.headers.get('Content-Type', '')
    
    def test_generate_markdown_report(self):
        """Test Markdown report generation"""
        response = requests.post(
            f"{BASE_URL}/api/v2/reports/generate",
            json={
                "analysisData": self.get_sample_analysis_data(),
                "format": "markdown"
            }
        )
        assert response.status_code == 200


class TestAPIv2Validation:
    """Test API v2 validation endpoints"""
    
    def test_validation_check(self):
        """Test AI validation"""
        response = requests.post(
            f"{BASE_URL}/api/v2/validation/check",
            json={
                "aiOutput": {"result": "test output"},
                "context": {"source": "test"}
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "confidence" in data or "validation" in data
    
    def test_validation_with_fallback(self):
        """Test validation with fallback response"""
        response = requests.post(
            f"{BASE_URL}/api/v2/validation/check",
            json={
                "aiOutput": {"result": "test"},
                "fallbackResponse": {"result": "fallback"}
            }
        )
        assert response.status_code == 200
    
    def test_prompt_performance(self):
        """Test prompt performance metrics"""
        response = requests.get(
            f"{BASE_URL}/api/v2/prompts/performance"
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
    
    def test_prompt_performance_specific(self):
        """Test specific prompt performance"""
        response = requests.get(
            f"{BASE_URL}/api/v2/prompts/performance?promptName=analyze"
        )
        assert response.status_code == 200


class TestAPIComparison:
    """Compare v1 and v2 API behavior"""
    
    def test_scan_vs_analyze(self):
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
    <write_to_file>
<path>tests/test_api_comprehensive.py</path>
<content>"""Comprehensive API testing suite for v1 and v2 endpoints"""
import pytest
import requests
import json
from pathlib import Path
import os

# Configuration
BASE_URL = os.getenv('API_BASE_URL', 'http://localhost:8000')
TEST_PDF = "docs/fixtures/accessible_guide.pdf"
TEST_PDF_MISSING_ALT = "docs/fixtures/missing_alttext.pdf"
TEST_PDF_UNTAGGED = "docs/fixtures/untagged_report3.pdf"


class TestHealth:
    """Test health check endpoint"""
    
    def test_health_check(self):
        """Test /health endpoint"""
        response = requests.get(f"{BASE_URL}/health")
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "healthy"


class TestAPIv1:
    """Test API v1 endpoints"""
    
    def test_v1_scan_valid(self):
        """Test /api/v1/scan with valid input"""
        response = requests.post(
            f"{BASE_URL}/api/v1/scan",
            json={"fileUrls": [TEST_PDF]}
        )
        assert response.status_code == 200
        data = response.json()
        # Should not have error field on success
        assert "error" not in data or data.get("success") is True
    
    def test_v1_scan_empty_array(self):
        """Test scan with empty fileUrls array"""
        response = requests.post(
            f"{BASE_URL}/api/v1/scan",
            json={"fileUrls": []}
        )
        assert response.status_code == 400
        data = response.json()
        assert "error" in data
    
    def test_v1_scan_missing_field(self):
        """Test scan without fileUrls field"""
        response = requests.post(
            f"{BASE_URL}/api/v1/scan",
            json={}
        )
        assert response.status_code == 400
        data = response.json()
        assert "error" in data
        assert "fileUrls" in data["error"]
    
    def test_v1_scan_invalid_type(self):
        """Test scan with non-array fileUrls"""
        response = requests.post(
            f"{BASE_URL}/api/v1/scan",
            json={"fileUrls": "not-an-array"}
        )
        assert response.status_code == 400
    
    def test_v1_remediate_valid(self):
        """Test /api/v1/remediate endpoint"""
        response = requests.post(
            f"{BASE_URL}/api/v1/remediate",
            json={"fileUrls": [TEST_PDF]}
        )
        assert response.status_code == 200
    
    def test_v1_remediate_invalid(self):
        """Test remediate with invalid input"""
        response = requests.post(
            f"{BASE_URL}/api/v1/remediate",
            json={"fileUrls": []}
        )
        assert response.status_code == 400
    
    def test_v1_dashboard_valid(self):
        """Test /api/v1/dashboard endpoint"""
        response = requests.post(
            f"{BASE_URL}/api/v1/dashboard",
            json={"fileUrls": [TEST_PDF]}
        )
        assert response.status_code == 200
    
    def test_v1_dashboard_multiple_files(self):
        """Test dashboard with multiple files"""
        response = requests.post(
            f"{BASE_URL}/api/v1/dashboard",
            json={"fileUrls": [TEST_PDF, TEST_PDF_MISSING_ALT]}
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
                    "autoRemediate": False,
                    "validateAI": False
                }
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") is True
        assert "complianceScore" in data
        assert "issues" in data
        assert isinstance(data["issues"], list)
    
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
        # PII detection should add piiDetected field
        assert "piiDetected" in data or "success" in data
    
    def test_v2_analyze_page_level(self):
        """Test analysis with page-level details"""
        response = requests.post(
            f"{BASE_URL}/api/v2/analyze",
            json={
                "fileUrl": TEST_PDF,
                "options": {
                    "pageLevel": True
                }
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "pageAnalyses" in data or "success" in data
    
    def test_v2_analyze_auto_remediate(self):
        """Test analysis with auto-remediation"""
        response = requests.post(
            f"{BASE_URL}/api/v2/analyze",
            json={
                "fileUrl": TEST_PDF,
                "options": {
                    "autoRemediate": True
                }
            }
        )
        assert response.status_code == 200
        data = response.json()
        if data.get("success"):
            assert "remediationResults" in data or "autoRemediatedPdfAvailable" in data
    
    def test_v2_analyze_all_options(self):
        """Test analysis with all options enabled"""
        response = requests.post(
            f"{BASE_URL}/api/v2/analyze",
            json={
                "fileUrl": TEST_PDF,
                "options": {
                    "detectPII": True,
                    "piiSensitivity": "medium",
                    "pageLevel": True,
                    "autoRemediate": True,
                    "validateAI": True,
                    "requireGeminiRemediation": False
                }
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") is True
    
    def test_v2_analyze_missing_file_url(self):
        """Test analyze without fileUrl"""
        response = requests.post(
            f"{BASE_URL}/api/v2/analyze",
            json={"options": {}}
        )
        assert response.status_code == 400
    
    def test_v2_analyze_upload(self):
        """Test multipart upload analysis"""
        if not Path(TEST_PDF).exists():
            pytest.skip(f"Test file not found: {TEST_PDF}")
        
        with open(TEST_PDF, 'rb') as f:
            files = {'file': f}
            data = {'options': json.dumps({"detectPII": True})}
            response = requests.post(
                f"{BASE_URL}/api/v2/analyze/upload",
                files=files,
                data=data
            )
        assert response.status_code == 200
        result = response.json()
        assert result.get("success") is True
    
    def test_v2_analyze_upload_no_file(self):
        """Test upload without file"""
        response = requests.post(
            f"{BASE_URL}/api/v2/analyze/upload",
            data={'options': json.dumps({})}
        )
        assert response.status_code == 400
    
    def test_v2_analyze_batch(self):
        """Test batch analysis"""
        response = requests.post(
            f"{BASE_URL}/api/v2/analyze/batch",
            json={
                "fileUrls": [TEST_PDF, TEST_PDF_MISSING_ALT],
                "options": {"detectPII": False}
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "results" in data
        assert len(data["results"]) == 2
    
    def test_v2_analyze_batch_empty(self):
        """Test batch with empty array"""
        response = requests.post(
            f"{BASE_URL}/api/v2/analyze/batch",
            json={"fileUrls": [], "options": {}}
        )
        assert response.status_code == 400


class TestAPIv2PII:
    """Test API v2 PII detection endpoints"""
    
    def test_pii_detect_basic(self):
        """Test basic PII detection"""
        response = requests.post(
            f"{BASE_URL}/api/v2/pii/detect",
            json={
                "fileUrl": TEST_PDF,
                "sensitivity": "medium",
                "redact": False
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "findings" in data or "success" in data
    
    @pytest.mark.parametrize("sensitivity", ["low", "medium", "high"])
    def test_pii_sensitivity_levels(self, sensitivity):
        """Test different PII sensitivity levels"""
        response = requests.post(
            f"{BASE_URL}/api/v2/pii/detect",
            json={
                "fileUrl": TEST_PDF,
                "sensitivity": sensitivity,
                "redact": False
            }
        )
        assert response.status_code == 200
    
    def test_pii_with_redaction(self):
        """Test PII detection with redaction"""
        response = requests.post(
            f"{BASE_URL}/api/v2/pii/detect",
            json={
                "fileUrl": TEST_PDF,
                "sensitivity": "high",
                "redact": True
            }
        )
        assert response.status_code == 200
        data = response.json()
        if data.get("success") and data.get("findings"):
            assert "redactedContent" in data


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
        data = response.json()
        assert "pageAnalyses" in data or "success" in data
    
    def test_pages_analyze_no_range(self):
        """Test page analysis without range (all pages)"""
        response = requests.post(
            f"{BASE_URL}/api/v2/pages/analyze",
            json={"fileUrl": TEST_PDF}
        )
        assert response.status_code == 200
    
    def test_scan_single_page(self):
        """Test single page scan"""
        response = requests.post(
            f"{BASE_URL}/api/v2/scan/page/1",
            json={"fileUrl": TEST_PDF}
        )
        assert response.status_code == 200
        data = response.json()
        assert "issues" in data or "success" in data
    
    def test_scan_invalid_page(self):
        """Test scan with invalid page number"""
        response = requests.post(
            f"{BASE_URL}/api/v2/scan/page/9999",
            json={"fileUrl": TEST_PDF}
        )
        assert response.status_code in [400, 500]
    
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
        data = response.json()
        assert "text" in data or "content" in data
    
    def test_extract_page_json(self):
        """Test page JSON extraction"""
        response = requests.post(
            f"{BASE_URL}/api/v2/pages/extract",
            json={
                "fileUrl": TEST_PDF,
                "pageNumber": 1,
                "format": "json"
            }
        )
        assert response.status_code == 200
    
    def test_extract_page_pdf(self):
        """Test page PDF extraction"""
        response = requests.post(
            f"{BASE_URL}/api/v2/pages/extract",
            json={
                "fileUrl": TEST_PDF,
                "pageNumber": 1,
                "format": "pdf"
            }
        )
        assert response.status_code == 200
        # Should return PDF binary
        assert 'application/pdf' in response.headers.get('Content-Type', '')
    
    def test_pages_summary(self):
        """Test pages summary"""
        response = requests.post(
            f"{BASE_URL}/api/v2/pages/summary",
            json={"fileUrl": TEST_PDF}
        )
        assert response.status_code == 200
        data = response.json()
        assert "totalPages" in data or "summary" in data


class TestAPIv2Remediation:
    """Test API v2 remediation endpoints"""
    
    def test_auto_remediate_basic(self):
        """Test basic auto-remediation"""
        response = requests.post(
            f"{BASE_URL}/api/v2/remediate/auto",
            json={
                "fileUrl": TEST_PDF,
                "issues": [],
                "includeAIGuidance": False,
                "requireGemini": False
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "remediationResults" in data or "success" in data
    
    def test_auto_remediate_with_ai_guidance(self):
        """Test auto-remediation with AI guidance"""
        response = requests.post(
            f"{BASE_URL}/api/v2/remediate/auto",
            json={
                "fileUrl": TEST_PDF,
                "issues": [],
                "includeAIGuidance": True,
                "requireGemini": False
            }
        )
        assert response.status_code == 200
    
    def test_auto_remediate_with_issues(self):
        """Test auto-remediation with specific issues"""
        issues = [
            {
                "description": "Document language is not declared",
                "standard": "WCAG 2.1 SC 3.1.1"
            }
        ]
        response = requests.post(
            f"{BASE_URL}/api/v2/remediate/auto",
            json={
                "fileUrl": TEST_PDF,
                "issues": issues,
                "includeAIGuidance": False
            }
        )
        assert response.status_code == 200
    
    def test_download_remediated_pdf_upload(self):
        """Test remediated PDF download via upload"""
        if not Path(TEST_PDF).exists():
            pytest.skip(f"Test file not found: {TEST_PDF}")
        
        with open(TEST_PDF, 'rb') as f:
            files = {'file': f}
            response = requests.post(
                f"{BASE_URL}/api/v2/remediate/auto/download",
                files=files
            )
        assert response.status_code == 200
        assert 'application/pdf' in response.headers.get('Content-Type', '')
        # Check filename
        content_disp = response.headers.get('Content-Disposition', '')
        assert 'auto_remediated.pdf' in content_disp
    
    def test_download_remediated_pdf_with_issues(self):
        """Test remediated PDF download with issues"""
        if not Path(TEST_PDF).exists():
            pytest.skip(f"Test file not found: {TEST_PDF}")
        
        issues = json.dumps([
            {"description": "Missing alt text", "standard": "WCAG 2.1"}
        ])
        
        with open(TEST_PDF, 'rb') as f:
            files = {'file': f}
            data = {'issues': issues}
            response = requests.post(
                f"{BASE_URL}/api/v2/remediate/auto/download",
                files=files,
                data=data
            )
        assert response.status_code == 200
        assert 'application/pdf' in response.headers.get('Content-Type', '')
    
    def test_download_remediated_pdf_json(self):
        """Test remediated PDF download via JSON"""
        response = requests.post(
            f"{BASE_URL}/api/v2/remediate/auto/download",
            json={
                "fileUrl": TEST_PDF,
                "issues": []
            }
        )
        assert response.status_code == 200
        assert 'application/pdf' in response.headers.get('Content-Type', '')
    
    def test_remediation_guidance(self):
        """Test remediation guidance"""
        response = requests.post(
            f"{BASE_URL}/api/v2/remediate/guidance",
            json={
                "issueType": "missing_alt_text",
                "issueDescription": "Image lacks alternative text",
                "standard": "WCAG 2.1",
                "requireGemini": False
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "guidance" in data or "template" in data
    
    def test_remediation_guidance_minimal(self):
        """Test remediation guidance with minimal input"""
        response = requests.post(
            f"{BASE_URL}/api/v2/remediate/guidance",
            json={"issueType": "missing_alt_text"}
        )
        assert response.status_code == 200


class TestAPIv2Reports:
    """Test API v2 report generation"""
    
    def get_sample_analysis_data(self):
        """Helper to get sample analysis data"""
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
            "recommendations": [
                {
                    "title": "Add alt text",
                    "description": "Add descriptive alt text to images"
                }
            ]
        }
    
    def test_generate_json_report(self):
        """Test JSON report generation"""
        response = requests.post(
            f"{BASE_URL}/api/v2/reports/generate",
            json={
                "analysisData": self.get_sample_analysis_data(),
                "format": "json"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") is True
        assert "report" in data
    
    def test_generate_pdf_report(self):
        """Test PDF report generation"""
        response = requests.post(
            f"{BASE_URL}/api/v2/reports/generate",
            json={
                "analysisData": self.get_sample_analysis_data(),
                "format": "pdf"
            }
        )
        assert response.status_code == 200
        assert 'application/pdf' in response.headers.get('Content-Type', '')
    
    def test_generate_html_report(self):
        """Test HTML report generation"""
        response = requests.post(
            f"{BASE_URL}/api/v2/reports/generate",
            json={
                "analysisData": self.get_sample_analysis_data(),
                "format": "html"
            }
        )
        assert response.status_code == 200
        assert 'text/html' in response.headers.get('Content-Type', '')
    
    def test_generate_csv_report(self):
        """Test CSV report generation"""
        response = requests.post(
            f"{BASE_URL}/api/v2/reports/generate",
            json={
                "analysisData": self.get_sample_analysis_data(),
                "format": "csv"
            }
        )
        assert response.status_code == 200
        assert 'text/csv' in response.headers.get('Content-Type', '')
    
    def test_generate_markdown_report(self):
        """Test Markdown report generation"""
        response = requests.post(
            f"{BASE_URL}/api/v2/reports/generate",
            json={
                "analysisData": self.get_sample_analysis_data(),
                "format": "markdown"
            }
        )
        assert response.status_code == 200


class TestAPIv2Validation:
    """Test API v2 validation endpoints"""
    
    def test_validation_check(self):
        """Test AI validation"""
        response = requests.post(
            f"{BASE_URL}/api/v2/validation/check",
            json={
                "aiOutput": {"result": "test output"},
                "context": {"source": "test"}
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "confidence" in data or "validation" in data
    
    def test_validation_with_fallback(self):
        """Test validation with fallback response"""
        response = requests.post(
            f"{BASE_URL}/api/v2/validation/check",
            json={
                "aiOutput": {"result": "test"},
                "fallbackResponse": {"result": "fallback"}
            }
        )
        assert response.status_code == 200
    
    def test_prompt_performance(self):
        """Test prompt performance metrics"""
        response = requests.get(
            f"{BASE_URL}/api/v2/prompts/performance"
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
    
    def test_prompt_performance_specific(self):
        """Test specific prompt performance"""
        response = requests.get(
            f"{BASE_URL}/api/v2/prompts/performance?promptName=analyze"
        )
        assert response.status_code == 200


class TestAPIComparison:
    """Compare v1 and v2 API behavior"""
    
    def test_scan_vs_analyze(self):
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
    
    def test_remediate_vs_auto_remediate(self):
        """Compare v1 remediate vs v2 auto-remediate"""
        # v1 remediate
        v1_response = requests.post(
            f"{BASE_URL}/api/v1/remediate",
            json={"fileUrls": [TEST_PDF]}
        )
        
        # v2 auto-remediate
        v2_response = requests.post(
            f"{BASE_URL}/api/v2/remediate/auto",
            json={
                "fileUrl": TEST_PDF,
                "issues": [],
                "includeAIGuidance": False
            }
        )
        
        assert v1_response.status_code == 200
        assert v2_response.status_code == 200
        
        # v2 should have more detailed remediation info
        v2_data = v2_response.json()
        assert "remediationResults" in v2_data or "success" in v2_data


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
    
    def test_large_file_processing(self):
        """Test processing of large files"""
        # Skip if large test file not available
        large_file = "docs/fixtures/large_document.pdf"
        if not Path(large_file).exists():
            pytest.skip("Large test file not available")
        
        response = requests.post(
            f"{BASE_URL}/api/v2/analyze",
            json={"fileUrl": large_file, "options": {}}
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") is True

