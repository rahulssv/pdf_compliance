# Troubleshooting API Logging

## Issue: API Logs Not Appearing

If you're not seeing the API request/response logs (📥 INCOMING REQUEST, ✅ OUTGOING RESPONSE), follow these steps:

### Step 1: Rebuild Docker Containers

The logging middleware requires a rebuild to be included:

```bash
# Stop containers
docker-compose down

# Rebuild with no cache
docker-compose build --no-cache

# Start containers
docker-compose up -d
```

### Step 2: Verify Environment Variables

Check that the logging environment variables are set:

```bash
docker-compose exec pdf-compliance-api env | grep ENABLE
```

You should see:
```
ENABLE_API_LOGGING=true
ENABLE_VERBOSE_LOGGING=false
```

### Step 3: Check Middleware Initialization

Look for the middleware initialization message in logs:

```bash
docker-compose logs pdf-compliance-api | grep "API Logger"
```

You should see:
```
✅ API Logger middleware enabled (verbose=False)
```

### Step 4: Make Test Requests

Make some API requests to generate logs:

```bash
# Test health endpoint
curl http://localhost:8000/health

# Test main page
curl http://localhost:8000/

# Test API endpoint (if you have a PDF file)
curl -X POST http://localhost:8000/api/v2/analyze/upload \
  -F "file=@your-file.pdf"
```

### Step 5: View Logs

View all logs:
```bash
docker-compose logs -f pdf-compliance-api
```

Filter for API logs only:
```bash
docker-compose logs -f pdf-compliance-api | grep -E "📥|✅|🌐|INCOMING|OUTGOING|GEMINI"
```

## Common Issues and Solutions

### Issue: "API Logger middleware disabled" message

**Cause:** `ENABLE_API_LOGGING` is not set to `true`

**Solution:**
```bash
# Edit docker-compose.yml and ensure:
environment:
  - ENABLE_API_LOGGING=true
  
# Then rebuild:
docker-compose down
docker-compose up -d --build
```

### Issue: Dependency warnings about urllib3

**Cause:** Version mismatch in requirements.txt

**Solution:** Already fixed in the updated `requirements.txt`. Rebuild:
```bash
docker-compose build --no-cache
docker-compose up -d
```

### Issue: Logs show service activity but no HTTP request details

**Cause:** Gunicorn access logs not configured

**Solution:** Already fixed in updated `Dockerfile`. Rebuild:
```bash
docker-compose build --no-cache
docker-compose up -d
```

### Issue: Want to see full request/response bodies

**Solution:** Enable verbose logging:

1. Edit `docker-compose.yml`:
```yaml
environment:
  - ENABLE_VERBOSE_LOGGING=true
```

2. Rebuild:
```bash
docker-compose down
docker-compose up -d --build
```

⚠️ **Warning:** Verbose logging includes full request/response bodies. Not recommended for production!

## Quick Test Script

Use the provided test script:

```bash
./test_api_logging.sh
```

This will:
1. Rebuild containers
2. Wait for service to start
3. Make test requests
4. Show recent logs
5. Filter for API logs

## Expected Log Output

After making a request, you should see logs like:

```
📥 INCOMING REQUEST: {
  "request_id": "1714305234567",
  "timestamp": "2024-04-28 12:30:34",
  "method": "GET",
  "url": "http://localhost:8000/health",
  "path": "/health"
}

✅ OUTGOING RESPONSE: {
  "request_id": "1714305234567",
  "status_code": 200,
  "duration_ms": 15.23
}
```

For Gemini API calls:
```
🌐 GEMINI API CALL: {
  "timestamp": "2024-04-28 12:30:35",
  "service": "Gemini API",
  "model": "gemini-2.5-flash",
  "prompt_length": 1024
}
```

## Still Not Working?

1. **Check if middleware is loaded:**
   ```bash
   docker-compose exec pdf-compliance-api python -c "from src.middleware import APILogger; print('✅ Middleware module loaded')"
   ```

2. **Check Flask app initialization:**
   ```bash
   docker-compose exec pdf-compliance-api python -c "from src.app import create_app; app = create_app(); print('✅ App created')"
   ```

3. **View all container logs:**
   ```bash
   docker-compose logs --tail 200 pdf-compliance-api
   ```

4. **Check container environment:**
   ```bash
   docker-compose exec pdf-compliance-api env
   ```

5. **Restart with fresh build:**
   ```bash
   docker-compose down -v
   docker-compose build --no-cache
   docker-compose up -d
   ```

## Manual Verification

If you want to verify the middleware is working without Docker:

```bash
# Activate virtual environment
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export ENABLE_API_LOGGING=true
export ENABLE_VERBOSE_LOGGING=false
export GEMINI_API_KEY=your_key_here

# Run the app
python -m src.app
```

Then in another terminal:
```bash
curl http://localhost:8000/health
```

You should see the API logs in the first terminal.

## Need More Help?

1. Check the full documentation: [docs/API_MONITORING_GUIDE.md](docs/API_MONITORING_GUIDE.md)
2. Review the quick start: [docs/API_LOGGING_QUICK_START.md](docs/API_LOGGING_QUICK_START.md)
3. Check the implementation summary: [API_LOGGING_IMPLEMENTATION_SUMMARY.md](API_LOGGING_IMPLEMENTATION_SUMMARY.md)