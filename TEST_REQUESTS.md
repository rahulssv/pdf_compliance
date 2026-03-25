# PDF Compliance Engine - API Test Requests

## Base URL
```
http://localhost:8000
```

## 1. Health Check

### Request
```bash
curl http://localhost:8000/health
```

### Expected Response
```json
{
  "service": "PDF Accessibility Compliance Engine",
  "status": "ok",
  "version": "1.0.0"
}
```

---

## 2. Scan Endpoint - Single File (Non-Compliant)

### Request
```bash
curl -X POST http://localhost:8000/api/v1/scan \
  -H "Content-Type: application/json" \
  -d '{
    "fileUrls": ["/evaluator/assets/untagged_report.pdf"]
  }'
```

### Expected Response
```json
{
  "files": [
    {
      "fileName": "untagged_report.pdf",
      "nonCompliancePercent": 65,
      "complianceStatus": "non-compliant",
      "issues": [
        {
          "description": "Document does not contain a tag tree...",
          "standard": "PDF/UA-1 §7.1",
          "category": "PDF/UA"
        },
        {
          "description": "Document language is not declared...",
          "standard": "WCAG 2.1 SC 3.1.1",
          "category": "WCAG"
        },
        {
          "description": "Document contains 1 image(s)...",
          "standard": "WCAG 2.1 SC 1.1.1",
          "category": "WCAG"
        }
      ]
    }
  ],
  "worstFile": {
    "fileName": "untagged_report.pdf",
    "nonCompliancePercent": 65
  }
}
```

---

## 3. Scan Endpoint - Single File (Compliant)

### Request
```bash
curl -X POST http://localhost:8000/api/v1/scan \
  -H "Content-Type: application/json" \
  -d '{
    "fileUrls": ["/evaluator/assets/accessible_guide.pdf"]
  }'
```

### Expected Response
```json
{
  "files": [
    {
      "fileName": "accessible_guide.pdf",
      "nonCompliancePercent": 20,
      "complianceStatus": "partially-compliant",
      "issues": [...]
    }
  ],
  "worstFile": {
    "fileName": "accessible_guide.pdf",
    "nonCompliancePercent": 20
  }
}
```

---

## 4. Scan Endpoint - Multiple Files

### Request
```bash
curl -X POST http://localhost:8000/api/v1/scan \
  -H "Content-Type: application/json" \
  -d '{
    "fileUrls": [
      "/evaluator/assets/untagged_report.pdf",
      "/evaluator/assets/accessible_guide.pdf",
      "/evaluator/assets/missing_alttext.pdf"
    ]
  }'
```

### What to Check
- `files` array has 3 elements
- `worstFile` identifies the file with highest `nonCompliancePercent`
- Each file has `fileName`, `nonCompliancePercent`, `complianceStatus`, `issues`

---

## 5. Remediate Endpoint - Single File (Gemini AI)

### Request
```bash
curl -X POST http://localhost:8000/api/v1/remediate \
  -H "Content-Type: application/json" \
  -d '{
    "fileUrls": ["/evaluator/assets/untagged_report.pdf"]
  }'
```

### Expected Response (with AI-generated fixes)
```json
{
  "files": [
    {
      "fileName": "untagged_report.pdf",
      "issues": [
        {
          "description": "Document does not contain a tag tree...",
          "standard": "PDF/UA-1 §7.1",
          "fix": "In Adobe Acrobat Pro, open the PDF and navigate to the 'Accessibility' tools. Select 'Autotag Document' to generate an initial tag tree..."
        },
        {
          "description": "Document language is not declared...",
          "standard": "WCAG 2.1 SC 3.1.1",
          "fix": "In Adobe Acrobat Pro, navigate to File > Properties. In the Document Properties dialog, select the 'Advanced' tab..."
        }
      ]
    }
  ]
}
```

### What to Check
- Each issue has a `fix` field
- Fixes are specific and actionable (not generic)
- Fixes mention specific tools (e.g., "Adobe Acrobat Pro")

---

## 6. Remediate Endpoint - Multiple Files

### Request
```bash
curl -X POST http://localhost:8000/api/v1/remediate \
  -H "Content-Type: application/json" \
  -d '{
    "fileUrls": [
      "/evaluator/assets/missing_alttext.pdf",
      "/evaluator/assets/partial_form.pdf"
    ]
  }'
```

### What to Check
- `files` array has 2 elements
- Each file has AI-generated remediation guidance
- Fixes are specific to the issue type

---

## 7. Dashboard Endpoint - Mixed Batch

### Request
```bash
curl -X POST http://localhost:8000/api/v1/dashboard \
  -H "Content-Type: application/json" \
  -d '{
    "fileUrls": [
      "/evaluator/assets/untagged_report.pdf",
      "/evaluator/assets/accessible_guide.pdf",
      "/evaluator/assets/missing_alttext.pdf",
      "/evaluator/assets/partial_form.pdf",
      "/evaluator/assets/scanned_policy.pdf"
    ]
  }'
```

