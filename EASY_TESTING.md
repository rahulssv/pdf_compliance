# Easy Testing Guide - PDF Accessibility Compliance API

Quick reference for spinning up and testing the PDF Accessibility Compliance API.

---

## 🚀 Quick Start

### 1. Start the Docker Environment
```bash
docker compose up --build -d
```

### 2. Check Container Status
```bash
docker ps
```

### 3. View Logs
```bash
# View all logs
docker logs 3_pdf_compliances-pdf-compliance-api-1

# Follow logs in real-time
docker logs -f 3_pdf_compliances-pdf-compliance-api-1

# View last 50 lines
docker logs 3_pdf_compliances-pdf-compliance-api-1 2>&1 | tail -50
```

---

## 🧪 API Testing Commands

### Health Check
```bash
curl -s http://localhost:8000/health | jq .
```

**Expected Response:**
```json
{
  "service": "PDF Accessibility Compliance Engine",
  "status": "ok",
  "version": "1.0.0"
}
```

---

### Scan Endpoint
Test with 2 files:
```bash
curl -X POST http://localhost:8000/api/v1/scan \
  -H "Content-Type: application/json" \
  -d '{"fileUrls": ["/evaluator/assets/accessible_guide.pdf", "/evaluator/assets/untagged_report.pdf"]}' \
  | jq .
```

Test with all fixture files:
```bash
curl -X POST http://localhost:8000/api/v1/scan \
  -H "Content-Type: application/json" \
  -d '{"fileUrls": [
    "/evaluator/assets/accessible_guide.pdf",
    "/evaluator/assets/missing_alttext.pdf",
    "/evaluator/assets/untagged_report.pdf",
    "/evaluator/assets/partial_form.pdf",
    "/evaluator/assets/scanned_policy.pdf"
  ]}' \
  | jq .
```

**Expected Response Structure:**
```json
{
  "files": [
    {
      "fileName": "...",
      "nonCompliancePercent": 0-100,
      "complianceStatus": "compliant|partially-compliant|non-compliant",
      "issues": [...]
    }
  ],
  "worstFile": {
    "fileName": "...",
    "nonCompliancePercent": 0-100
  }
}
```

---

### Remediate Endpoint
Test with single file:
```bash
curl -X POST http://localhost:8000/api/v1/remediate \
  -H "Content-Type: application/json" \
  -d '{"fileUrls": ["/evaluator/assets/missing_alttext.pdf"]}' \
  | jq .
```

Test with multiple files:
```bash
curl -X POST http://localhost:8000/api/v1/remediate \
  -H "Content-Type: application/json" \
  -d '{"fileUrls": [
    "/evaluator/assets/missing_alttext.pdf",
    "/evaluator/assets/untagged_report.pdf"
  ]}' \
  | jq .
```

**Expected Response Structure:**
```json
{
  "files": [
    {
      "fileName": "...",
      "issues": [
        {
          "description": "...",
          "standard": "...",
          "fix": "Detailed AI-generated remediation guidance"
        }
      ]
    }
  ]
}
```

---

### Dashboard Endpoint
Test with all fixture files:
```bash
curl -X POST http://localhost:8000/api/v1/dashboard \
  -H "Content-Type: application/json" \
  -d '{"fileUrls": [
    "/evaluator/assets/accessible_guide.pdf",
    "/evaluator/assets/missing_alttext.pdf",
    "/evaluator/assets/untagged_report.pdf",
    "/evaluator/assets/partial_form.pdf",
    "/evaluator/assets/scanned_policy.pdf"
  ]}' \
  | jq .
```

**Expected Response Structure:**
```json
{
  "totalScanned": 5,
  "totalIssues": 11,
  "totalFixable": 11,
  "complianceBreakdown": [...],
  "topIssueTypes": [...],
  "standardViolationFrequency": [...]
}
```

---

## 🤖 Gemini API Testing

### Test Gemini API Key
```bash
./test_gemini_api.sh
```

