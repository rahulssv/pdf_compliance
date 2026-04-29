# Fixing Swagger UI 404 Error

## Problem
Getting 404 error when accessing `/api/docs` endpoint.

## Root Causes
1. ❌ Missing dependencies (`flask-swagger-ui`, `flasgger`)
2. ❌ Swagger blueprint not imported in `src/app.py`
3. ❌ Swagger blueprint not registered in `src/app.py`
4. ❌ Missing `static/openapi.yaml` file
5. ❌ Application not restarted after changes

## ✅ Solution Applied

I've fixed all the issues:

### 1. Updated `requirements.txt`
Added the required dependencies:
```
flask-swagger-ui==4.11.1
flasgger==0.9.7.1
pytest-html==3.2.0
```

### 2. Updated `src/app.py`
- **Line 11**: Added import: `from src.routes.swagger import swagger_bp`
- **Line 50**: Registered blueprint: `app.register_blueprint(swagger_bp, url_prefix='/api/docs')`
- **Line 51**: Added log message

### 3. Created `static/openapi.yaml`
Complete OpenAPI 3.0 specification with all v1 and v2 endpoints.

### 4. Created `src/routes/swagger.py`
Swagger UI blueprint configuration.

## 🚀 Quick Fix (Run This)

```bash
# Option 1: Automated fix script
./scripts/fix_swagger_setup.sh

# Option 2: Manual steps
pip install flask-swagger-ui flasgger pytest-html
docker-compose down
docker-compose up --build -d
```

## 🧪 Verify the Fix

```bash
# 1. Check health endpoint
curl http://localhost:8000/health

# 2. Check static file is accessible
curl http://localhost:8000/static/openapi.yaml

# 3. Check Swagger UI
curl -I http://localhost:8000/api/docs/

# 4. Open in browser
open http://localhost:8000/api/docs
```

## 📋 Verification Checklist

Run these commands to verify everything is set up correctly:

```bash
# Check if dependencies are installed
pip list | grep -E "flask-swagger-ui|flasgger"

# Check if swagger.py exists
ls -la src/routes/swagger.py

# Check if openapi.yaml exists
ls -la static/openapi.yaml

# Check if swagger is imported in app.py
grep "swagger" src/app.py

# Check application logs
docker-compose logs | grep -i swagger
```

Expected output:
```
✅ flask-swagger-ui    4.11.1
✅ flasgger           0.9.7.1
✅ src/routes/swagger.py exists
✅ static/openapi.yaml exists
✅ "from src.routes.swagger import swagger_bp" found
✅ "app.register_blueprint(swagger_bp" found
✅ "Swagger UI available at /api/docs" in logs
```

## 🔍 Still Getting 404?

### Debug Steps

1. **Check if application restarted:**
   ```bash
   docker-compose ps
   docker-compose logs -f
   ```

2. **Verify blueprint registration:**
   ```bash
   grep -n "swagger" src/app.py
   ```
   Should show:
   - Line 11: Import statement
   - Line 50: Blueprint registration
   - Line 51: Log message

3. **Test static file serving:**
   ```bash
   curl http://localhost:8000/static/openapi.yaml
   ```
   Should return YAML content, not 404.

4. **Check Flask static folder:**
   ```bash
   grep "static_folder" src/app.py
   ```
   Should show: `static_folder=str(repo_root / "static")`

5. **Verify swagger_bp is created:**
   ```bash
   cat src/routes/swagger.py | grep "swagger_bp"
   ```

### Common Issues

**Issue 1: Import Error**
```
ImportError: cannot import name 'swagger_bp' from 'src.routes.swagger'
```
**Fix:** Ensure `src/routes/swagger.py` exists and contains `swagger_bp = get_swaggerui_blueprint(...)`

**Issue 2: Module Not Found**
```
ModuleNotFoundError: No module named 'flask_swagger_ui'
```
**Fix:** Install dependencies:
```bash
pip install flask-swagger-ui flasgger
# Then rebuild Docker
docker-compose up --build -d
```

**Issue 3: Static File 404**
```
GET /static/openapi.yaml 404
```
**Fix:** Verify static folder exists and contains openapi.yaml:
```bash
ls -la static/openapi.yaml
```

**Issue 4: Blueprint Not Registered**
```
No logs showing "Swagger UI available at /api/docs"
```
**Fix:** Check app.py has both import and registration:
```bash
grep -A 2 "swagger" src/app.py
```

## 🎯 Expected Behavior After Fix

1. **Application starts successfully:**
   ```
   ✅ Blueprints registered (API prefix: /api/v1)
   ✅ Swagger UI available at /api/docs
   ```

2. **Swagger UI loads:**
   - Navigate to `http://localhost:8000/api/docs`
   - See interactive API documentation
   - All endpoints listed and testable

3. **Static file accessible:**
   ```bash
   curl http://localhost:8000/static/openapi.yaml
   # Returns YAML content
   ```

## 📞 Need More Help?

If you're still experiencing issues:

1. **Share logs:**
   ```bash
   docker-compose logs > logs.txt
   ```

2. **Verify file structure:**
   ```bash
   tree -L 3 -I '__pycache__|*.pyc'
   ```

3. **Check Python environment:**
   ```bash
   pip list | grep flask
   python --version
   ```

## ✅ Success!

Once fixed, you should see:
- ✅ No 404 errors in logs
- ✅ Swagger UI loads at `/api/docs`
- ✅ All 20 endpoints visible (3 v1 + 17 v2)
- ✅ "Try it out" buttons work
- ✅ Can test endpoints interactively

**Swagger UI URL:** http://localhost:8000/api/docs