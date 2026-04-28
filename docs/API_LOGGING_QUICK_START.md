# API Logging Quick Start Guide

## 🚀 Quick Setup (3 Steps)

### Step 1: Enable Logging
```bash
# Option A: Use the interactive script
./scripts/enable_api_logging.sh

# Option B: Manual configuration
# Add to .env file:
ENABLE_API_LOGGING=true
ENABLE_VERBOSE_LOGGING=false
```

### Step 2: Restart Services
```bash
docker-compose down
docker-compose up -d
```

### Step 3: View Logs
```bash
# Real-time logs
docker-compose logs -f pdf-compliance-api

# Filter API calls only
docker-compose logs -f pdf-compliance-api | grep -E "INCOMING|OUTGOING|GEMINI"
```

## 📊 Common Log Viewing Commands

### View All Logs
```bash
docker-compose logs -f pdf-compliance-api
```

### View Incoming Requests
```bash
docker-compose logs pdf-compliance-api | grep "📥 INCOMING REQUEST"
```

### View Outgoing Responses
```bash
docker-compose logs pdf-compliance-api | grep "OUTGOING RESPONSE"
```

### View Gemini API Calls
```bash
docker-compose logs pdf-compliance-api | grep "🌐 GEMINI API"
```

### View Errors Only
```bash
docker-compose logs pdf-compliance-api | grep "💥\|❌\|ERROR"
```

### Export to File
```bash
docker-compose logs pdf-compliance-api > api_logs.txt
```

### View Last N Lines
```bash
docker-compose logs --tail 100 pdf-compliance-api
```

### View Logs Since Time
```bash
# Last hour
docker-compose logs --since 1h pdf-compliance-api

# Last 30 minutes
docker-compose logs --since 30m pdf-compliance-api
```

## 🎯 What Gets Logged?

### ✅ Incoming Requests
- HTTP method (GET, POST, PUT, DELETE)
- Full URL and path
- Headers (sensitive ones redacted)
- Query parameters
- Request body (JSON/form data)
- File upload metadata
- Client IP and User-Agent
- Unique request ID

### ✅ Outgoing Responses
- Status code (200, 404, 500, etc.)
- Response headers
- Response body (for JSON)
- Duration in milliseconds
- Content type and size

### ✅ External API Calls (Gemini)
- Model name and configuration
- Prompt preview
- Response preview
- Timing information
- Retry attempts
- Error details

### ✅ Errors
- Exception type and message
- Stack trace
- Request context
- Correlation ID

## 🔧 Configuration Options

### Standard Logging (Recommended for Production)
```bash
ENABLE_API_LOGGING=true
ENABLE_VERBOSE_LOGGING=false
```
- Logs metadata only
- Redacts sensitive information
- Minimal performance impact

### Verbose Logging (Debug Mode)
```bash
ENABLE_API_LOGGING=true
ENABLE_VERBOSE_LOGGING=true
```
- Includes full request/response bodies
- Complete Gemini prompts and responses
- Higher performance impact
- ⚠️ **NOT recommended for production**

### Disable Logging
```bash
ENABLE_API_LOGGING=false
ENABLE_VERBOSE_LOGGING=false
```

## 📝 Log Format Examples

### Incoming Request
```
📥 INCOMING REQUEST: {
  "request_id": "1714305234567",
  "method": "POST",
  "path": "/api/v2/analyze",
  "status_code": 200,
  "duration_ms": 3542.15
}
```

### Gemini API Call
```
🌐 GEMINI API CALL: {
  "model": "gemini-2.5-flash",
  "prompt_length": 1024,
  "duration_ms": 2341.23
}
```

### Error
```
💥 REQUEST EXCEPTION: {
  "request_id": "1714305234567",
  "exception_type": "ValueError",
  "exception_message": "Invalid PDF format"
}
```

## 🔍 Troubleshooting

### No Logs Appearing?
```bash
# Check configuration
docker-compose exec pdf-compliance-api env | grep ENABLE_API_LOGGING

# Restart services
docker-compose restart pdf-compliance-api
```

### Too Many Logs?
```bash
# Disable verbose mode
# In .env: ENABLE_VERBOSE_LOGGING=false

# Filter logs
docker-compose logs pdf-compliance-api | grep -v "DEBUG"
```

### Can't See Request Bodies?
```bash
# Enable verbose logging
# In .env: ENABLE_VERBOSE_LOGGING=true

# Restart
docker-compose restart pdf-compliance-api
```

## 📚 Full Documentation

For complete details, see [API_MONITORING_GUIDE.md](./API_MONITORING_GUIDE.md)

## 🎓 Examples

### Example 1: Monitor a Specific Endpoint
```bash
# Watch /api/v2/analyze endpoint
docker-compose logs -f pdf-compliance-api | grep "/api/v2/analyze"
```

### Example 2: Track Request Performance
```bash
# Find slow requests (>5 seconds)
docker-compose logs pdf-compliance-api | grep "duration_ms" | grep -E "[5-9][0-9]{3}|[0-9]{5,}"
```

### Example 3: Debug Failed Requests
```bash
# Show all 4xx and 5xx responses
docker-compose logs pdf-compliance-api | grep -E "status_code.*[45][0-9]{2}"
```

### Example 4: Monitor Gemini API Usage
```bash
# Count Gemini API calls
docker-compose logs pdf-compliance-api | grep "GEMINI API CALL" | wc -l

# Show Gemini errors
docker-compose logs pdf-compliance-api | grep "GEMINI" | grep "ERROR"
```

## 💡 Pro Tips

1. **Use Request IDs**: Each request has a unique ID for tracing through logs
2. **Filter by Emoji**: Use emoji markers (📥, ✅, ❌) for quick filtering
3. **Export Regularly**: Save logs to files for analysis
4. **Monitor Performance**: Track `duration_ms` to identify slow endpoints
5. **Watch for Patterns**: Look for repeated errors or unusual traffic

## 🔐 Security Notes

- Sensitive headers (Authorization, API keys) are automatically redacted
- Passwords in request bodies are masked
- Use standard logging in production (not verbose)
- Restrict log file access on the host system

## 📞 Need Help?

- Full guide: [API_MONITORING_GUIDE.md](./API_MONITORING_GUIDE.md)
- Main README: [../README.md](../README.md)
- Open an issue on GitHub for support