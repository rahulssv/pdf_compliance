# API v2 Specification

Base prefix: **`/api/v2`**

This document reflects the currently implemented v2 routes and request/response behavior.

## 1. Analysis

### `POST /api/v2/analyze`

Analyze a PDF using `fileUrl` (local path, `file://`, or HTTP/HTTPS URL supported by the file handler).

Request:

```json
{
  "fileUrl": "/absolute/path/or/url/to/file.pdf",
  "options": {
    "detectPII": true,
    "piiSensitivity": "medium",
    "pageLevel": false,
    "autoRemediate": false,
    "validateAI": true,
    "requireGeminiRemediation": false
  }
}
```

Response (success):

- `success`
- document-level compliance metrics
- `issues`
- `recommendations`
- optional: `piiDetected`, `pageAnalyses`, `pageSummary`, `validationMetrics`
- if `autoRemediate=true`: `remediationResults`, `autoRemediatedPdfAvailable`, `autoRemediatedPdfDownloadEndpoint`

### `POST /api/v2/analyze/upload`

Multipart upload analysis.

Form fields:

- `file` (required, PDF)
- `options` (optional JSON string)

### `POST /api/v2/analyze/batch`

Batch analyze multiple file URLs.

```json
{
  "fileUrls": ["/path/a.pdf", "/path/b.pdf"],
  "options": {}
}
```

## 2. PII

### `POST /api/v2/pii/detect`

```json
{
  "fileUrl": "/path/file.pdf",
  "sensitivity": "medium",
  "redact": false
}
```

Returns detection summary and optional `redactedContent` when `redact=true`.

## 3. Page-level endpoints

- `POST /api/v2/pages/analyze`
- `POST /api/v2/scan/pages` (compat alias)
- `POST /api/v2/scan/page/<page_number>`
- `POST /api/v2/pages/extract`
- `POST /api/v2/extract/page/<page_number>` (compat alias)
- `POST /api/v2/pages/summary`

Notes:

- `pages/extract` returns a downloadable PDF when `format=pdf`.
- For text/json extraction, JSON payload is returned.

## 4. Remediation

### `POST /api/v2/remediate/auto`

Run auto-remediation and return action summary plus optional AI guidance.

```json
{
  "fileUrl": "/path/file.pdf",
  "issues": [],
  "includeAIGuidance": true,
  "requireGemini": false
}
```

### `POST /api/v2/remediate/auto/download`

Generate and download the remediated PDF.

Supports either:

1. Multipart:
   - `file` (required)
   - `issues` (optional JSON array string)
2. JSON:
   - `fileUrl` (required)
   - `issues` (optional array)

Returns `application/pdf` attachment: `<original>_auto_remediated.pdf`

### `POST /api/v2/remediate/guidance`

Get manual remediation template + AI guidance.

```json
{
  "issueType": "missing_alt_text",
  "issueDescription": "Optional custom issue text",
  "standard": "WCAG 2.1",
  "requireGemini": false
}
```

## 5. Reports

### `POST /api/v2/reports/generate`

Generate report from analysis payload.

Request:

- `analysisData` (required)
- `format`: `json|pdf|html|csv|markdown`
- `sections` (optional list)
- optional branding fields

Behavior:

- `json` returns JSON body: `{ "success": true, "report": ... }`
- all other formats return downloadable file attachments

## 6. Validation and prompt metrics

- `POST /api/v2/validation/check`
  - input: `aiOutput` or `analysisResult`, optional `context`, optional `fallbackResponse`
  - output: confidence and recommendation fields
- `GET /api/v2/prompts/performance`
  - optional query: `promptName`

## 7. Error shape

Most endpoints return:

```json
{
  "success": false,
  "error": "error message"
}
```

HTTP status codes:

- `400` invalid request data
- `500` processing errors
- binary endpoints return files on success
