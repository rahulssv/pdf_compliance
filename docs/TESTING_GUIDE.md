# Testing Guide

## Run all tests

```bash
pytest -q
```

## Run a specific test file

```bash
pytest -q tests/test_api_v2.py
```

## Run a single test

```bash
pytest -q tests/test_api_v2.py::test_download_auto_remediated_pdf_from_upload
```

## Smoke test (without pytest)

1. Start app (`docker compose up --build -d` or local run).
2. Verify health:

```bash
curl http://localhost:8000/health
```

3. Open UI:

```text
http://localhost:8000/
```

4. Upload a PDF and run analysis.
5. Enable **Auto-remediate** and confirm **Download Auto-remediated PDF** works.

## API smoke examples

### Analyze upload

```bash
curl -X POST http://localhost:8000/api/v2/analyze/upload \
  -F "file=@/absolute/path/sample.pdf" \
  -F 'options={"detectPII":true,"pageLevel":false,"autoRemediate":true,"validateAI":true}'
```

### Download auto-remediated PDF

```bash
curl -X POST http://localhost:8000/api/v2/remediate/auto/download \
  -F "file=@/absolute/path/sample.pdf" \
  -F 'issues=[{"description":"Document language is not declared at the document level.","standard":"WCAG 2.1 SC 3.1.1"}]' \
  --output sample_auto_remediated.pdf
```

## Notes

- The repository enforces coverage via `pytest.ini`.
- Some warnings may appear from third-party dependencies; they do not automatically indicate endpoint failure.
