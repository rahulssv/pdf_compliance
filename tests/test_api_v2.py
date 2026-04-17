"""API v2 integration tests."""

import io
import json
from pathlib import Path

import pypdf
from src.routes import api_v2 as api_v2_routes


def _create_test_pdf(path: Path) -> Path:
    writer = pypdf.PdfWriter()
    writer.add_blank_page(width=612, height=792)
    writer.add_metadata({"/Title": "API Test PDF"})
    with open(path, "wb") as f:
        writer.write(f)
    return path


def test_analyze_endpoint_returns_enhanced_payload(client, tmp_path):
    pdf_path = _create_test_pdf(tmp_path / "sample.pdf")

    response = client.post(
        "/api/v2/analyze",
        json={
            "fileUrl": str(pdf_path),
            "options": {
                "detectPII": True,
                "pageLevel": True,
                "autoRemediate": False,
                "validateAI": True,
            },
        },
    )

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["success"] is True
    assert payload["documentName"] == "sample.pdf"
    assert "issues" in payload
    assert "validationMetrics" in payload
    assert "pageSummary" in payload


def test_pii_detect_endpoint_works_for_pdf(client, tmp_path):
    pdf_path = _create_test_pdf(tmp_path / "pii-test.pdf")

    response = client.post(
        "/api/v2/pii/detect",
        json={"fileUrl": str(pdf_path), "sensitivity": "high", "redact": True},
    )

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["success"] is True
    assert "detected" in payload
    assert "totalInstances" in payload


def test_report_generation_json_format(client):
    response = client.post(
        "/api/v2/reports/generate",
        json={
            "analysisData": {
                "documentName": "report.pdf",
                "analysisDate": "2026-04-17T00:00:00",
                "complianceScore": 85,
                "complianceLevel": "partially-compliant",
                "wcagLevel": "AA",
                "totalPages": 1,
                "totalIssues": 1,
                "highIssues": 1,
                "issues": [
                    {
                        "description": "Document language is not declared.",
                        "category": "WCAG",
                        "severity": "high",
                        "wcag_criterion": "WCAG 2.1 SC 3.1.1",
                    }
                ],
                "recommendations": [{"priority": "high", "action": "Set document language."}],
            },
            "format": "json",
        },
    )

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["success"] is True
    assert payload["report"]["document_name"] == "report.pdf"


def test_homepage_renders(client):
    response = client.get("/")
    assert response.status_code == 200
    assert b"PDF Accessibility Compliance Engine" in response.data


def test_analyze_upload_endpoint(client, tmp_path):
    pdf_path = _create_test_pdf(tmp_path / "upload.pdf")
    pdf_bytes = pdf_path.read_bytes()

    response = client.post(
        "/api/v2/analyze/upload",
        data={
            "file": (io.BytesIO(pdf_bytes), "upload.pdf"),
            "options": json.dumps({"pageLevel": True, "detectPII": True, "validateAI": True}),
        },
        content_type="multipart/form-data",
    )

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["success"] is True
    assert payload["documentName"] == "upload.pdf"
    assert "pageSummary" in payload


def test_analyze_upload_defaults_to_non_strict_gemini(client, tmp_path, monkeypatch):
    pdf_path = _create_test_pdf(tmp_path / "upload-default-nonstrict.pdf")
    pdf_bytes = pdf_path.read_bytes()
    require_flags = []

    def fake_generate(*, issue_description, standard, require_gemini=False, max_retries=3):
        require_flags.append(require_gemini)
        if require_gemini:
            raise RuntimeError("Gemini unavailable")
        return {
            "text": "Fallback remediation guidance.",
            "provider": "fallback",
            "model": None,
            "fallback_used": True,
        }

    monkeypatch.setattr(api_v2_routes.gemini_service, "api_key", "configured-key")
    monkeypatch.setattr(
        api_v2_routes.gemini_service,
        "generate_remediation_response",
        fake_generate,
    )

    response = client.post(
        "/api/v2/analyze/upload",
        data={
            "file": (io.BytesIO(pdf_bytes), "upload-default-nonstrict.pdf"),
            "options": json.dumps({"detectPII": False, "pageLevel": False, "validateAI": False}),
        },
        content_type="multipart/form-data",
    )

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["success"] is True
    assert require_flags
    assert all(flag is False for flag in require_flags)


def test_analyze_upload_honors_strict_gemini_option(client, tmp_path, monkeypatch):
    pdf_path = _create_test_pdf(tmp_path / "upload-strict.pdf")
    pdf_bytes = pdf_path.read_bytes()

    def fake_generate(*, issue_description, standard, require_gemini=False, max_retries=3):
        if require_gemini:
            raise RuntimeError("Gemini unavailable")
        return {
            "text": "Fallback remediation guidance.",
            "provider": "fallback",
            "model": None,
            "fallback_used": True,
        }

    monkeypatch.setattr(api_v2_routes.gemini_service, "api_key", "configured-key")
    monkeypatch.setattr(
        api_v2_routes.gemini_service,
        "generate_remediation_response",
        fake_generate,
    )

    response = client.post(
        "/api/v2/analyze/upload",
        data={
            "file": (io.BytesIO(pdf_bytes), "upload-strict.pdf"),
            "options": json.dumps(
                {
                    "detectPII": False,
                    "pageLevel": False,
                    "validateAI": False,
                    "requireGeminiRemediation": True,
                }
            ),
        },
        content_type="multipart/form-data",
    )

    assert response.status_code == 500
    payload = response.get_json()
    assert payload["success"] is False
    assert "Gemini unavailable" in payload["error"]


def test_compatibility_page_endpoints(client, tmp_path):
    pdf_path = _create_test_pdf(tmp_path / "compat.pdf")

    page_response = client.post(
        "/api/v2/scan/page/1",
        json={"fileUrl": str(pdf_path)},
    )
    assert page_response.status_code == 200
    page_payload = page_response.get_json()
    assert page_payload["success"] is True
    assert page_payload["page"]["pageNumber"] == 1

    summary_response = client.post(
        "/api/v2/pages/summary",
        json={"fileUrl": str(pdf_path)},
    )
    assert summary_response.status_code == 200
    summary_payload = summary_response.get_json()
    assert summary_payload["success"] is True
    assert summary_payload["summary"]["totalPages"] >= 1


def test_report_generation_pdf_format(client):
    response = client.post(
        "/api/v2/reports/generate",
        json={
            "analysisData": {
                "documentName": "report.pdf",
                "analysisDate": "2026-04-17T00:00:00+00:00",
                "complianceScore": 85,
                "complianceLevel": "partially-compliant",
                "wcagLevel": "AA",
                "totalPages": 1,
                "totalIssues": 1,
                "highIssues": 1,
                "issues": [
                    {
                        "description": "Document language is not declared.",
                        "category": "WCAG",
                        "severity": "high",
                        "wcag_criterion": "WCAG 2.1 SC 3.1.1",
                    }
                ],
                "recommendations": [{"priority": "high", "action": "Set document language."}],
            },
            "format": "pdf",
        },
    )

    assert response.status_code == 200
    assert response.mimetype == "application/pdf"
    assert response.data.startswith(b"%PDF")
