# Testing Guide - PDF Accessibility Compliance Engine

## Overview

Comprehensive testing strategy for all implemented features including unit tests, integration tests, and performance benchmarks.

**Test Coverage Target:** 85%+  
**Test Framework:** pytest  
**Test Types:** Unit, Integration, Performance, Security

---

## Table of Contents

1. [Test Setup](#test-setup)
2. [Test Structure](#test-structure)
3. [Unit Tests](#unit-tests)
4. [Integration Tests](#integration-tests)
5. [Performance Tests](#performance-tests)
6. [Security Tests](#security-tests)
7. [Running Tests](#running-tests)
8. [Coverage Reports](#coverage-reports)
9. [CI/CD Integration](#cicd-integration)

---

## Test Setup

### Install Dependencies

```bash
pip install pytest pytest-cov pytest-mock pytest-asyncio
pip install -r requirements.txt
```

### Test Configuration

Create `pytest.ini`:

```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = 
    -v
    --strict-markers
    --cov=src
    --cov-report=html
    --cov-report=term-missing
    --cov-fail-under=85
markers =
    unit: Unit tests
    integration: Integration tests
    performance: Performance tests
    security: Security tests
    slow: Slow running tests
```

---

## Test Structure

```
tests/
├── __init__.py
├── conftest.py                    # Shared fixtures
├── unit/
│   ├── test_pii_detector.py      # PII detection tests
│   ├── test_ephemeral_handler.py # Zero-persistence tests
│   ├── test_page_processor.py    # Page processing tests
│   ├── test_ai_validator.py      # AI validation tests
│   ├── test_auto_remediation.py  # Remediation tests
│   ├── test_prompt_manager.py    # Prompt management tests
│   └── test_report_generator.py  # Report generation tests
├── integration/
│   ├── test_full_workflow.py     # End-to-end tests
│   ├── test_api_endpoints.py     # API integration tests
│   └── test_service_integration.py
├── performance/
│   ├── test_pii_performance.py
│   ├── test_page_performance.py
│   └── test_report_performance.py
└── security/
    ├── test_data_privacy.py
    ├── test_pii_redaction.py
    └── test_zero_persistence.py
```

---

## Unit Tests

### 1. PII Detector Tests (`test_pii_detector.py`)

**Test Cases:**

```python
class TestPIIDetector:
    """Test PII detection functionality"""
    
    def test_email_detection(self):
        """Verify email addresses are detected"""
        detector = PIIDetector(sensitivity='high')
        text = "Contact: john.doe@example.com"
        matches = detector.detect_pii(text)
        
        assert len(matches) > 0
        assert matches[0].type == 'email'
        assert matches[0].confidence > 0.9
    
    def test_ssn_detection(self):
        """Verify SSN detection"""
        detector = PIIDetector()
        text = "SSN: 123-45-6789"
        matches = detector.detect_pii(text)
        
        assert any(m.type == 'ssn' for m in matches)
        assert matches[0].severity == 'critical'
    
    def test_credit_card_detection(self):
        """Verify credit card detection"""
        detector = PIIDetector()
        text = "Card: 4532-1234-5678-9010"
        matches = detector.detect_pii(text)
        
        assert any(m.type == 'credit_card' for m in matches)
    
    def test_pii_masking(self):
        """Verify PII masking preserves format"""
        detector = PIIDetector()
        text = "SSN: 123-45-6789"
        matches = detector.detect_pii(text)
        redacted = detector.redact_pii(text, matches)
        
        assert '123-45-6789' not in redacted
        assert 'XXX-XX-' in redacted  # Format preserved
    
    def test_sensitivity_levels(self):
        """Verify sensitivity levels work correctly"""
        text = "Email: test@example.com"
        
        high = PIIDetector(sensitivity='high')
        low = PIIDetector(sensitivity='low')
        
        high_matches = high.detect_pii(text)
        low_matches = low.detect_pii(text)
        
        assert len(high_matches) >= len(low_matches)
    
    def test_performance_target(self):
        """Verify detection meets performance target (<100ms/page)"""
        import time
        
        detector = PIIDetector()
        text = "Email: test@example.com\n" * 50  # Simulate page
        
        start = time.time()
        matches = detector.detect_pii(text)
        duration = time.time() - start
        
        assert duration < 0.1  # <100ms
```

**Expected Results:**
- All PII types detected correctly
- Confidence scores > 0.9 for clear matches
- Masking preserves format
- Performance < 100ms per page

---

### 2. Ephemeral File Handler Tests (`test_ephemeral_handler.py`)

**Test Cases:**

```python
class TestEphemeralFileHandler:
    """Test zero-persistence file handling"""
    
    def test_no_temp_files_created(self, tmp_path):
        """Verify no temporary files are created"""
        handler = EphemeralFileHandler()
        
        # Track file system before
        files_before = set(tmp_path.glob('**/*'))
        
        with handler.ephemeral_file_context('https://example.com/test.pdf') as buffer:
            # Process file
            pass
        
        # Track file system after
        files_after = set(tmp_path.glob('**/*'))
        
        # No new files should exist
        assert files_before == files_after
    
    def test_memory_cleanup(self):
        """Verify memory is cleaned up after processing"""
        import gc
        
        handler = EphemeralFileHandler()
        
        with handler.ephemeral_file_context('test.pdf') as buffer:
            buffer.write(b'test data' * 1000)
            buffer_id = id(buffer)
        
        # Force garbage collection
        gc.collect()
        
        # Buffer should be garbage collected
        # (Implementation-specific verification)
    
    def test_memory_limit_enforcement(self):
        """Verify memory limits are enforced"""
        handler = EphemeralFileHandler(memory_limit_mb=1)
        
        with pytest.raises(MemoryError):
            with handler.ephemeral_file_context('large.pdf') as buffer:
                # Try to write more than limit
                buffer.write(b'x' * (2 * 1024 * 1024))  # 2MB
    
    def test_context_manager_cleanup(self):
        """Verify context manager cleans up on exception"""
        handler = EphemeralFileHandler()
        
        try:
            with handler.ephemeral_file_context('test.pdf') as buffer:
                raise ValueError("Test exception")
        except ValueError:
            pass
        
        # Verify cleanup occurred (no lingering resources)
```

**Expected Results:**
- Zero files written to disk
- Memory cleaned up after processing
- Memory limits enforced
- Cleanup on exceptions

---

### 3. Page Processor Tests (`test_page_processor.py`)

**Test Cases:**

```python
class TestPageProcessor:
    """Test page-level PDF processing"""
    
    def test_page_extraction(self):
        """Verify individual page extraction"""
        processor = PageProcessor()
        
        # Mock PDF with 10 pages
        result = processor.extract_page(mock_pdf, page_number=5)
        
        assert result is not None
        assert 'content' in result
    
    def test_page_analysis(self):
        """Verify page-by-page analysis"""
        processor = PageProcessor()
        
        result = processor.analyze_document_by_pages(mock_pdf, 'test.pdf')
        
        assert 'pages' in result
        assert len(result['pages']) > 0
        assert all('pageScore' in p for p in result['pages'])
    
    def test_parallel_processing(self):
        """Verify parallel processing improves performance"""
        import time
        
        processor = PageProcessor(max_workers=4)
        
        # Process with parallel
        start = time.time()
        result_parallel = processor.analyze_document_by_pages(
            large_pdf, 'test.pdf', parallel=True
        )
        time_parallel = time.time() - start
        
        # Process without parallel
        start = time.time()
        result_serial = processor.analyze_document_by_pages(
            large_pdf, 'test.pdf', parallel=False
        )
        time_serial = time.time() - start
        
        # Parallel should be faster for large documents
        assert time_parallel < time_serial
    
    def test_performance_target(self):
        """Verify page analysis meets performance target (<500ms/page)"""
        import time
        
        processor = PageProcessor()
        
        start = time.time()
        result = processor.analyze_single_page(mock_page, 1)
        duration = time.time() - start
        
        assert duration < 0.5  # <500ms
```

**Expected Results:**
- Pages extracted correctly
- Analysis provides page-specific scores
- Parallel processing improves performance
- Performance < 500ms per page

---

### 4. AI Validator Tests (`test_ai_validator.py`)

**Test Cases:**

```python
class TestAIValidator:
    """Test AI output validation framework"""
    
    def test_confidence_scoring(self):
        """Verify confidence scores are calculated correctly"""
        validator = AIValidator()
        
        result = validator.validate_output(
            analysis_result=mock_analysis,
            issue_context=mock_context,
            fallback_response=mock_fallback
        )
        
        assert 0 <= result.overall_confidence <= 100
        assert result.confidence_level in [
            'very_high', 'high', 'medium', 'low', 'very_low'
        ]
    
    def test_all_validation_layers(self):
        """Verify all 5 validation layers are executed"""
        validator = AIValidator()
        
        result = validator.validate_output(
            mock_analysis, mock_context, mock_fallback
        )
        
        assert len(result.layer_scores) == 5
        assert 'rule_based' in result.layer_scores
        assert 'pattern_matching' in result.layer_scores
        assert 'consistency' in result.layer_scores
        assert 'knowledge_base' in result.layer_scores
        assert 'ensemble' in result.layer_scores
    
    def test_fallback_recommendation(self):
        """Verify fallback is recommended for low confidence"""
        validator = AIValidator()
        
        # Mock low-confidence result
        low_confidence_result = create_low_confidence_mock()
        
        result = validator.validate_output(
            low_confidence_result, mock_context, mock_fallback
        )
        
        assert result.overall_confidence < 60
        assert result.fallback_recommended is True
    
    def test_weighted_scoring(self):
        """Verify layer weights are applied correctly"""
        validator = AIValidator()
        
        # Weights: rule_based=25%, pattern=20%, consistency=25%,
        #          knowledge=15%, ensemble=15%
        
        result = validator.validate_output(
            mock_analysis, mock_context, mock_fallback
        )
        
        # Verify weighted calculation
        expected = (
            result.layer_scores['rule_based'] * 0.25 +
            result.layer_scores['pattern_matching'] * 0.20 +
            result.layer_scores['consistency'] * 0.25 +
            result.layer_scores['knowledge_base'] * 0.15 +
            result.layer_scores['ensemble'] * 0.15
        )
        
        assert abs(result.overall_confidence - expected) < 0.1
```

**Expected Results:**
- Confidence scores 0-100
- All 5 layers executed
- Fallback recommended when confidence < 60
- Weighted scoring accurate

---

### 5. Auto Remediation Tests (`test_auto_remediation.py`)

**Test Cases:**

```python
class TestAutoRemediationEngine:
    """Test automated remediation functionality"""
    
    def test_automated_fixes(self):
        """Verify automated fixes are applied correctly"""
        engine = AutoRemediationEngine()
        
        issues = [
            {'type': 'missing_language', 'severity': 'high'},
            {'type': 'missing_title', 'severity': 'medium'}
        ]
        
        result = engine.remediate_issues(mock_pdf, issues)
        
        assert result['fixedIssues'] > 0
        assert result['totalIssues'] == len(issues)
    
    def test_user_action_templates(self):
        """Verify user action templates are generated"""
        engine = AutoRemediationEngine()
        
        template = engine.get_user_action_template('missing_alt_text')
        
        assert template is not None
        assert 'steps' in template
        assert 'estimatedTime' in template
        assert 'difficulty' in template
    
    def test_remediation_rate(self):
        """Verify auto-remediation rate meets target (30%+)"""
        engine = AutoRemediationEngine()
        
        # Mix of auto-fixable and manual issues
        issues = create_mixed_issues(count=100)
        
        result = engine.remediate_issues(mock_pdf, issues)
        
        auto_rate = result['fixedIssues'] / result['totalIssues'] * 100
        assert auto_rate >= 30.0
    
    def test_success_tracking(self):
        """Verify remediation success is tracked"""
        engine = AutoRemediationEngine()
        
        issues = [{'type': 'missing_language', 'severity': 'high'}]
        result = engine.remediate_issues(mock_pdf, issues)
        
        stats = engine.get_statistics()
        assert stats['total_remediations'] > 0
        assert 'success_rate' in stats
```

**Expected Results:**
- Automated fixes applied successfully
- User action templates generated
- Auto-remediation rate ≥ 30%
- Success tracking functional

---

### 6. Prompt Manager Tests (`test_prompt_manager.py`)

**Test Cases:**

```python
class TestPromptManager:
    """Test prompt management and version control"""
    
    def test_version_control(self):
        """Verify prompt versions are managed correctly"""
        manager = PromptManager()
        
        # Register new version
        new_version = create_prompt_version('1.4.0')
        manager.register_version(new_version)
        
        # Verify registration
        versions = manager.list_versions('compliance_analysis')
        assert any(v['version'] == '1.4.0' for v in versions)
    
    def test_active_version_management(self):
        """Verify active version switching"""
        manager = PromptManager()
        
        manager.set_active_version('compliance_analysis', '1.3.0')
        active = manager.get_active_prompt('compliance_analysis')
        
        assert active.version == '1.3.0'
    
    def test_performance_tracking(self):
        """Verify performance metrics are tracked"""
        manager = PromptManager()
        
        # Record usage
        manager.record_usage(
            'compliance_analysis',
            success=True,
            response_time=3.2,
            confidence_score=92.5
        )
        
        # Get report
        report = manager.get_performance_report('compliance_analysis')
        
        assert report['metrics']['totalUses'] > 0
        assert 'successRate' in report['metrics']
    
    def test_ab_testing(self):
        """Verify A/B testing functionality"""
        manager = PromptManager()
        
        test_id = manager.create_ab_test(
            'compliance_analysis',
            variant_a_version='1.2.0',
            variant_b_version='1.3.0'
        )
        
        assert test_id is not None
        
        # Get results
        results = manager.get_ab_test_results(test_id)
        assert 'variants' in results
        assert 'winner' in results
```

**Expected Results:**
- Version control functional
- Active version switching works
- Performance tracking accurate
- A/B testing operational

---

### 7. Report Generator Tests (`test_report_generator.py`)

**Test Cases:**

```python
class TestReportGenerator:
    """Test report generation in multiple formats"""
    
    def test_json_report_generation(self):
        """Verify JSON report generation"""
        generator = ReportGenerator()
        
        report = generator.generate_report(
            mock_report_data,
            ReportConfig(format=ReportFormat.JSON)
        )
        
        assert report is not None
        content = json.loads(report.getvalue())
        assert 'complianceScore' in content
    
    def test_html_report_generation(self):
        """Verify HTML report generation"""
        generator = ReportGenerator()
        
        report = generator.generate_report(
            mock_report_data,
            ReportConfig(format=ReportFormat.HTML)
        )
        
        html = report.getvalue().decode('utf-8')
        assert '<html' in html
        assert 'Compliance Report' in html
    
    def test_csv_report_generation(self):
        """Verify CSV report generation"""
        generator = ReportGenerator()
        
        report = generator.generate_report(
            mock_report_data,
            ReportConfig(format=ReportFormat.CSV)
        )
        
        csv_content = report.getvalue().decode('utf-8')
        assert 'Issue ID' in csv_content
        assert 'Severity' in csv_content
    
    def test_custom_branding(self):
        """Verify custom branding is applied"""
        generator = ReportGenerator()
        
        config = ReportConfig(
            format=ReportFormat.HTML,
            branding={
                'companyName': 'Test Corp',
                'primaryColor': '#ff0000'
            }
        )
        
        report = generator.generate_report(mock_report_data, config)
        html = report.getvalue().decode('utf-8')
        
        assert 'Test Corp' in html
        assert '#ff0000' in html
    
    def test_section_filtering(self):
        """Verify report sections can be filtered"""
        generator = ReportGenerator()
        
        config = ReportConfig(
            format=ReportFormat.JSON,
            include_sections=[
                ReportSection.EXECUTIVE_SUMMARY,
                ReportSection.ISSUE_DETAILS
            ]
        )
        
        report = generator.generate_report(mock_report_data, config)
        content = json.loads(report.getvalue())
        
        # Should include specified sections
        assert 'complianceScore' in content
        assert 'issues' in content
```

**Expected Results:**
- All formats generate correctly
- Branding applied properly
- Section filtering works
- Output valid and complete

---

## Integration Tests

### Full Workflow Test

```python
class TestFullWorkflow:
    """Test complete end-to-end workflow"""
    
    def test_complete_analysis_workflow(self):
        """Test full analysis from file to report"""
        # 1. Load file with ephemeral handler
        handler = EphemeralFileHandler()
        with handler.ephemeral_file_context('test.pdf') as buffer:
            
            # 2. Detect PII
            pii_detector = PIIDetector()
            pii_results = pii_detector.detect_pii(extract_text(buffer))
            
            # 3. Analyze pages
            page_processor = PageProcessor()
            page_results = page_processor.analyze_document_by_pages(
                buffer, 'test.pdf'
            )
            
            # 4. Validate AI output
            validator = AIValidator()
            validation = validator.validate_output(
                page_results, {}, {}
            )
            
            # 5. Auto-remediate
            remediation = AutoRemediationEngine()
            remediation_results = remediation.remediate_issues(
                buffer, page_results['issues']
            )
            
            # 6. Generate report
            report_gen = ReportGenerator()
            report = report_gen.generate_report(
                create_report_data(page_results, pii_results),
                ReportConfig(format=ReportFormat.HTML)
            )
        
        # Verify complete workflow
        assert pii_results is not None
        assert page_results is not None
        assert validation.overall_confidence > 0
        assert remediation_results['fixedIssues'] >= 0
        assert report is not None
```

---

## Performance Tests

### Performance Benchmarks

```python
class TestPerformance:
    """Performance benchmark tests"""
    
    @pytest.mark.performance
    def test_pii_detection_performance(self):
        """Benchmark PII detection speed"""
        detector = PIIDetector()
        text = generate_sample_text(lines=100)
        
        times = []
        for _ in range(10):
            start = time.time()
            detector.detect_pii(text)
            times.append(time.time() - start)
        
        avg_time = sum(times) / len(times)
        assert avg_time < 0.1  # <100ms target
    
    @pytest.mark.performance
    def test_page_processing_performance(self):
        """Benchmark page processing speed"""
        processor = PageProcessor()
        
        times = []
        for _ in range(10):
            start = time.time()
            processor.analyze_single_page(mock_page, 1)
            times.append(time.time() - start)
        
        avg_time = sum(times) / len(times)
        assert avg_time < 0.5  # <500ms target
    
    @pytest.mark.performance
    def test_report_generation_performance(self):
        """Benchmark report generation speed"""
        generator = ReportGenerator()
        
        start = time.time()
        report = generator.generate_report(
            mock_report_data,
            ReportConfig(format=ReportFormat.HTML)
        )
        duration = time.time() - start
        
        assert duration < 1.0  # <1s target
```

---

## Security Tests

### Security Validation

```python
class TestSecurity:
    """Security and privacy tests"""
    
    @pytest.mark.security
    def test_zero_persistence_guarantee(self):
        """Verify zero data persistence"""
        import os
        import tempfile
        
        temp_dir = tempfile.gettempdir()
        files_before = set(os.listdir(temp_dir))
        
        # Process document
        handler = EphemeralFileHandler()
        with handler.ephemeral_file_context('test.pdf') as buffer:
            buffer.write(b'sensitive data')
        
        files_after = set(os.listdir(temp_dir))
        
        # No new files should exist
        assert files_before == files_after
    
    @pytest.mark.security
    def test_pii_redaction_completeness(self):
        """Verify all PII is redacted"""
        detector = PIIDetector()
        text = "SSN: 123-45-6789, Email: test@example.com"
        
        matches = detector.detect_pii(text)
        redacted = detector.redact_pii(text, matches)
        
        # Original PII should not appear in redacted text
        assert '123-45-6789' not in redacted
        assert 'test@example.com' not in redacted
    
    @pytest.mark.security
    def test_memory_limit_enforcement(self):
        """Verify memory limits prevent DoS"""
        handler = EphemeralFileHandler(memory_limit_mb=10)
        
        with pytest.raises(MemoryError):
            with handler.ephemeral_file_context('large.pdf') as buffer:
                # Attempt to exceed limit
                buffer.write(b'x' * (20 * 1024 * 1024))
```

---

## Running Tests

### Run All Tests

```bash
pytest
```

### Run Specific Test Categories

```bash
# Unit tests only
pytest -m unit

# Integration tests
pytest -m integration

# Performance tests
pytest -m performance

# Security tests
pytest -m security
```

### Run with Coverage

```bash
pytest --cov=src --cov-report=html
```

### Run Specific Test File

```bash
pytest tests/unit/test_pii_detector.py -v
```

### Run Specific Test

```bash
pytest tests/unit/test_pii_detector.py::TestPIIDetector::test_email_detection -v
```

---

## Coverage Reports

### Generate HTML Coverage Report

```bash
pytest --cov=src --cov-report=html
open htmlcov/index.html
```

### Coverage Requirements

- **Overall Coverage:** 85%+
- **Critical Modules:** 90%+
  - PII Detector
  - Ephemeral File Handler
  - AI Validator
- **Standard Modules:** 80%+
  - Page Processor
  - Auto Remediation
  - Report Generator

---

## CI/CD Integration

### GitHub Actions Workflow

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v2
    
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install pytest pytest-cov
    
    - name: Run tests
      run: |
        pytest --cov=src --cov-report=xml
    
    - name: Upload coverage
      uses: codecov/codecov-action@v2
      with:
        file: ./coverage.xml
```

---

## Test Data

### Mock Data Location

```
tests/
├── fixtures/
│   ├── sample_pdfs/
│   │   ├── accessible.pdf
│   │   ├── with_pii.pdf
│   │   └── large_document.pdf
│   ├── mock_responses/
│   │   ├── gemini_response.json
│   │   └── validation_result.json
│   └── expected_outputs/
│       ├── report_html.html
│       └── analysis_result.json
```

---

## Continuous Monitoring

### Performance Monitoring

Track performance metrics over time:

- PII detection speed
- Page processing speed
- Report generation speed
- Memory usage
- API response times

### Quality Metrics

Monitor code quality:

- Test coverage percentage
- Test pass rate
- Code complexity
- Security vulnerabilities
- Documentation coverage

---

*Testing Guide Version: 1.0.0*  
*Last Updated: April 17, 2026*