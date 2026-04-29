# Fix: "Failed to load API definition - NOT FOUND /static/openapi.yaml"

## Problem
Swagger UI loads at `/api/docs` but shows error: **"Failed to load API definition - NOT FOUND /static/openapi.yaml"**

## Root Cause
The `static/` folder was not being copied into the Docker container, so the `openapi.yaml` file is not accessible.

## ✅ Solution

### The Issue
The [`Dockerfile`](Dockerfile) was missing the line to copy the `static/` folder:

```dockerfile
# Before (WRONG)
COPY src/ ./src/
COPY templates/ ./templates/
# Missing: COPY static/ ./static/

# After (CORRECT)
COPY src/ ./src/
COPY templates/ ./templates/
COPY static/ ./static/  # ← Added this line
```

### Files Fixed
1. ✅ [`Dockerfile`](Dockerfile) - Added `COPY static/ ./static/` at line 17
2. ✅ [`scripts/fix_swagger_setup.sh`](scripts/fix_swagger_setup.sh) - Updated to rebuild container

## 🚀 Apply the Fix

### Option 1: Automated (Recommended)
```bash
./scripts/fix_swagger_setup.sh
```

### Option 2: Manual Steps
```bash
# 1. Verify static folder exists
ls -la static/openapi.yaml

# 2. Stop containers
docker-compose down

# 3. Rebuild with no cache (important!)
docker-compose build --no-cache

# 4. Start containers
docker-compose up -d

# 5. Wait for startup
sleep 10

# 6. Test static file
curl http://localhost:8000/static/openapi.yaml

# 7. Test Swagger UI
open http://localhost:8000/api/docs
```

## 🧪 Verification Steps

### 1. Check Static File is Accessible
```bash
curl http://localhost:8000/static/openapi.yaml
```
**Expected:** YAML content (not 404)

### 2. Check Swagger UI Loads
```bash
curl -I http://localhost:8000/api/docs/
```
**Expected:** HTTP 200

### 3. Check Container Has Static Files
```bash
docker-compose exec app ls -la /app/static/
```
**Expected:** Should show `openapi.yaml`

### 4. Check Application Logs
```bash
docker-compose logs | grep -i swagger
```
**Expected:** 
```
✅ Swagger UI available at /api/docs
```

### 5. Open in Browser
Navigate to: **http://localhost:8000/api/docs**

**Expected:**
- ✅ Swagger UI interface loads
- ✅ "PDF Accessibility Compliance API" title visible
- ✅ All endpoints listed (3 v1 + 17 v2)
- ✅ No "Failed to load API definition" error

## 📋 Complete Checklist

Before rebuild:
- [ ] `static/openapi.yaml` exists locally
- [ ] `Dockerfile` has `COPY static/ ./static/` line
- [ ] `src/app.py` has swagger blueprint registered
- [ ] `requirements.txt` has `flask-swagger-ui` and `flasgger`

After rebuild:
- [ ] Container rebuilt with `--no-cache`
- [ ] Static file accessible: `curl http://localhost:8000/static/openapi.yaml`
- [ ] Swagger UI loads without errors
- [ ] Can test endpoints via "Try it out"

## 🔍 Troubleshooting

### Still Getting 404 on Static File?

**Check 1: Verify local file exists**
```bash
ls -la static/openapi.yaml
# Should show file with ~500 lines
```

**Check 2: Verify file in container**
```bash
docker-compose exec app cat /app/static/openapi.yaml | head -5
# Should show YAML content
```

**Check 3: Check Dockerfile**
```bash
grep "COPY static" Dockerfile
# Should show: COPY static/ ./static/
```

**Check 4: Rebuild without cache**
```bash
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

### Swagger UI Loads But Shows Different Error?

**Error: "Resolver error"**
- Check YAML syntax: `yamllint static/openapi.yaml`
- Validate OpenAPI spec: https://editor.swagger.io/

**Error: "Network error"**
- Check if app is running: `curl http://localhost:8000/health`
- Check Docker logs: `docker-compose logs -f`

**Error: "CORS error"**
- CORS is already enabled in app.py
- Check browser console for details

## 📁 File Structure

After fix, your structure should be:
```
pdf_compliance/
├── Dockerfile              ← Updated (line 17)
├── static/
│   └── openapi.yaml       ← Must exist
├── src/
│   ├── app.py             ← Swagger registered
│   └── routes/
│       └── swagger.py     ← Swagger blueprint
├── templates/
└── requirements.txt       ← Has flask-swagger-ui
```

## 🎯 Expected Result

After applying the fix and rebuilding:

1. **Static file accessible:**
   ```bash
   $ curl http://localhost:8000/static/openapi.yaml
   openapi: 3.0.0
   info:
     title: PDF Accessibility Compliance API
   ...
   ```

2. **Swagger UI loads:**
   - Navigate to http://localhost:8000/api/docs
   - See full API documentation
   - All 20 endpoints visible
   - "Try it out" buttons work

3. **No errors in logs:**
   ```bash
   $ docker-compose logs | grep -i error
   # Should be empty or no static file errors
   ```

## 💡 Why This Happened

The Dockerfile copies specific folders into the container:
- ✅ `src/` - Application code
- ✅ `templates/` - HTML templates
- ❌ `static/` - **Was missing!**

Without copying `static/`, the `openapi.yaml` file doesn't exist in the container, causing the 404 error even though:
- The file exists locally
- Flask is configured correctly
- Swagger blueprint is registered

**The fix:** Add `COPY static/ ./static/` to Dockerfile and rebuild.

## ✅ Success Indicators

You'll know it's fixed when:
1. ✅ `curl http://localhost:8000/static/openapi.yaml` returns YAML (not 404)
2. ✅ Swagger UI shows API documentation (not error message)
3. ✅ Can expand and test endpoints
4. ✅ "Try it out" buttons are functional
5. ✅ No "Failed to load API definition" error

## 🚀 Quick Fix Command

```bash
# One-liner to fix everything
docker-compose down && \
docker-compose build --no-cache && \
docker-compose up -d && \
sleep 10 && \
curl http://localhost:8000/static/openapi.yaml && \
echo "✅ Static file accessible!" && \
open http://localhost:8000/api/docs
```

---

**Need more help?** Check [`SWAGGER_404_FIX.md`](SWAGGER_404_FIX.md) for additional troubleshooting.