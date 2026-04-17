"""
API v2 endpoints for enhanced PDF accessibility compliance workflows.
"""

import json
import logging
from dataclasses import asdict
from datetime import datetime, timezone
from io import BytesIO
from typing import Any, Dict, List, Optional, Tuple

import pdfplumber
import pypdf
from flask import Blueprint, jsonify, request, send_file

from src.prompts import PromptManager
from src.services.ai_validator import AIValidator
from src.services.auto_remediation import AutoRemediationEngine
from src.services.ephemeral_file_handler import MemoryAwareFileHandler
from src.services.gemini_service import GeminiService
from src.services.page_processor import PageProcessor
from src.services.pdf_analyzer import PDFAnalyzer
from src.services.pii_detector import PIIDetector
from src.services.report_generator import (
    ComplianceReport,
    ReportConfig,
    ReportFormat,
    ReportGenerator,
    ReportSection,
)

logger = logging.getLogger(__name__)

api_v2_bp = Blueprint("api_v2", __name__)

ephemeral_handler = MemoryAwareFileHandler(max_memory_mb=100)
pdf_analyzer = PDFAnalyzer()
pii_detector = PIIDetector(sensitivity="high")
page_processor = PageProcessor()
remediation_engine = AutoRemediationEngine()
report_generator = ReportGenerator()
ai_validator = AIValidator()
gemini_service = GeminiService()
prompt_manager = PromptManager(storage_path="/tmp/pdf_compliance/prompts")


def _normalize_pii_sensitivity(sensitivity: str) -> str:
    normalized = (sensitivity or "medium").strip().lower()
    if normalized in {"low", "medium", "high"}:
        return normalized
    if normalized == "maximum":
        return "high"
    return "medium"


def _parse_page_range(payload: Optional[Dict[str, Any]]) -> Optional[Tuple[int, int]]:
    if not payload:
        return None
    start = int(payload.get("start", 1))
    end = int(payload.get("end", start))
    if start < 1 or end < 1:
        raise ValueError("pageRange start and end must be >= 1")
    return start, end


def _extract_text(file_buffer: BytesIO) -> str:
    pdf_bytes = file_buffer.getvalue()
    text_parts: List[str] = []
    with pdfplumber.open(BytesIO(pdf_bytes)) as pdf:
        for page in pdf.pages:
            text_parts.append(page.extract_text() or "")
    return "\n".join(text_parts).strip()


def _auto_remediated_download_name(filename: str) -> str:
    cleaned = (filename or "document.pdf").split("/")[-1].split("\\")[-1]
    if cleaned.lower().endswith(".pdf"):
        cleaned = cleaned[:-4]
    return f"{cleaned}_auto_remediated.pdf"


def _issue_severity(description: str) -> str:
    desc = description.lower()
    if any(term in desc for term in ["scanned", "tag tree", "alternative text", "form field"]):
        return "high"
    if any(term in desc for term in ["language", "metadata", "reading order"]):
        return "medium"
    return "low"


def _classify_issue_for_remediation(description: str) -> str:
    issue = {"description": description}
    return remediation_engine._classify_issue(issue)  # Reuse central classification logic.


def _normalize_issue(issue: Dict[str, Any]) -> Dict[str, Any]:
    description = issue.get("description", "Unknown issue")
    severity = issue.get("severity") or _issue_severity(description)
    remediation_type = _classify_issue_for_remediation(description)
    auto_fixable = remediation_type in remediation_engine.auto_fixable_issues
    complexity = "easy" if auto_fixable else ("hard" if severity == "high" else "medium")

    return {
        "category": issue.get("category", "General"),
        "severity": severity,
        "wcag_criterion": issue.get("standard", "N/A"),
        "standard": issue.get("standard", "N/A"),
        "description": description,
        "location": issue.get("scope", "document"),
        "impact": issue.get("impact", "Can reduce accessibility for assistive technology users."),
        "remediation_complexity": complexity,
        "estimated_time": issue.get("estimated_time", "5-20 minutes"),
        "auto_fixable": auto_fixable,
    }