**Expected Output (Valid Key):**
```
✅ API Key is VALID!
   Generated text: Hello.
```

**Expected Output (Invalid Key):**
```
❌ API Error (Code: 400)
   Message: API key not valid. Please pass a valid API key.
```

### Check Gemini Logs
```bash
docker logs 3_pdf_compliances-pdf-compliance-api-1 2>&1 | grep -E "Gemini|🤖|✅|⚠️|❌"
```

---

## 🔧 Useful Commands

### Rebuild and Restart
```bash
docker compose up --build -d
```

### Stop Container
```bash
docker compose down
```

### Check Environment Variables
```bash
docker exec 3_pdf_compliances-pdf-compliance-api-1 env | grep GEMINI
```

### Access Container Shell
```bash
docker exec -it 3_pdf_compliances-pdf-compliance-api-1 bash
```

### View Available Fixture Files
```bash
ls -la docs/fixtures/
```

---

## 📝 Quick Test Sequence

Run all tests in sequence:
```bash
# 1. Health check
echo "=== Testing Health Endpoint ==="
curl -s http://localhost:8000/health | jq .

# 2. Scan endpoint
echo -e "\n=== Testing Scan Endpoint ==="
curl -s -X POST http://localhost:8000/api/v1/scan \
  -H "Content-Type: application/json" \
  -d '{"fileUrls": ["/evaluator/assets/untagged_report.pdf"]}' \
  | jq .

# 3. Remediate endpoint
echo -e "\n=== Testing Remediate Endpoint ==="
curl -s -X POST http://localhost:8000/api/v1/remediate \
  -H "Content-Type: application/json" \
  -d '{"fileUrls": ["/evaluator/assets/missing_alttext.pdf"]}' \
  | jq '.files[0].issues[0].fix'

# 4. Dashboard endpoint
echo -e "\n=== Testing Dashboard Endpoint ==="
curl -s -X POST http://localhost:8000/api/v1/dashboard \
  -H "Content-Type: application/json" \
  -d '{"fileUrls": [
    "/evaluator/assets/accessible_guide.pdf",
    "/evaluator/assets/missing_alttext.pdf",
    "/evaluator/assets/untagged_report.pdf"
  ]}' \
  | jq '{totalScanned, totalIssues, totalFixable}'
```

---

## 🐛 Troubleshooting

### Container not starting?
```bash
# Check logs for errors
docker logs 3_pdf_compliances-pdf-compliance-api-1

# Rebuild from scratch
docker compose down
docker compose up --build
```

### API not responding?
```bash
# Check if container is healthy
docker ps

# Check if port 8000 is accessible
curl http://localhost:8000/health
```

### Gemini not working?
```bash
# Test API key
./test_gemini_api.sh

# Check environment variable
docker exec 3_pdf_compliances-pdf-compliance-api-1 env | grep GEMINI_API_KEY
```

---

## 📚 File Paths Reference

All fixture files are mounted at `/evaluator/assets/` inside the container:

- `/evaluator/assets/accessible_guide.pdf` - Fully compliant PDF
- `/evaluator/assets/missing_alttext.pdf` - Missing alternative text
- `/evaluator/assets/partial_form.pdf` - Form field issues
- `/evaluator/assets/scanned_policy.pdf` - Scanned document issues
- `/evaluator/assets/untagged_report.pdf` - Missing tag tree

---

## 🎯 Expected Behavior

### Compliant File
- `nonCompliancePercent`: 0
- `complianceStatus`: "compliant"
- `issues`: [] (empty array)

### Non-Compliant File
- `nonCompliancePercent`: > 0
- `complianceStatus`: "non-compliant" or "partially-compliant"
- `issues`: Array with detailed issue descriptions

### Gemini Integration
- Remediation fixes should be detailed and context-specific
- Not generic template responses
- Should reference specific tools (e.g., Adobe Acrobat Pro)
- Should provide step-by-step guidance