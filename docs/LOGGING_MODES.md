# API Logging Modes

## Overview

The application supports two logging modes to balance between visibility and log volume.

## Logging Modes

### 1. Standard Mode (Default - Recommended)

**Configuration:**
```yaml
environment:
  - ENABLE_API_LOGGING=true
  - ENABLE_VERBOSE_LOGGING=false  # This is the key setting
```

**What You Get:**
- ✅ Concise gunicorn access logs (Apache-style format)
- ✅ Application service logs (PDF analysis, Gemini calls, etc.)
- ✅ Error logs with stack traces
- ❌ No verbose JSON request/response logs

**Example Output:**
```
127.0.0.1 - - [28/Apr/2026:12:29:15 +0000] "GET /health HTTP/1.1" 200 82 "-" "curl/8.14.1"
172.20.0.1 - - [28/Apr/2026:12:26:57 +0000] "POST /api/v2/analyze/upload HTTP/1.1" 200 22188 "http://0.0.0.0:8000/" "Mozilla/5.0..."
2026-04-28 12:26:57 - src.services.pdf_analyzer - INFO - 🔍 Analyzing document.pdf...
2026-04-28 12:26:57 - src.services.gemini_service - INFO - 🤖 Gemini call using model gemini-2.5-flash
```

**Best For:**
- ✅ Production environments
- ✅ Monitoring API traffic
- ✅ Performance tracking
- ✅ Keeping log volume manageable

### 2. Verbose Mode (Debug)

**Configuration:**
```yaml
environment:
  - ENABLE_API_LOGGING=true
  - ENABLE_VERBOSE_LOGGING=true  # Enable detailed logging
```

**What You Get:**
- ✅ Everything from Standard Mode
- ✅ Detailed JSON request logs with headers, body, files
- ✅ Detailed JSON response logs with headers, body
- ✅ Request/response correlation via unique IDs
- ✅ Full Gemini API call details

**Example Output:**
```
📥 INCOMING REQUEST: {
  "request_id": "1777379217052",
  "timestamp": "2026-04-28 12:26:57",
  "method": "POST",
  "url": "http://0.0.0.0:8000/api/v2/analyze/upload",
  "path": "/api/v2/analyze/upload",
  "remote_addr": "172.20.0.1",
  "headers": {...},
  "files": {
    "file": {
      "filename": "document.pdf",
      "content_type": "application/pdf"
    }
  }
}

✅ OUTGOING RESPONSE: {
  "request_id": "1777379217052",
  "status_code": 200,
  "duration_ms": 11848.48,
  "content_length": 22188
}
```

**Best For:**
- ✅ Development and debugging
- ✅ Troubleshooting issues
- ✅ Understanding request/response flow
- ✅ API integration testing

**⚠️ Warning:** Verbose mode generates significantly more log data. Not recommended for production.

## Switching Between Modes

### Method 1: Docker Compose (Recommended)

Edit `docker-compose.yml`:

```yaml
services:
  pdf-compliance-api:
    environment:
      - ENABLE_VERBOSE_LOGGING=false  # Standard mode
      # OR
      - ENABLE_VERBOSE_LOGGING=true   # Verbose mode
```

Then restart:
```bash
docker-compose restart pdf-compliance-api
```

### Method 2: Environment File

Edit `.env`:
```bash
ENABLE_VERBOSE_LOGGING=false  # Standard mode
# OR
ENABLE_VERBOSE_LOGGING=true   # Verbose mode
```

Then rebuild:
```bash
docker-compose down
docker-compose up -d --build
```

### Method 3: Interactive Script

```bash
./scripts/enable_api_logging.sh
# Choose option 1 for standard mode
# Choose option 2 for verbose mode
```

## Log Volume Comparison

| Mode | Logs per Request | Daily Volume (1000 req/day) |
|------|------------------|----------------------------|
| Standard | ~200 bytes | ~200 KB |
| Verbose | ~2-5 KB | ~2-5 MB |

## What's Always Logged (Both Modes)

Regardless of the mode, you always get:

1. **Gunicorn Access Logs:**
   ```
   IP - - [timestamp] "METHOD /path HTTP/1.1" status size "referer" "user-agent"
   ```

2. **Application Service Logs:**
   - PDF analysis progress
   - Gemini API calls
   - PII detection results
   - Auto-remediation actions
   - Validation results

3. **Error Logs:**
   - Exceptions with stack traces
   - Request context for errors
   - Correlation IDs

## Filtering Logs

### View Only Access Logs (Standard Format)
```bash
docker-compose logs pdf-compliance-api | grep -E "^\d+\.\d+\.\d+\.\d+"
```

### View Only Application Logs
```bash
docker-compose logs pdf-compliance-api | grep -E "INFO|WARNING|ERROR" | grep -v "^\d+\.\d+\.\d+\.\d+"
```

### Exclude Health Checks
```bash
docker-compose logs pdf-compliance-api | grep -v "/health"
```

### Use the Helper Script
```bash
./scripts/view_api_logs.sh no-health    # Exclude health checks
./scripts/view_api_logs.sh api-only     # Only API calls
./scripts/view_api_logs.sh gemini       # Only Gemini calls
```

## Recommendations

### For Production
```yaml
ENABLE_API_LOGGING=true
ENABLE_VERBOSE_LOGGING=false
```
- Clean, concise logs
- Easy to parse and analyze
- Minimal storage requirements
- Still captures all important information

### For Development
```yaml
ENABLE_API_LOGGING=true
ENABLE_VERBOSE_LOGGING=true
```
- Full visibility into requests/responses
- Easier debugging
- Better understanding of data flow
- Helpful for API integration

### For Troubleshooting
1. Start with standard mode
2. If you need more details, temporarily enable verbose mode
3. Reproduce the issue
4. Capture the detailed logs
5. Switch back to standard mode

## Performance Impact

| Mode | CPU Impact | Memory Impact | I/O Impact |
|------|-----------|---------------|------------|
| Standard | Minimal (~1%) | Minimal | Low |
| Verbose | Low (~2-3%) | Low | Medium |

Both modes have negligible performance impact on the application itself.

## Summary

- **Standard Mode (default)**: Clean, concise logs with gunicorn access logs + application logs
- **Verbose Mode**: Detailed JSON logs with full request/response details
- **Switch anytime**: Just change `ENABLE_VERBOSE_LOGGING` and restart
- **Production**: Always use standard mode
- **Development**: Use verbose mode when needed

For more information, see:
- [API Monitoring Guide](./API_MONITORING_GUIDE.md)
- [Quick Start Guide](./API_LOGGING_QUICK_START.md)