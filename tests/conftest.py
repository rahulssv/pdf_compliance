"""
Shared test fixtures and configuration for pytest.

This module provides common fixtures, mock objects, and test utilities
used across all test suites.
"""

import io
import os
import sys
from pathlib import Path
from typing import Dict, Any, Generator
from unittest.mock import Mock, MagicMock

import pytest
from flask import Flask
from flask.testing import FlaskClient

# Keep AI calls disabled during tests.
os.environ.setdefault("GEMINI_API_KEY", "")

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.app import create_app
from src.config import Config


# ============================================================================
# Application Fixtures
# ============================================================================

@pytest.fixture(scope="session")
def app() -> Generator[Flask, None, None]:
    """Create Flask application for testing."""
    os.environ["TESTING"] = "true"
    
    app = create_app()
    app.config["TESTING"] = True
    app.config["WTF_CSRF_ENABLED"] = False
    
    yield app


@pytest.fixture(scope="function")
def client(app: Flask) -> FlaskClient:
    """Create Flask test client."""
    return app.test_client()


@pytest.fixture(scope="function")
def app_context(app: Flask) -> Generator:
    """Create Flask application context."""
    with app.app_context():
        yield


# ============================================================================
# Mock Service Fixtures
# ============================================================================

@pytest.fixture
def mock_gemini_service() -> Mock:
    """Mock Gemini AI service."""
    mock = Mock()
    mock.analyze_accessibility.return_value = {
        "issues": [],
        "score": 95,
        "recommendations": ["Test recommendation"]
    }
    mock.validate_response.return_value = True
    return mock


@pytest.fixture
def mock_pii_detector() -> Mock:
    """Mock PII detector service."""
    mock = Mock()
    mock.detect_pii.return_value = {
        "pii_found": False,
        "pii_types": [],
        "masked_content": "Test content",
        "confidence": 0.95
    }
    return mock


@pytest.fixture
def mock_page_processor() -> Mock:
    """Mock page processor service."""
    mock = Mock()
    mock.process_pages.return_value = {
        "total_pages": 10,
        "pages": [],
        "processing_time": 1.5
    }
    return mock


@pytest.fixture
def mock_ai_validator() -> Mock:
    """Mock AI validator service."""
    mock = Mock()
    mock.validate.return_value = {
        "confidence_score": 85,
        "validation_passed": True,
        "layer_scores": {
            "rule_based": 90,
            "pattern_matching": 85,
            "consistency": 80,
            "knowledge_base": 85,
            "ensemble": 88
        }
    }
    return mock


@pytest.fixture
def mock_auto_remediation() -> Mock:
    """Mock auto remediation service."""
    mock = Mock()
    mock.remediate.return_value = {
        "automated_fixes": 5,
        "manual_actions": 3,
        "success_rate": 0.85
    }
    return mock


# ============================================================================
# Test Data Fixtures
# ============================================================================

@pytest.fixture
def sample_pdf_bytes() -> bytes:
    """Generate sample PDF bytes for testing."""
    # Minimal valid PDF structure
    pdf_content = b"""%PDF-1.4
1 0 obj
<<
/Type /Catalog
/Pages 2 0 R
>>
endobj
2 0 obj
<<
/Type /Pages
/Kids [3 0 R]
/Count 1
>>
endobj
3 0 obj
<<
/Type /Page
/Parent 2 0 R
/MediaBox [0 0 612 792]
/Contents 4 0 R
/Resources <<
/Font <<
/F1 <<
/Type /Font
/Subtype /Type1
/BaseFont /Helvetica
>>
>>
>>
>>
endobj
4 0 obj
<<
/Length 44
>>
stream
BT
/F1 12 Tf
100 700 Td
(Test PDF) Tj
ET
endstream
endobj
xref
0 5
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
0000000317 00000 n 
trailer
<<
/Size 5
/Root 1 0 R
>>
startxref
410
%%EOF
"""
    return pdf_content


@pytest.fixture
def sample_pdf_file(sample_pdf_bytes: bytes) -> io.BytesIO:
    """Create in-memory PDF file for testing."""
    return io.BytesIO(sample_pdf_bytes)