def _wcag_level(score: float) -> str:
    if score >= 90:
        return "AAA"
    if score >= 75:
        return "AA"
    if score >= 60:
        return "A"
    return "non-compliant"


def _build_recommendations(
    issues: List[Dict[str, Any]],
    require_gemini: bool = False,
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    recommendations: List[Dict[str, Any]] = []
    fallback_count = 0

    for issue in issues:
        remediation = gemini_service.generate_remediation_response(
            issue_description=issue.get("description", ""),
            standard=issue.get("standard", "N/A"),
            require_gemini=require_gemini,
        )
        if remediation.get("fallback_used"):
            fallback_count += 1

        recommendations.append(
            {
                "priority": issue.get("severity", "medium"),
                "action": remediation["text"],
                "benefit": f"Improves alignment with {issue.get('standard', 'accessibility requirements')}.",
                "provider": remediation.get("provider"),
                "model": remediation.get("model"),
                "fallbackUsed": remediation.get("fallback_used", False),
            }
        )
    metadata = {
        "geminiConfigured": bool(gemini_service.api_key),
        "fallbackCount": fallback_count,
        "generatedCount": len(recommendations),
    }
    return recommendations, metadata


def _build_validation_metrics(
    recommendations: List[Dict[str, Any]],
    issues: List[Dict[str, Any]],
) -> Dict[str, Any]:
    if not recommendations:
        return {
            "overallConfidence": 100.0,
            "confidenceLevel": "very_high",
            "recommendation": "No AI-generated remediation output to validate.",
            "fallbackRecommended": False,
            "perIssue": [],
        }

    per_issue = []
    total = 0.0

    for rec, issue in zip(recommendations, issues):
        ai_output = rec.get("action", "")
        fallback = gemini_service._fallback_remediation(
            issue.get("description", ""),
            issue.get("standard", "N/A"),
        )
        validation = ai_validator.validate_output(
            ai_output=ai_output,
            issue_context={
                "description": issue.get("description", ""),
                "standard": issue.get("standard", "N/A"),
            },
            fallback_response=fallback,
        )
        total += validation.overall_score
        per_issue.append(
            {
                "description": issue.get("description", ""),
                "confidenceScore": validation.overall_score,
                "confidenceLevel": validation.confidence_level,
                "fallbackRecommended": validation.fallback_recommended,
                "validationBreakdown": validation.breakdown,
            }
        )

    overall = round(total / len(per_issue), 1)
    confidence_level = ai_validator._determine_level(overall)

    return {
        "overallConfidence": overall,
        "confidenceLevel": confidence_level,
        "recommendation": ai_validator._generate_recommendation(overall),
        "fallbackRecommended": overall < 60,
        "perIssue": per_issue,
    }


def _analyze_document_from_buffer(
    file_buffer: BytesIO,
    filename: str,
    options: Dict[str, Any],
) -> Dict[str, Any]:
    detect_pii = options.get("detectPII", True)
    page_level = options.get("pageLevel", False)
    auto_remediate = options.get("autoRemediate", False)
    validate_ai = options.get("validateAI", True)
    pii_sensitivity = options.get("piiSensitivity", "medium")
    require_gemini_remediation = options.get(
        "requireGeminiRemediation",
        False,
    )
    page_range = _parse_page_range(options.get("pageRange"))

    base = pdf_analyzer.analyze_pdf_buffer(file_buffer, filename)
    issues = [_normalize_issue(issue) for issue in base.get("issues", [])]

    compliance_score = max(0, 100 - base.get("nonCompliancePercent", 100))
    recommendations, recommendation_meta = _build_recommendations(
        issues,
        require_gemini=require_gemini_remediation,
    )

    result: Dict[str, Any] = {
        "documentName": filename,
        "analysisDate": datetime.now(timezone.utc).isoformat(),
        "complianceScore": compliance_score,
        "complianceLevel": base.get("complianceStatus", "non-compliant"),
        "wcagLevel": _wcag_level(compliance_score),
        "totalIssues": len(issues),
        "criticalIssues": sum(1 for issue in issues if issue["severity"] == "critical"),
        "highIssues": sum(1 for issue in issues if issue["severity"] == "high"),
        "mediumIssues": sum(1 for issue in issues if issue["severity"] == "medium"),
        "lowIssues": sum(1 for issue in issues if issue["severity"] == "low"),
        "issues": issues,
        "recommendations": recommendations,
        "remediationMetadata": recommendation_meta,
        "memoryUsage": ephemeral_handler.get_memory_usage(),
    }

    if detect_pii:
        sensitivity = _normalize_pii_sensitivity(pii_sensitivity)
        pii_service = PIIDetector(sensitivity=sensitivity)
        text = _extract_text(file_buffer)
        pii_result = pii_service.detect_pii(text)
        result["piiDetected"] = {
            "detected": pii_result["detected"],
            "totalInstances": pii_result["count"],
            "types": pii_result["categories"],
            "summary": pii_result["summary"],
            "details": pii_result["details"] if pii_sensitivity == "maximum" else None,
        }

    if page_level:
        file_buffer.seek(0)
        page_result = page_processor.analyze_document_by_pages(
            file_buffer=file_buffer,
            filename=filename,
            page_range=page_range,
            parallel=True,
        )
        result["pageAnalyses"] = page_result.get("pageAnalysis", [])
        result["pageSummary"] = {
            "totalPages": page_result.get("totalPages", 0),
            "analyzedPages": page_result.get("analyzedPages", 0),
            "aggregateMetrics": page_result.get("aggregateMetrics", {}),
        }
        result["totalPages"] = page_result.get("totalPages", 0)
    else:
        result["totalPages"] = 0

    if auto_remediate:
        file_buffer.seek(0)
        remediation = remediation_engine.remediate_issues(
            file_buffer=file_buffer,
            filename=filename,
            issues=issues,
        )
        result["remediationResults"] = remediation
        result["autoRemediatedPdfAvailable"] = True
        result["autoRemediatedPdfDownloadEndpoint"] = "/api/v2/remediate/auto/download"
        summary = remediation.get("summary", {})
        result["autoFixable"] = summary.get("autoFixed", 0)
        result["manualFixesRequired"] = summary.get("manualRequired", 0)
    else:
        result["autoRemediatedPdfAvailable"] = False
        result["autoFixable"] = sum(1 for issue in issues if issue.get("auto_fixable"))
        result["manualFixesRequired"] = sum(1 for issue in issues if not issue.get("auto_fixable"))

    if validate_ai:
        result["validationMetrics"] = _build_validation_metrics(recommendations, issues)

    return result


def analyze_document_internal(file_url: str, options: Dict[str, Any]) -> Dict[str, Any]:
    with ephemeral_handler.ephemeral_file_context(file_url) as (file_buffer, filename):
        return _analyze_document_from_buffer(file_buffer, filename, options)


def _run_auto_remediation_with_pdf(
    file_buffer: BytesIO,
    filename: str,
    incoming_issues: Optional[List[Dict[str, Any]]],
) -> Tuple[BytesIO, Dict[str, Any]]:
    if incoming_issues is None:
        analyzed = pdf_analyzer.analyze_pdf_buffer(file_buffer, filename)
        issues = [_normalize_issue(issue) for issue in analyzed.get("issues", [])]
    else:
        issues = [_normalize_issue(issue) for issue in incoming_issues]

    file_buffer.seek(0)
    remediation_result = remediation_engine.remediate_issues(
        file_buffer=file_buffer,
        filename=filename,
        issues=issues,
        include_pdf=True,
    )
    remediated_pdf_buffer = remediation_result.pop("remediatedPdfBuffer", None)
    if remediated_pdf_buffer is None:
        raise RuntimeError("Failed to generate auto-remediated PDF")

    return remediated_pdf_buffer, remediation_result


@api_v2_bp.route("/analyze", methods=["POST"])
def analyze_document():
    try:
        data = request.get_json()
        if not data or "fileUrl" not in data:
            return jsonify({"success": False, "error": "fileUrl is required"}), 400

        result = analyze_document_internal(data["fileUrl"], data.get("options", {}))
        return jsonify({"success": True, **result}), 200
    except Exception as e:
        logger.error(f"Error analyzing document: {e}", exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 500


@api_v2_bp.route("/analyze/upload", methods=["POST"])
def analyze_uploaded_document():
    try:
        file = request.files.get("file")
        if not file or not file.filename:
            return jsonify({"success": False, "error": "file is required"}), 400

        options_payload = request.form.get("options", "{}")
        try:
            options = json.loads(options_payload) if options_payload else {}
        except json.JSONDecodeError:
            return jsonify({"success": False, "error": "options must be valid JSON"}), 400

        file_bytes = file.read()
        if not file_bytes:
            return jsonify({"success": False, "error": "uploaded file is empty"}), 400
        if len(file_bytes) > ephemeral_handler.max_memory_bytes:
            return jsonify({"success": False, "error": "uploaded file exceeds in-memory limit"}), 400

        filename = file.filename
        if not filename.lower().endswith(".pdf"):
            return jsonify({"success": False, "error": "only PDF uploads are supported"}), 400

        result = _analyze_document_from_buffer(BytesIO(file_bytes), filename, options)
        return jsonify({"success": True, **result}), 200
    except Exception as e:
        logger.error(f"Error analyzing uploaded document: {e}", exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 500


@api_v2_bp.route("/analyze/batch", methods=["POST"])
def analyze_batch():
    try:
        data = request.get_json()
        if not data or "fileUrls" not in data:
            return jsonify({"success": False, "error": "fileUrls is required"}), 400

        file_urls = data["fileUrls"]
        if not isinstance(file_urls, list) or not file_urls:
            return jsonify({"success": False, "error": "fileUrls must be a non-empty array"}), 400

        options = data.get("options", {})
        results = []
        for file_url in file_urls:
            try:
                results.append({"success": True, **analyze_document_internal(file_url, options)})
            except Exception as e:
                results.append({"success": False, "fileUrl": file_url, "error": str(e)})

        return jsonify(
            {
                "success": True,
                "totalDocuments": len(file_urls),
                "successfulDocuments": sum(1 for item in results if item.get("success")),
                "results": results,
            }
        ), 200
    except Exception as e:
        logger.error(f"Error in batch analysis: {e}", exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 500


@api_v2_bp.route("/pii/detect", methods=["POST"])
def detect_pii():
    try:
        data = request.get_json()
        if not data or "fileUrl" not in data:
            return jsonify({"success": False, "error": "fileUrl is required"}), 400

        sensitivity = data.get("sensitivity", "medium")
        redact = data.get("redact", False)
        normalized = _normalize_pii_sensitivity(sensitivity)

        with ephemeral_handler.ephemeral_file_context(data["fileUrl"]) as (file_buffer, filename):
            text = _extract_text(file_buffer)
            detector = PIIDetector(sensitivity=normalized)
            result = detector.detect_pii(text)

            response: Dict[str, Any] = {
                "success": True,
                "documentName": filename,
                "detected": result["detected"],
                "totalInstances": result["count"],
                "types": result["categories"],
                "summary": result["summary"],
                "detections": result["details"] if sensitivity == "maximum" else None,
            }
            if redact:
                response["redactedContent"] = detector.redact_pii(text)

            return jsonify(response), 200
    except Exception as e:
        logger.error(f"Error detecting PII: {e}", exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 500


@api_v2_bp.route("/pages/analyze", methods=["POST"])
def analyze_pages():
    try:
        data = request.get_json()
        if not data or "fileUrl" not in data:
            return jsonify({"success": False, "error": "fileUrl is required"}), 400

        page_range = _parse_page_range(data.get("pageRange"))
        with ephemeral_handler.ephemeral_file_context(data["fileUrl"]) as (file_buffer, filename):
            result = page_processor.analyze_document_by_pages(
                file_buffer=file_buffer,
                filename=filename,
                page_range=page_range,
                parallel=True,
            )
            return jsonify({"success": True, **result}), 200
    except Exception as e:
        logger.error(f"Error analyzing pages: {e}", exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 500


@api_v2_bp.route("/scan/pages", methods=["POST"])
def scan_pages_compat():
    """Compatibility endpoint matching the implementation plan path."""
    return analyze_pages()


@api_v2_bp.route("/scan/page/<int:page_number>", methods=["POST"])
def scan_single_page(page_number: int):
    try:
        data = request.get_json()
        if not data or "fileUrl" not in data:
            return jsonify({"success": False, "error": "fileUrl is required"}), 400
        if page_number < 1:
            return jsonify({"success": False, "error": "page_number must be >= 1"}), 400

        with ephemeral_handler.ephemeral_file_context(data["fileUrl"]) as (file_buffer, filename):
            reader = pypdf.PdfReader(file_buffer)
            total_pages = len(reader.pages)
            if page_number > total_pages:
                return jsonify(
                    {
                        "success": False,
                        "error": f"page_number {page_number} exceeds total pages {total_pages}",
                    }
                ), 400

            file_buffer.seek(0)
            page = page_processor.analyze_single_page(
                file_buffer=file_buffer,
                page_number=page_number - 1,
                total_pages=total_pages,
            )
            return jsonify(
                {
                    "success": True,
                    "documentName": filename,
                    "totalPages": total_pages,
                    "page": page,
                }
            ), 200
    except Exception as e:
        logger.error(f"Error analyzing single page: {e}", exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 500


@api_v2_bp.route("/pages/extract", methods=["POST"])
def extract_page():
    try:
        data = request.get_json()
        if not data or "fileUrl" not in data or "pageNumber" not in data:
            return jsonify({"success": False, "error": "fileUrl and pageNumber are required"}), 400

        page_number = int(data["pageNumber"])
        if page_number < 1:
            return jsonify({"success": False, "error": "pageNumber must be >= 1"}), 400

        format_type = data.get("format", "pdf").lower()
        with ephemeral_handler.ephemeral_file_context(data["fileUrl"]) as (file_buffer, _):
            extracted = page_processor.extract_page(
                file_buffer=file_buffer,
                page_number=page_number,
                output_format=format_type,
            )

            if format_type == "pdf":
                return send_file(
                    extracted,
                    mimetype="application/pdf",
                    as_attachment=True,
                    download_name=f"page_{page_number}.pdf",
                )

            payload = extracted.getvalue().decode("utf-8")
            if format_type == "json":
                return jsonify({"success": True, "pageNumber": page_number, "content": json.loads(payload)}), 200
            return jsonify({"success": True, "pageNumber": page_number, "content": payload}), 200
    except Exception as e:
        logger.error(f"Error extracting page: {e}", exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 500


@api_v2_bp.route("/extract/page/<int:page_number>", methods=["POST"])
def extract_page_compat(page_number: int):
    """Compatibility endpoint matching the implementation plan path."""
    try:
        data = request.get_json(silent=True) or {}
        if "fileUrl" not in data:
            return jsonify({"success": False, "error": "fileUrl is required"}), 400

        if page_number < 1:
            return jsonify({"success": False, "error": "page_number must be >= 1"}), 400

        format_type = data.get("format", request.args.get("format", "pdf")).lower()
        with ephemeral_handler.ephemeral_file_context(data["fileUrl"]) as (file_buffer, _):
            extracted = page_processor.extract_page(
                file_buffer=file_buffer,
                page_number=page_number,
                output_format=format_type,
            )

            if format_type == "pdf":
                return send_file(
                    extracted,
                    mimetype="application/pdf",
                    as_attachment=True,
                    download_name=f"page_{page_number}.pdf",
                )

            payload = extracted.getvalue().decode("utf-8")
            if format_type == "json":
                return jsonify({"success": True, "pageNumber": page_number, "content": json.loads(payload)}), 200
            return jsonify({"success": True, "pageNumber": page_number, "content": payload}), 200
    except Exception as e:
        logger.error(f"Error extracting compatibility page endpoint: {e}", exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 500


@api_v2_bp.route("/pages/summary", methods=["POST"])
def pages_summary():
    try:
        data = request.get_json()
        if not data or "fileUrl" not in data:
            return jsonify({"success": False, "error": "fileUrl is required"}), 400

        page_range = _parse_page_range(data.get("pageRange"))
        with ephemeral_handler.ephemeral_file_context(data["fileUrl"]) as (file_buffer, filename):
            result = page_processor.analyze_document_by_pages(
                file_buffer=file_buffer,
                filename=filename,
                page_range=page_range,
                parallel=True,
            )
            metrics = result.get("aggregateMetrics", {})
            summary = {
                "documentName": filename,
                "totalPages": result.get("totalPages", 0),
                "analyzedPages": result.get("analyzedPages", 0),
                "pageRange": result.get("pageRange"),
                "averageComplianceScore": metrics.get("averageComplianceScore", 0),
                "pagesWithPII": metrics.get("pagesWithPII", 0),
                "pagesWithImages": metrics.get("pagesWithImages", 0),
                "pagesWithForms": metrics.get("pagesWithForms", 0),
                "totalIssues": metrics.get("totalIssues", 0),
            }
            return jsonify({"success": True, "summary": summary}), 200
    except Exception as e:
        logger.error(f"Error generating page summary: {e}", exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 500


@api_v2_bp.route("/remediate/auto", methods=["POST"])
def auto_remediate():
    try:
        data = request.get_json()
        if not data or "fileUrl" not in data:
            return jsonify({"success": False, "error": "fileUrl is required"}), 400

        incoming_issues = data.get("issues")
        require_gemini = bool(data.get("requireGemini", False))
        include_ai_guidance = bool(data.get("includeAIGuidance", True))

        with ephemeral_handler.ephemeral_file_context(data["fileUrl"]) as (file_buffer, filename):
            if incoming_issues is None:
                analyzed = pdf_analyzer.analyze_pdf_buffer(file_buffer, filename)
                issues = [_normalize_issue(issue) for issue in analyzed.get("issues", [])]
            else:
                issues = [_normalize_issue(issue) for issue in incoming_issues]

            file_buffer.seek(0)
            result = remediation_engine.remediate_issues(
                file_buffer=file_buffer,
                filename=filename,
                issues=issues,
            )

            if include_ai_guidance:
                ai_guidance = []
                fallback_count = 0
                for issue in issues:
                    remediation = gemini_service.generate_remediation_response(
                        issue_description=issue.get("description", ""),
                        standard=issue.get("standard", "N/A"),
                        require_gemini=require_gemini,
                    )
                    if remediation.get("fallback_used"):
                        fallback_count += 1
                    ai_guidance.append(
                        {
                            "description": issue.get("description", ""),
                            "standard": issue.get("standard", "N/A"),
                            "guidance": remediation["text"],
                            "provider": remediation.get("provider"),
                            "model": remediation.get("model"),
                            "fallbackUsed": remediation.get("fallback_used", False),
                        }
                    )
                result["aiGuidance"] = ai_guidance
                result["aiGuidanceMetadata"] = {
                    "geminiConfigured": bool(gemini_service.api_key),
                    "generatedCount": len(ai_guidance),
                    "fallbackCount": fallback_count,
                }

            return jsonify({"success": True, **result}), 200
    except Exception as e:
        logger.error(f"Error in auto-remediation: {e}", exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 500


@api_v2_bp.route("/remediate/auto/download", methods=["POST"])
def download_auto_remediated_pdf():
    try:
        uploaded_file = request.files.get("file")

        if uploaded_file:
            if not uploaded_file.filename:
                return jsonify({"success": False, "error": "file is required"}), 400

            issues_payload = request.form.get("issues")
            incoming_issues = None
            if issues_payload:
                try:
                    parsed_issues = json.loads(issues_payload)
                except json.JSONDecodeError:
                    return jsonify({"success": False, "error": "issues must be valid JSON"}), 400
                if not isinstance(parsed_issues, list):
                    return jsonify({"success": False, "error": "issues must be an array"}), 400
                incoming_issues = parsed_issues

            file_bytes = uploaded_file.read()
            if not file_bytes:
                return jsonify({"success": False, "error": "uploaded file is empty"}), 400
            if len(file_bytes) > ephemeral_handler.max_memory_bytes:
                return jsonify({"success": False, "error": "uploaded file exceeds in-memory limit"}), 400

            filename = uploaded_file.filename
            if not filename.lower().endswith(".pdf"):
                return jsonify({"success": False, "error": "only PDF uploads are supported"}), 400

            remediated_pdf_buffer, _ = _run_auto_remediation_with_pdf(
                file_buffer=BytesIO(file_bytes),
                filename=filename,
                incoming_issues=incoming_issues,
            )
        else:
            data = request.get_json(silent=True)
            if not data or "fileUrl" not in data:
                return jsonify({"success": False, "error": "file or fileUrl is required"}), 400

            incoming_issues = data.get("issues")
            if incoming_issues is not None and not isinstance(incoming_issues, list):
                return jsonify({"success": False, "error": "issues must be an array"}), 400

            with ephemeral_handler.ephemeral_file_context(data["fileUrl"]) as (file_buffer, filename):
                remediated_pdf_buffer, _ = _run_auto_remediation_with_pdf(
                    file_buffer=file_buffer,
                    filename=filename,
                    incoming_issues=incoming_issues,
                )

        return send_file(
            remediated_pdf_buffer,
            mimetype="application/pdf",
            as_attachment=True,
            download_name=_auto_remediated_download_name(filename),
        )
    except Exception as e:
        logger.error(f"Error generating auto-remediated download: {e}", exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 500


@api_v2_bp.route("/remediate/guidance", methods=["POST"])
def get_remediation_guidance():
    try:
        data = request.get_json()
        if not data or "issueType" not in data:
            return jsonify({"success": False, "error": "issueType is required"}), 400

        issue_type = data["issueType"]
        issue_description = data.get("issueDescription", issue_type)
        require_gemini = bool(data.get("requireGemini", False))

        guidance = remediation_engine.get_user_action_template(issue_type)
        if not guidance:
            guidance = remediation_engine._generate_user_action(
                issue_type=issue_type,
                issue={"description": issue_description},
            )

        gemini_guidance = gemini_service.generate_remediation_response(
            issue_description=issue_description,
            standard=data.get("standard", "WCAG 2.1"),
            require_gemini=require_gemini,
        )

        return jsonify(
            {
                "success": True,
                "guidance": asdict(guidance),
                "aiGuidance": gemini_guidance["text"],
                "aiProvider": gemini_guidance.get("provider"),
                "aiModel": gemini_guidance.get("model"),
                "fallbackUsed": gemini_guidance.get("fallback_used", False),
            }
        ), 200
    except Exception as e:
        logger.error(f"Error getting remediation guidance: {e}", exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 500


@api_v2_bp.route("/reports/generate", methods=["POST"])
def generate_report():
    try:
        data = request.get_json()
        if not data or "analysisData" not in data:
            return jsonify({"success": False, "error": "analysisData is required"}), 400

        analysis_data = data["analysisData"]
        format_type = data.get("format", "html")
        sections = data.get(
            "sections",
            [
                "executive_summary",
                "compliance_overview",
                "issue_details",
                "remediation_plan",
                "recommendations",
            ],
        )

        parsed_sections = []
        for section in sections:
            enum_name = str(section).upper().replace("-", "_")
            if enum_name in ReportSection.__members__:
                parsed_sections.append(ReportSection[enum_name])
        if not parsed_sections:
            parsed_sections = [
                ReportSection.EXECUTIVE_SUMMARY,
                ReportSection.COMPLIANCE_OVERVIEW,
                ReportSection.ISSUE_DETAILS,
                ReportSection.RECOMMENDATIONS,
            ]

        report_data = ComplianceReport(
            document_name=analysis_data.get("documentName", "Unknown"),
            analysis_date=datetime.fromisoformat(
                analysis_data.get("analysisDate", datetime.now(timezone.utc).isoformat())
            ),
            compliance_score=float(analysis_data.get("complianceScore", 0)),
            compliance_level=analysis_data.get("complianceLevel", "none"),
            wcag_level=analysis_data.get("wcagLevel", "non-compliant"),
            total_pages=int(analysis_data.get("totalPages", 0)),
            total_issues=int(analysis_data.get("totalIssues", 0)),
            critical_issues=int(analysis_data.get("criticalIssues", 0)),
            high_issues=int(analysis_data.get("highIssues", 0)),
            medium_issues=int(analysis_data.get("mediumIssues", 0)),
            low_issues=int(analysis_data.get("lowIssues", 0)),
            auto_fixable=int(analysis_data.get("autoFixable", 0)),
            manual_fixes_required=int(analysis_data.get("manualFixesRequired", 0)),
            issues=analysis_data.get("issues", []),
            recommendations=analysis_data.get("recommendations", []),
            page_analyses=analysis_data.get("pageAnalyses"),
            pii_summary=analysis_data.get("piiDetected"),
            validation_metrics=analysis_data.get("validationMetrics"),
        )

        branding = data.get("branding") or {}
        branding_config = {
            "company_name": branding.get("companyName"),
            "logo_url": branding.get("logoUrl"),
            "primary_color": branding.get("primaryColor"),
        }

        report_format = ReportFormat[format_type.upper()]
        config = ReportConfig(
            format=report_format,
            include_sections=parsed_sections,
            branding={k: v for k, v in branding_config.items() if v},
            include_pii_details=bool(data.get("includePiiDetails", False)),
        )

        report_output = report_generator.generate_report(report_data=report_data, config=config)

        if report_format == ReportFormat.JSON:
            return jsonify({"success": True, "report": json.loads(report_output.getvalue().decode("utf-8"))}), 200

        mimetypes = {
            ReportFormat.PDF: "application/pdf",
            ReportFormat.HTML: "text/html",
            ReportFormat.CSV: "text/csv",
            ReportFormat.MARKDOWN: "text/markdown",
        }
        return send_file(
            report_output,
            mimetype=mimetypes.get(report_format, "application/octet-stream"),
            as_attachment=True,
            download_name=f"compliance_report.{report_format.value}",
        )
    except Exception as e:
        logger.error(f"Error generating report: {e}", exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 500


@api_v2_bp.route("/validation/check", methods=["POST"])
def validate_analysis():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "request body is required"}), 400

        ai_output = data.get("aiOutput")
        analysis_result = data.get("analysisResult")
        if ai_output is None and analysis_result is None:
            return jsonify({"success": False, "error": "aiOutput or analysisResult is required"}), 400

        if ai_output is None:
            ai_output = json.dumps(analysis_result, default=str)

        context = data.get("context", {})
        fallback_response = data.get("fallbackResponse") or ai_output

        validation_result = ai_validator.validate_output(
            ai_output=ai_output,
            issue_context=context,
            fallback_response=fallback_response,
        )

        return jsonify(
            {
                "success": True,
                "overallConfidence": validation_result.overall_score,
                "confidenceLevel": validation_result.confidence_level,
                "layerScores": validation_result.breakdown,
                "recommendation": validation_result.recommendation,
                "fallbackRecommended": validation_result.fallback_recommended,
            }
        ), 200
    except Exception as e:
        logger.error(f"Error validating analysis: {e}", exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 500


@api_v2_bp.route("/prompts/performance", methods=["GET"])
def get_prompt_performance():
    try:
        prompt_name = request.args.get("promptName")
        report = prompt_manager.get_performance_report(prompt_name)
        return jsonify({"success": True, "report": report}), 200
    except Exception as e:
        logger.error(f"Error getting prompt performance: {e}", exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 500
