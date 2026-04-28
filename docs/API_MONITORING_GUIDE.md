# API Monitoring and Logging Guide

## Overview

This guide explains how to monitor and log all API calls in the PDF Compliance application running in Docker Compose. The system captures both incoming HTTP requests and outgoing API calls (like Gemini API) with full details including HTTP methods, URLs, headers, request/response bodies, and timing information.

## Features

### 1. **Incoming Request Logging**
- HTTP method (GET, POST, PUT, DELETE, etc.)
- Full URL and path
- Request headers (sensitive headers redacted)
- Query parameters
- Request body (JSON, form data, file uploads)
- Client IP address and User-Agent
- Unique request ID for tracing

### 2. **Outgoing Response Logging**
- HTTP status code and status message
- Response headers
- Response body (for JSON responses)
- Response time (duration in milliseconds)
- Content type and size

### 3. **External API Call Logging**
- Gemini API calls with model information
- Request/response timing
- Prompt and response previews
- Error tracking and retry attempts
- Model fallback information

### 4. **Error Tracking**
- Exception details with stack traces
- Request context when errors occur
- Correlation with request IDs

## Configuration

### Environment Variables

Add these to your `.env` file or Docker Compose environment:

```bash
# Enable comprehensive API request/response logging
ENABLE_API_LOGGING=true

# Enable verbose/debug logging (includes full request/response bodies)
ENABLE_VERBOSE_LOGGING=false
```

### Logging Levels

- **Standard Logging** (`ENABLE_API_LOGGING=true`, `ENABLE_VERBOSE_LOGGING=false`):
  - Logs request/response metadata
  - Includes status codes, timing, and headers
  - Redacts sensitive information
  - Suitable for production

- **Verbose Logging** (`ENABLE_VERBOSE_LOGGING=true`):
  - Includes full request/response bodies
  - Detailed Gemini API call information
  - Complete prompt and response content
  - Use for debugging only (not recommended for production)

## Docker Compose Setup

The `docker-compose.yml` is already configured with:

```yaml
services:
  pdf-compliance-api:
    environment:
      - ENABLE_API_LOGGING=true
      - ENABLE_VERBOSE_LOGGING=false
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

## Viewing Logs

### Method 1: Real-time Log Streaming

View logs in real-time as requests come in:

```bash
# View all logs
docker-compose logs -f pdf-compliance-api

# View only API-related logs
docker-compose logs -f pdf-compliance-api | grep -E "INCOMING|OUTGOING|GEMINI"
```

### Method 2: Filter by Log Type

```bash
# View incoming requests only
docker-compose logs pdf-compliance-api | grep "📥 INCOMING REQUEST"

# View outgoing responses only
docker-compose logs pdf-compliance-api | grep "OUTGOING RESPONSE"

# View Gemini API calls
docker-compose logs pdf-compliance-api | grep "🌐 GEMINI API"

# View errors only
docker-compose logs pdf-compliance-api | grep "💥 REQUEST EXCEPTION"
```

### Method 3: Export Logs to File

```bash
# Export all logs
docker-compose logs pdf-compliance-api > api_logs.txt

# Export logs from last hour
docker-compose logs --since 1h pdf-compliance-api > recent_logs.txt

# Export logs with timestamps
docker-compose logs -t pdf-compliance-api > timestamped_logs.txt
```

### Method 4: Use Docker Logs Command

```bash
# Get container ID
docker ps | grep pdf-compliance-api

# View logs by container ID
docker logs -f <container_id>

# View last 100 lines
docker logs --tail 100 <container_id>
```

## Log Format Examples

### Incoming Request Log

```json
📥 INCOMING REQUEST: {
  "request_id": "1714305234567",
  "timestamp": "2024-04-28 12:30:34",
  "method": "POST",
  "url": "http://localhost:8000/api/v2/analyze",
  "path": "/api/v2/analyze",
  "remote_addr": "172.18.0.1",
  "user_agent": "Mozilla/5.0...",
  "headers": {
    "Content-Type": "multipart/form-data",
    "Authorization": "***REDACTED***"
  },
  "files": {
    "file": {
      "filename": "document.pdf",
      "content_type": "application/pdf"
    }
  }
}
```

### Outgoing Response Log

```json
✅ OUTGOING RESPONSE: {
  "request_id": "1714305234567",
  "timestamp": "2024-04-28 12:30:38",
  "method": "POST",
  "path": "/api/v2/analyze",
  "status_code": 200,
  "status": "200 OK",
  "duration_ms": 3542.15,
  "content_type": "application/json",
  "content_length": 2048
}
```

### Gemini API Call Log

```json
🌐 GEMINI API CALL: {
  "timestamp": "2024-04-28 12:30:35",
  "service": "Gemini API",
  "model": "gemini-2.5-flash",
  "attempt": "1/3",
  "prompt_length": 1024,
  "prompt_preview": "Analyze the following PDF content...",
  "temperature": 0.7,
  "max_tokens": 2048
}
```

## Advanced Monitoring Techniques

### 1. Using jq for JSON Parsing

If you have `jq` installed, you can parse JSON logs:

```bash
# Extract all status codes
docker-compose logs pdf-compliance-api | grep "OUTGOING RESPONSE" | jq '.status_code'