@pytest.fixture
def sample_scan_request() -> Dict[str, Any]:
    """Sample scan request payload."""
    return {
        "fileUrls": ["test.pdf"],
        "standards": ["WCAG_2_1", "PDF_UA"],
        "options": {
            "detectPII": True,
            "pageLevel": False,
            "includeValidation": True
        }
    }


@pytest.fixture
def sample_scan_response() -> Dict[str, Any]:
    """Sample scan response payload."""
    return {
        "status": "success",
        "results": {
            "overall_score": 85,
            "issues_found": 5,
            "pii_detected": False,
            "pages_analyzed": 10
        }
    }


@pytest.fixture
def sample_pii_data() -> Dict[str, Any]:
    """Sample data containing PII."""
    return {
        "text": "Contact John Doe at john.doe@example.com or 555-123-4567. SSN: 123-45-6789",
        "expected_pii_types": ["EMAIL", "PHONE", "SSN", "PERSON"]
    }


@pytest.fixture
def sample_page_data() -> Dict[str, Any]:
    """Sample page analysis data."""
    return {
        "page_number": 1,
        "text_content": "Sample page content",
        "has_images": True,
        "has_forms": False,
        "accessibility_score": 90
    }


# ============================================================================
# File System Fixtures
# ============================================================================

@pytest.fixture
def temp_pdf_file(tmp_path: Path, sample_pdf_bytes: bytes) -> Path:
    """Create temporary PDF file."""
    pdf_file = tmp_path / "test.pdf"
    pdf_file.write_bytes(sample_pdf_bytes)
    return pdf_file


@pytest.fixture
def test_fixtures_dir() -> Path:
    """Get path to test fixtures directory."""
    return Path(__file__).parent.parent / "docs" / "fixtures"


# ============================================================================
# Configuration Fixtures
# ============================================================================

@pytest.fixture
def test_config() -> Dict[str, Any]:
    """Create test configuration."""
    return {
        "TESTING": True,
        "GEMINI_API_KEY": "test-api-key",
        "MAX_MEMORY_MB": 50,
        "EPHEMERAL_MODE": True
    }


# ============================================================================
# Mock External Services
# ============================================================================

@pytest.fixture
def mock_redis() -> Mock:
    """Mock Redis connection."""
    mock = Mock()
    mock.ping.return_value = True
    mock.get.return_value = None
    mock.set.return_value = True
    mock.delete.return_value = 1
    return mock


@pytest.fixture
def mock_gemini_api() -> Mock:
    """Mock Gemini API responses."""
    mock = Mock()
    mock.generate_content.return_value = MagicMock(
        text='{"issues": [], "score": 95, "recommendations": []}'
    )
    return mock


# ============================================================================
# Utility Functions
# ============================================================================

def create_mock_pdf_document(num_pages: int = 1) -> io.BytesIO:
    """
    Create a mock PDF document with specified number of pages.
    
    Args:
        num_pages: Number of pages to create
        
    Returns:
        BytesIO object containing PDF data
    """
    # This is a simplified version - real implementation would use pypdf
    pdf_content = b"%PDF-1.4\n"
    return io.BytesIO(pdf_content)


def assert_valid_response(response: Dict[str, Any]) -> None:
    """
    Assert that a response has valid structure.
    
    Args:
        response: Response dictionary to validate
    """
    assert "status" in response
    assert response["status"] in ["success", "error"]
    if response["status"] == "error":
        assert "error" in response
        assert "message" in response["error"]


# ============================================================================
# Pytest Hooks
# ============================================================================

def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "unit: Unit tests for individual components"
    )
    config.addinivalue_line(
        "markers", "integration: Integration tests for workflows"
    )
    config.addinivalue_line(
        "markers", "e2e: End-to-end tests"
    )
    config.addinivalue_line(
        "markers", "performance: Performance tests"
    )
    config.addinivalue_line(
        "markers", "security: Security tests"
    )


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers automatically."""
    for item in items:
        # Add unit marker to test files in tests/ root
        if "integration" not in str(item.fspath) and "e2e" not in str(item.fspath):
            item.add_marker(pytest.mark.unit)
        
        # Add integration marker to integration tests
        if "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
        
        # Add e2e marker to e2e tests
        if "e2e" in str(item.fspath):
            item.add_marker(pytest.mark.e2e)

