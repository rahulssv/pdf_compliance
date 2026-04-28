# PDF Accessibility Compliance Engine

Flask-based API and UI for PDF accessibility analysis, remediation guidance, PII detection, and compliance reporting.

## What is implemented

- **v1 contract endpoints**: `/api/v1/scan`, `/api/v1/remediate`, `/api/v1/dashboard`
- **v2 workflows**: upload analysis, batch analysis, page-level analysis/extraction, remediation guidance, report generation
- **Auto-remediation download**: generate and download an auto-remediated PDF
- **Gemini integration**: AI remediation/guidance with fallback behavior when Gemini is unavailable
- **Web UI** at `/` for upload → analyze → export/download

## Quick start (Docker)

```bash
cp .env.example .env
# Optional but recommended for AI guidance:
# echo "GEMINI_API_KEY=your_key" >> .env

docker compose up --build -d
curl http://localhost:8000/health
```

Open:

- UI: `http://localhost:8000/`
- Health: `http://localhost:8000/health`

## Quick start (local)

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Optional:
export GEMINI_API_KEY="your_key"

python -m src.app
```

## UI flow

1. Open `/`
2. Upload a PDF
3. Enable **Auto-remediate** (optional)
4. Analyze
5. If auto-remediation is enabled, use **Download Auto-remediated PDF**

## API overview

### Core endpoints

| Area | Endpoint | Method |
|---|---|---|
| Health | `/health` | GET |
| UI | `/` | GET |
| v1 scan | `/api/v1/scan` | POST |
| v1 remediate | `/api/v1/remediate` | POST |
| v1 dashboard | `/api/v1/dashboard` | POST |
| v2 analyze by locator | `/api/v2/analyze` | POST |
| v2 analyze upload | `/api/v2/analyze/upload` | POST |
| v2 analyze batch | `/api/v2/analyze/batch` | POST |
| v2 PII detect | `/api/v2/pii/detect` | POST |
| v2 pages analyze | `/api/v2/pages/analyze` | POST |
| v2 pages extract | `/api/v2/pages/extract` | POST |
| v2 pages summary | `/api/v2/pages/summary` | POST |
| v2 auto-remediate | `/api/v2/remediate/auto` | POST |
| v2 auto-remediated PDF download | `/api/v2/remediate/auto/download` | POST |
| v2 remediation guidance | `/api/v2/remediate/guidance` | POST |
| v2 report generate | `/api/v2/reports/generate` | POST |
| v2 validation | `/api/v2/validation/check` | POST |
| v2 prompt performance | `/api/v2/prompts/performance` | GET |

### Example: analyze uploaded PDF

```bash
curl -X POST http://localhost:8000/api/v2/analyze/upload \
  -F "file=@/absolute/path/sample.pdf" \
  -F 'options={"detectPII":true,"pageLevel":true,"autoRemediate":true,"validateAI":true}'
```

### Example: download auto-remediated PDF

```bash
curl -X POST http://localhost:8000/api/v2/remediate/auto/download \
  -F "file=@/absolute/path/sample.pdf" \
  -F 'issues=[{"description":"Document language is not declared at the document level.","standard":"WCAG 2.1 SC 3.1.1"}]' \
  --output sample_auto_remediated.pdf
```

## Gemini behavior

- If `GEMINI_API_KEY` is set, AI guidance/remediation uses Gemini first.
- If Gemini fails and strict mode is not requested, fallback remediation text is returned.
- Strict Gemini mode can be requested per request using `requireGemini` / `requireGeminiRemediation`.

## Testing

```bash
pytest -q
```

## API Monitoring & Logging

Monitor all API calls (incoming requests and outgoing Gemini API calls) with comprehensive logging:

```bash
# Quick start - enable logging
./scripts/enable_api_logging.sh

# View logs in real-time
docker-compose logs -f pdf-compliance-api | grep -E "INCOMING|OUTGOING|GEMINI"
```

**Documentation:**
- 📖 [Quick Start Guide](docs/API_LOGGING_QUICK_START.md) - Get started in 3 steps
- 📚 [Complete Monitoring Guide](docs/API_MONITORING_GUIDE.md) - Full documentation

**What gets logged:**
- ✅ All HTTP requests (method, URL, headers, body)
- ✅ All HTTP responses (status, timing, body)
- ✅ Gemini API calls (model, prompts, responses)
- ✅ Errors with stack traces
- ✅ Request correlation via unique IDs

## Documentation

- [`docs/API_V2_SPECIFICATION.md`](docs/API_V2_SPECIFICATION.md)
- [`docs/DEPLOYMENT_GUIDE.md`](docs/DEPLOYMENT_GUIDE.md)
- [`docs/TESTING_GUIDE.md`](docs/TESTING_GUIDE.md)
- [`docs/API_LOGGING_QUICK_START.md`](docs/API_LOGGING_QUICK_START.md) - **NEW: API Monitoring Quick Start**
- [`docs/API_MONITORING_GUIDE.md`](docs/API_MONITORING_GUIDE.md) - **NEW: Complete Monitoring Guide**
- [`docs/pdf-accessibility-compliance-api-contract.md`](docs/pdf-accessibility-compliance-api-contract.md) (legacy v1 contract reference)
