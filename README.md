# PDF Accessibility Compliance Engine

## Project Overview
A document intelligence system that analyzes PDF files for accessibility compliance violations, provides AI-powered remediation guidance, and generates compliance dashboards. Supports multiple accessibility standards including WCAG 2.1, PDF/UA-1, ADA, Section 508, and European Accessibility Act (EAA).

**Status**: ✅ Fully Implemented and Tested

---

## 🚀 Quick Start

### Prerequisites
- Docker and Docker Compose installed
- Python 3.11+
- Valid Google Gemini API key ([Get one here](https://makersuite.google.com/app/apikey))

### Setup & Run
```bash
# 1. Set your Gemini API key in .env
echo "GEMINI_API_KEY=your-api-key-here" > .env

# 2. Start the service
docker compose up --build -d

# 3. Verify it's running
curl http://localhost:8000/health
```

The service exposes:
- **Health endpoint**: `GET /health` (returns 200)
- **API endpoints**: Port 8000 (see API Contract below)

### Testing
See [`EASY_TESTING.md`](EASY_TESTING.md) for comprehensive testing commands and examples.

### Verify Gemini Integration
```bash
./test_gemini_api.sh
```

---

## 📚 Documentation

- **[EASY_TESTING.md](EASY_TESTING.md)** - Complete testing guide with all API commands
- **[API_CONTRACT_COMPLIANCE.md](API_CONTRACT_COMPLIANCE.md)** - Verification that implementation meets contract specs
- **[docs/pdf-accessibility-compliance-api-contract.md](docs/pdf-accessibility-compliance-api-contract.md)** - Full API contract specification

---

## API Contract

### Base URL
All endpoints are under `/api/v1/`

### Request Format (All Endpoints)
All three endpoints accept the same request body:

```json
{
  "fileUrls": [
    "/evaluator/assets/doc1.pdf",
    "C:\\data\\docs\\doc2.pdf",
    "https://example.com/doc3.pdf",
    "file:///path/to/doc4.pdf"
  ]
}
```

**Important**: `fileUrls` are actual file locators (HTTPS URLs, `file://` URLs, or absolute paths), NOT resource IDs.

---

## Required Endpoints

### 1. POST /api/v1/scan
**Purpose**: Detect accessibility issues and compute compliance metrics

**Response (200 OK)**:
```json
{
  "files": [
    {
      "fileName": "untagged_report.pdf",
      "nonCompliancePercent": 84,
      "complianceStatus": "non-compliant",
      "issues": [
        {
          "description": "Document does not contain a tag tree, so screen readers cannot interpret structural semantics.",
          "standard": "PDF/UA-1 §7.1",
          "category": "PDF/UA"
        },
        {
          "description": "Document language is not declared at the document level.",
          "standard": "WCAG 2.1 SC 3.1.1",
          "category": "WCAG"
        }
      ]
    },
    {
      "fileName": "accessible_guide.pdf",
      "nonCompliancePercent": 0,
      "complianceStatus": "compliant",
      "issues": []
    }
  ],
  "worstFile": {
    "fileName": "untagged_report.pdf",
    "nonCompliancePercent": 84
  }
}
```

**Field Requirements**:
- `nonCompliancePercent`: Must be a number (0-100), not a string
- `complianceStatus`: Recommended values: `compliant`, `partially-compliant`, `non-compliant`
- `issues`: Must be empty array for compliant files
- `issues[].standard`: Must reference real standards (e.g., "WCAG 2.1 SC 1.1.1", "PDF/UA-1 §7.1")
- `issues[].category`: Must be from: `WCAG`, `PDF/UA`, `ADA`, `Section 508`, `EAA`
- `worstFile`: Must identify the file with highest non-compliance percentage

---

### 2. POST /api/v1/remediate
**Purpose**: Provide actionable fix suggestions for each issue

**Response (200 OK)**:
```json
{
  "files": [
    {
      "fileName": "missing_alttext.pdf",
      "issues": [
        {
          "description": "Figure elements are missing alternative text.",
          "standard": "WCAG 2.1 SC 1.1.1",
          "fix": "Add meaningful Alt Text to each figure tag so a screen reader can announce the image purpose to non-visual users."
        }
      ]
    },
    {
      "fileName": "accessible_guide.pdf",
      "issues": []
    }
  ]
}
```

**Field Requirements**:
- `issues`: Must be empty array for compliant files
- `issues[].fix`: Must provide substantive, actionable remediation guidance (not generic text like "Fix this issue")
- Every issue must include `description`, `standard`, and `fix`

---

### 3. POST /api/v1/dashboard
**Purpose**: Aggregate compliance intelligence across the batch

**Response (200 OK)**:
```json
{
  "totalScanned": 5,
  "totalIssues": 27,
  "totalFixable": 23,
  "complianceBreakdown": [
    { "status": "compliant", "count": 1 },
    { "status": "partially-compliant", "count": 2 },
    { "status": "non-compliant", "count": 2 }
  ],
  "topIssueTypes": [
    { "type": "Missing Alt Text", "count": 8 },
    { "type": "No Tag Tree", "count": 5 },
    { "type": "Missing Document Language", "count": 4 }
  ],
  "standardViolationFrequency": [
    { "standard": "WCAG 2.1", "count": 14 },
    { "standard": "PDF/UA-1", "count": 9 },
    { "standard": "Section 508", "count": 4 }
  ]
}
```

**Arithmetic Rules**:
- `totalScanned` must equal the number of files in request
- Sum of `complianceBreakdown[].count` must equal `totalScanned`
- `totalFixable` must be ≤ `totalIssues`
- All trend arrays must include counts
- `topIssueTypes` should be empty only if `totalIssues` is 0

---

## Implementation Checklist

### Phase 1: Project Setup
- [ ] Initialize Python project with virtual environment
- [ ] Install dependencies: Flask/FastAPI, PyPDF2/pdfplumber/pypdf, google-generativeai
- [ ] Set up Docker and docker-compose.yml
- [ ] Configure web server/framework
- [ ] Implement `/health` endpoint (returns 200 with JSON body)
- [ ] Test local startup with `docker compose up --build`

### Phase 2: PDF Processing Infrastructure
- [ ] Integrate PDF processing library (PyPDF2, pdfplumber, or pypdf)
- [ ] Implement file locator handler supporting:
  - [ ] HTTPS URLs (using requests library)
  - [ ] `file://` URLs
  - [ ] Absolute filesystem paths (Windows and Unix)
- [ ] Add error handling for missing/invalid files
- [ ] Test reading from `/evaluator/assets/` directory

### Phase 3: Accessibility Analysis Engine
- [ ] Implement PDF structure analysis:
  - [ ] Tag tree detection
  - [ ] Document language detection
  - [ ] Alternative text presence
  - [ ] Form field labels
  - [ ] Reading order
  - [ ] Color contrast (if applicable)
  - [ ] Heading structure
- [ ] Map findings to standards:
  - [ ] WCAG 2.1 success criteria
  - [ ] PDF/UA-1 sections
  - [ ] Section 508 requirements
  - [ ] ADA guidelines
  - [ ] EAA requirements

### Phase 4: Gemini LLM Integration
- [ ] Set up Google Gemini API client
- [ ] Configure API key (via environment variable)
- [ ] Design prompts for:
  - [ ] Issue description generation
  - [ ] Standard mapping validation
  - [ ] Remediation guidance generation
- [ ] Implement fallback for LLM failures
- [ ] Add rate limiting and error handling

### Phase 5: Endpoint Implementation

#### /api/v1/scan
- [ ] Accept `fileUrls` array in request body
- [ ] Process each PDF file
- [ ] Detect accessibility issues
- [ ] Calculate `nonCompliancePercent` (0-100)
- [ ] Assign `complianceStatus`
- [ ] Populate `issues` array with proper structure
- [ ] Identify `worstFile`
- [ ] Return compliant files with empty issues array
- [ ] Ensure numeric types for percentages

#### /api/v1/remediate
- [ ] Reuse scan logic for issue detection
- [ ] Generate substantive `fix` text for each issue using Gemini
- [ ] Avoid generic remediation text
- [ ] Return empty issues for compliant files
- [ ] Ensure all required fields present

#### /api/v1/dashboard
- [ ] Aggregate data across all files
- [ ] Calculate `totalScanned`, `totalIssues`, `totalFixable`
- [ ] Build `complianceBreakdown` with correct counts
- [ ] Generate `topIssueTypes` ranking
- [ ] Generate `standardViolationFrequency` ranking
- [ ] Validate arithmetic consistency
- [ ] Handle edge case of all-compliant batch

### Phase 6: Testing & Validation
- [ ] Test with provided fixture files:
  - [ ] `accessible_guide.pdf` (should be compliant)
  - [ ] `missing_alttext.pdf` (alt text issues)
  - [ ] `partial_form.pdf` (form field issues)
  - [ ] `scanned_policy.pdf` (OCR/scanned document issues)
  - [ ] `untagged_report.pdf` (tag tree issues)
- [ ] Verify response schemas match contract exactly
- [ ] Test with mixed compliant/non-compliant batches
- [ ] Validate arithmetic rules in dashboard
- [ ] Test file locator handling (paths, URLs, file://)

### Phase 7: Docker & Deployment
- [ ] Finalize Dockerfile with Python base image
- [ ] Configure docker-compose.yml with proper port mapping
- [ ] Add environment variables (GEMINI_API_KEY)
- [ ] Ensure startup completes within 90 seconds
- [ ] Test health check responds before processing requests
- [ ] Optimize image size if needed

---

## Tech Stack

### Python Framework
**Flask** or **FastAPI**
- Flask: Lightweight, simple, great for REST APIs
- FastAPI: Modern, async support, automatic API docs

### PDF Processing
Choose one based on your needs:
- **PyPDF2**: General-purpose PDF manipulation
- **pdfplumber**: Better for text extraction and layout analysis
- **pypdf**: Modern fork of PyPDF2 with active maintenance

### LLM Integration
**Google Gemini**
- Library: `google-generativeai`
- Models: gemini-pro, gemini-pro-vision
- Setup:
  ```python
  import google.generativeai as genai
  genai.configure(api_key=os.environ["GEMINI_API_KEY"])
  model = genai.GenerativeModel('gemini-pro')
  ```

### Additional Libraries
- **requests**: For downloading PDFs from HTTPS URLs
- **urllib**: For parsing file:// URLs
- **pathlib**: For filesystem path handling

---

## Project Structure Example

```
pdf-compliance-engine/
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
├── README.md
├── .env.example
├── src/
│   ├── __init__.py
│   ├── app.py                 # Flask/FastAPI application
│   ├── config.py              # Configuration management
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── health.py          # Health check endpoint
│   │   └── api_v1.py          # API v1 endpoints
│   ├── services/
│   │   ├── __init__.py
│   │   ├── pdf_analyzer.py    # PDF accessibility analysis
│   │   ├── file_handler.py    # File locator handling
│   │   ├── gemini_service.py  # Gemini LLM integration
│   │   └── compliance.py      # Compliance logic
│   ├── models/
│   │   ├── __init__.py
│   │   └── schemas.py         # Request/response models
│   └── utils/
│       ├── __init__.py
│       └── standards.py       # Accessibility standards mapping
└── tests/
    ├── __init__.py
    └── test_api.py
```

---

## Sample requirements.txt

```txt
flask==3.0.0
# OR fastapi==0.109.0
# OR fastapi[all]==0.109.0  # includes uvicorn

google-generativeai==0.3.2
PyPDF2==3.0.1
# OR pdfplumber==0.10.3
# OR pypdf==3.17.4

requests==2.31.0
python-dotenv==1.0.0
gunicorn==21.2.0  # for production
```

---

## Sample Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies if needed
RUN apt-get update && apt-get install -y \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ ./src/

# Expose port
EXPOSE 8000

# Run the application
CMD ["python", "-m", "src.app"]
# OR for FastAPI: CMD ["uvicorn", "src.app:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

## Sample docker-compose.yml

```yaml
version: '3.8'

services:
  pdf-compliance-api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - GEMINI_API_KEY=${GEMINI_API_KEY}
      - FLASK_ENV=production
    volumes:
      - /evaluator/assets:/evaluator/assets:ro
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 10s
      timeout: 5s
      retries: 5
```

---

## Gemini Integration Example

```python
import google.generativeai as genai
import os

class GeminiService:
    def __init__(self):
        genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
        self.model = genai.GenerativeModel('gemini-pro')
    
    def generate_remediation(self, issue_description, standard):
        prompt = f"""
        You are an accessibility expert. Given the following PDF accessibility issue:
        
        Issue: {issue_description}
        Standard: {standard}
        
        Provide a specific, actionable remediation step that a document author can follow.
        Be concise but detailed enough to be useful.
        """
        
        try:
            response = self.model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            # Fallback to generic guidance
            return f"Review and fix the issue according to {standard} requirements."
    
    def enhance_issue_description(self, raw_finding, standard):
        prompt = f"""
        Convert this technical PDF accessibility finding into a clear description:
        
        Finding: {raw_finding}
        Standard: {standard}
        
        Provide a one-sentence explanation that is clear to non-technical users.
        """
        
        try:
            response = self.model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            return raw_finding
```

---

## Submission Requirements

### ZIP Structure
```
my-submission.zip
└── pdf-compliance-engine/
    ├── docker-compose.yml
    ├── Dockerfile
    ├── requirements.txt
    ├── src/
    ├── .env.example
    └── README.md
```

**Critical Rules**:
- Exactly ONE top-level folder in ZIP
- `docker-compose.yml` must be directly inside that folder
- No files at ZIP root level
- Keep ZIP under 50 MB

### Pre-Submission Checklist
- [ ] `docker compose up --build` starts without errors
- [ ] `GET /health` returns 200 within 90 seconds
- [ ] All three endpoints implemented and tested
- [ ] Response schemas match contract exactly
- [ ] Fixture files can be read from `/evaluator/assets/`
- [ ] No false positives on compliant files
- [ ] Arithmetic rules validated in dashboard
- [ ] ZIP structure is correct
- [ ] GEMINI_API_KEY configured in docker-compose.yml

---

## Common Pitfalls to Avoid

### Response Format Issues
❌ **Wrong**: `"nonCompliancePercent": "84%"` (string)  
✅ **Correct**: `"nonCompliancePercent": 84` (number)

❌ **Wrong**: Missing `issues` array  
✅ **Correct**: Always include `issues`, use empty array for compliant files

❌ **Wrong**: `"standard": "Accessibility"` (too vague)  
✅ **Correct**: `"standard": "WCAG 2.1 SC 1.1.1"` (specific)

❌ **Wrong**: `"fix": "Fix this issue."` (generic)  
✅ **Correct**: `"fix": "Add meaningful Alt Text to each figure tag..."` (actionable)

### File Handling Issues
❌ **Wrong**: Treating `fileUrls` as resource IDs  
✅ **Correct**: Reading files directly from provided locators

❌ **Wrong**: Only supporting HTTPS URLs  
✅ **Correct**: Supporting HTTPS, file://, and absolute paths

### Dashboard Arithmetic Issues
❌ **Wrong**: `totalScanned: 5` but breakdown sums to 3  
✅ **Correct**: Breakdown counts must sum to `totalScanned`

❌ **Wrong**: `totalFixable: 10` when `totalIssues: 8`  
✅ **Correct**: `totalFixable` ≤ `totalIssues`

---

## Accessibility Standards Reference

### WCAG 2.1 (Web Content Accessibility Guidelines)
- **SC 1.1.1**: Non-text Content (alt text)
- **SC 3.1.1**: Language of Page
- **SC 1.3.1**: Info and Relationships (structure)
- **SC 2.4.6**: Headings and Labels

### PDF/UA-1 (PDF Universal Accessibility)
- **§7.1**: Tag tree requirement
- **§7.3**: Alternative descriptions
- **§7.18**: Form fields

### Section 508
- **§1194.22(n)**: Form field labels
- **§1194.22(a)**: Text equivalents

### ADA (Americans with Disabilities Act)
- Title III requirements for digital accessibility

### EAA (European Accessibility Act)
- Digital accessibility requirements for EU

---

## Evaluation Process

1. **Submission Upload**: ZIP file uploaded via web UI
2. **Extraction**: Evaluator extracts to versioned folder
3. **Build**: Runs `docker compose up --build`
4. **Health Check**: Polls `/health` (90s timeout)
5. **Testing**: Runs Karate feature file against your API
6. **Scoring**: (scenarios passed / total) × 100
7. **Report**: Download evaluation-result.json and Karate HTML report

**Score Calculation**: Each Karate scenario is a scoring unit. All assertions in a scenario must pass for it to count.

---

## 🧪 Testing & Development

### Quick Testing
See [`EASY_TESTING.md`](EASY_TESTING.md) for all testing commands. Quick examples:

```bash
# Test all endpoints
curl http://localhost:8000/health
curl -X POST http://localhost:8000/api/v1/scan -H "Content-Type: application/json" \
  -d '{"fileUrls": ["/evaluator/assets/untagged_report.pdf"]}'
curl -X POST http://localhost:8000/api/v1/remediate -H "Content-Type: application/json" \
  -d '{"fileUrls": ["/evaluator/assets/missing_alttext.pdf"]}'
curl -X POST http://localhost:8000/api/v1/dashboard -H "Content-Type: application/json" \
  -d '{"fileUrls": ["/evaluator/assets/accessible_guide.pdf"]}'
```

### Verify Gemini Integration
```bash
# Test if Gemini API key is valid
./test_gemini_api.sh

# Check Docker logs for Gemini activity
docker logs 3_pdf_compliances-pdf-compliance-api-1 2>&1 | tail -50
```

### Local Development (without Docker)
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export GEMINI_API_KEY="your-api-key-here"

# Run locally
python -m src.app
```

### Debugging Tips
- Check [`API_CONTRACT_COMPLIANCE.md`](API_CONTRACT_COMPLIANCE.md) for contract verification
- Use `docker logs` to see Gemini API calls and responses
- Verify response field types (number vs string)
- Test arithmetic rules in dashboard endpoint
- Ensure health check works before testing other endpoints
- Check Gemini API quota and rate limits

---

## Resources

### Fixture Files Location
During evaluation: `/evaluator/assets/`
- `accessible_guide.pdf` - Fully compliant
- `missing_alttext.pdf` - Missing alternative text
- `partial_form.pdf` - Form field issues
- `scanned_policy.pdf` - Scanned document issues
- `untagged_report.pdf` - Missing tag tree

### Documentation
- WCAG 2.1: https://www.w3.org/WAI/WCAG21/quickref/
- PDF/UA: https://www.pdfa.org/resource/pdfua-in-a-nutshell/
- Section 508: https://www.section508.gov/
- Google Gemini API: https://ai.google.dev/docs

### Python Libraries
- Flask: https://flask.palletsprojects.com/
- FastAPI: https://fastapi.tiangolo.com/
- PyPDF2: https://pypdf2.readthedocs.io/
- pdfplumber: https://github.com/jsvine/pdfplumber
- google-generativeai: https://github.com/google/generative-ai-python

---

## Support

For questions about:
- **API Contract**: Review `docs/pdf-accessibility-compliance-api-contract.md`
- **Submission Process**: Review `docs/LEARNER_SUBMISSION_GUIDELINES.md`
- **Evaluation Failures**: Check Karate HTML report for specific assertion failures

---

## License

[Specify your license here]