### Expected Response
```json
{
  "totalScanned": 5,
  "totalIssues": 27,
  "totalFixable": 23,
  "complianceBreakdown": [
    { "status": "compliant", "count": 0 },
    { "status": "partially-compliant", "count": 2 },
    { "status": "non-compliant", "count": 3 }
  ],
  "topIssueTypes": [
    { "type": "Missing Alt Text", "count": 8 },
    { "type": "No Tag Tree", "count": 5 }
  ],
  "standardViolationFrequency": [
    { "standard": "WCAG 2.1", "count": 14 },
    { "standard": "PDF/UA-1", "count": 9 }
  ]
}
```

### Arithmetic Validation
- ✅ Sum of `complianceBreakdown[].count` = `totalScanned`
- ✅ `totalFixable` ≤ `totalIssues`
- ✅ All arrays have `count` fields

---

## 8. Dashboard Endpoint - Single Compliant File

### Request
```bash
curl -X POST http://localhost:8000/api/v1/dashboard \
  -H "Content-Type: application/json" \
  -d '{
    "fileUrls": ["/evaluator/assets/accessible_guide.pdf"]
  }'
```

### What to Check
- `totalScanned`: 1
- `complianceBreakdown` has 1 entry
- `topIssueTypes` may be empty if file is fully compliant
- `standardViolationFrequency` may be empty if file is fully compliant

---

## 9. Pretty Print JSON Output

Add `| python3 -m json.tool` to any request for formatted output:

```bash
curl -X POST http://localhost:8000/api/v1/scan \
  -H "Content-Type: application/json" \
  -d '{"fileUrls": ["/evaluator/assets/untagged_report.pdf"]}' \
  | python3 -m json.tool
```

---

## 10. Check Docker Logs (See Gemini API Activity)

```bash
docker logs pdf_compliance-pdf-compliance-api-1 2>&1 | tail -50
```

### What to Look For
- `✅ Gemini API initialized successfully`
- `🤖 Calling Gemini API for remediation...`
- `✅ Gemini response received`
- Progress indicators like `[2/5] Processing...`

---

## 11. Test Error Handling - Invalid File

### Request
```bash
curl -X POST http://localhost:8000/api/v1/scan \
  -H "Content-Type: application/json" \
  -d '{
    "fileUrls": ["/nonexistent/file.pdf"]
  }'
```

### Expected Behavior
- Returns 200 OK (not 404)
- File marked as non-compliant with error issue
- Error message explains file not found

---

## 12. Test Error Handling - Missing Field

### Request
```bash
curl -X POST http://localhost:8000/api/v1/scan \
  -H "Content-Type: application/json" \
  -d '{}'
```

### Expected Response
```json
{
  "error": "fileUrls is required"
}
```

---

## Quick Test Script

Save this as `test_api.sh`:

```bash
#!/bin/bash

echo "Testing all endpoints..."
echo ""

echo "1. Health:"
curl -s http://localhost:8000/health | python3 -m json.tool
echo ""

echo "2. Scan:"
curl -s -X POST http://localhost:8000/api/v1/scan \
  -H "Content-Type: application/json" \
  -d '{"fileUrls": ["/evaluator/assets/untagged_report.pdf"]}' \
  | python3 -m json.tool
echo ""

echo "3. Remediate (Gemini AI):"
curl -s -X POST http://localhost:8000/api/v1/remediate \
  -H "Content-Type: application/json" \
  -d '{"fileUrls": ["/evaluator/assets/untagged_report.pdf"]}' \
  | python3 -m json.tool
echo ""

echo "4. Dashboard:"
curl -s -X POST http://localhost:8000/api/v1/dashboard \
  -H "Content-Type: application/json" \
  -d '{"fileUrls": ["/evaluator/assets/untagged_report.pdf", "/evaluator/assets/accessible_guide.pdf"]}' \
  | python3 -m json.tool
```

Run with:
```bash
chmod +x test_api.sh
./test_api.sh
```

---

## Expected Fixture Files

These files should be available at `/evaluator/assets/`:
- `accessible_guide.pdf` - Fully or mostly compliant
- `missing_alttext.pdf` - Missing alternative text issues
- `partial_form.pdf` - Form field issues
- `scanned_policy.pdf` - Scanned document issues
- `untagged_report.pdf` - Missing tag tree issues

---

## Performance Notes

- **First request**: May take 3-5 seconds (Gemini API call + PDF analysis)
- **Cached requests**: < 100ms (using in-memory cache)
- **Retry behavior**: Up to 3 attempts with exponential backoff if Gemini fails
- **Fallback**: Quality responses even without Gemini API

---

## Troubleshooting

### If Gemini API is not working:
```bash
# Check logs
docker logs pdf_compliance-pdf-compliance-api-1 2>&1 | grep -i gemini

# Expected to see:
✅ Gemini API initialized successfully with model: gemini-2.5-flash
```

### If getting 500 errors:
```bash
# Check container logs
docker logs pdf_compliance-pdf-compliance-api-1 2>&1 | tail -100
```

### Restart container:
```bash
docker compose restart
```
