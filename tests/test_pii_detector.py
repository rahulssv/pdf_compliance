"""Unit tests for PII detection service."""

from src.services.pii_detector import PIIDetector
from src.utils.pii_patterns import PIIPatterns, mask_pii


def test_detects_multiple_pii_types():
    detector = PIIDetector(sensitivity="high")
    text = """
    Contact John Doe at john.doe@example.com or +1 (555) 123-4567.
    SSN: 123-45-6789
    Card: 4532-1234-5678-9010
    """

    result = detector.detect_pii(text)

    assert result["detected"] is True
    assert result["count"] >= 4
    assert "EMAIL" in result["categories"]
    assert "SSN" in result["categories"]


def test_returns_empty_result_for_no_pii():
    detector = PIIDetector(sensitivity="high")
    result = detector.detect_pii("This sentence contains no sensitive data.")

    assert result["detected"] is False
    assert result["count"] == 0
    assert result["details"] == []


def test_redaction_masks_values():
    detector = PIIDetector(sensitivity="high")
    text = "Email: john.doe@example.com, SSN: 123-45-6789"

    redacted = detector.redact_pii(text)

    assert "john.doe@example.com" not in redacted
    assert "123-45-6789" not in redacted
    assert "***" in redacted


def test_sensitivity_controls_pattern_count():
    text = "Contact at john.doe@example.com and zip 90210"
    high = PIIDetector(sensitivity="high").detect_pii(text)
    medium = PIIDetector(sensitivity="medium").detect_pii(text)
    low = PIIDetector(sensitivity="low").detect_pii(text)

    assert high["count"] >= medium["count"] >= low["count"]


def test_statistics_shape_and_values():
    detector = PIIDetector(sensitivity="medium")
    stats = detector.get_statistics()

    assert stats["sensitivity"] == "medium"
    assert stats["active_patterns"] > 0
    assert "patterns_by_category" in stats


def test_pattern_library_has_required_categories():
    patterns = PIIPatterns.get_all_patterns()
    categories = {pattern.category for pattern in patterns}

    assert {"financial", "personal", "medical", "government", "technical"}.issubset(categories)


def test_mask_pii_preserves_last4_when_available():
    masked = mask_pii("123-45-6789", PIIPatterns.SSN)
    assert masked.endswith("6789")
    assert "123-45" not in masked