# Find slow requests (>5 seconds)
docker-compose logs pdf-compliance-api | grep "OUTGOING RESPONSE" | jq 'select(.duration_ms > 5000)'

# Count requests by endpoint
docker-compose logs pdf-compliance-api | grep "INCOMING REQUEST" | jq -r '.path' | sort | uniq -c
```

### 2. Network Traffic Inspection with tcpdump

For deep packet inspection (requires root access):

```bash
# Install tcpdump in container
docker-compose exec pdf-compliance-api apt-get update && apt-get install -y tcpdump

# Capture HTTP traffic
docker-compose exec pdf-compliance-api tcpdump -i any -A 'tcp port 8000'

# Save to file
docker-compose exec pdf-compliance-api tcpdump -i any -w /tmp/capture.pcap 'tcp port 8000'
```

### 3. Using Docker Stats for Resource Monitoring

```bash
# Monitor container resource usage
docker stats pdf-compliance-api

# Continuous monitoring
watch -n 1 'docker stats --no-stream pdf-compliance-api'
```

### 4. Centralized Logging with ELK Stack

For production environments, consider integrating with ELK (Elasticsearch, Logstash, Kibana):

```yaml
# docker-compose.yml addition
services:
  pdf-compliance-api:
    logging:
      driver: "gelf"
      options:
        gelf-address: "udp://logstash:12201"
        tag: "pdf-compliance-api"
```

## Troubleshooting

### Issue: No Logs Appearing

**Solution:**
```bash
# Check if logging is enabled
docker-compose exec pdf-compliance-api env | grep ENABLE_API_LOGGING

# Restart with logging enabled
docker-compose down
docker-compose up -d
```

### Issue: Too Many Logs

**Solution:**
```bash
# Disable verbose logging
# In docker-compose.yml, set:
ENABLE_VERBOSE_LOGGING=false

# Or filter logs
docker-compose logs pdf-compliance-api | grep -v "DEBUG"
```

### Issue: Logs Not Showing Request Bodies

**Solution:**
```bash
# Enable verbose logging
# In docker-compose.yml, set:
ENABLE_VERBOSE_LOGGING=true

# Restart container
docker-compose restart pdf-compliance-api
```

### Issue: Cannot See Gemini API Calls

**Solution:**
```bash
# Check if Gemini API key is configured
docker-compose exec pdf-compliance-api env | grep GEMINI_API_KEY

# Enable verbose logging to see full API details
ENABLE_VERBOSE_LOGGING=true
```

## Performance Considerations

### Log Volume Management

- **Standard logging**: ~1-2 KB per request
- **Verbose logging**: ~10-50 KB per request (includes full bodies)
- **Recommended**: Use log rotation (already configured in docker-compose.yml)

### Log Rotation Settings

Current configuration in `docker-compose.yml`:
```yaml
logging:
  driver: "json-file"
  options:
    max-size: "10m"    # Max 10MB per log file
    max-file: "3"      # Keep 3 log files (30MB total)
```

Adjust based on your needs:
- **High traffic**: Increase `max-file` to 5-10
- **Low storage**: Decrease `max-size` to 5m
- **Long-term retention**: Use external logging service

## Security Best Practices

1. **Sensitive Data Redaction**: The middleware automatically redacts:
   - Authorization headers
   - API keys
   - Cookies
   - Passwords in request bodies

2. **Production Settings**:
   ```bash
   ENABLE_API_LOGGING=true
   ENABLE_VERBOSE_LOGGING=false  # Never true in production
   ```

3. **Access Control**: Restrict log file access:
   ```bash
   # On host machine
   chmod 600 /var/lib/docker/containers/*/json.log
   ```

4. **Regular Cleanup**: Set up log rotation and cleanup:
   ```bash
   # Cron job to clean old logs
   0 0 * * * find /var/lib/docker/containers -name "*.log" -mtime +7 -delete
   ```

## Integration with Monitoring Tools

### Prometheus Metrics

Add metrics endpoint for monitoring:
```python
# Future enhancement: Add Prometheus metrics
from prometheus_client import Counter, Histogram

request_count = Counter('http_requests_total', 'Total HTTP requests')
request_duration = Histogram('http_request_duration_seconds', 'HTTP request duration')
```

### Grafana Dashboards

Create dashboards to visualize:
- Request rate over time
- Response time percentiles
- Error rates by endpoint
- Gemini API usage and costs

## Summary

The API monitoring system provides comprehensive visibility into:
- ✅ All incoming HTTP requests with full details
- ✅ All outgoing responses with timing information
- ✅ External API calls (Gemini) with model and prompt info
- ✅ Error tracking with stack traces
- ✅ Request correlation via unique IDs
- ✅ Automatic sensitive data redaction
- ✅ Configurable verbosity levels

For questions or issues, refer to the main README.md or open an issue on GitHub.