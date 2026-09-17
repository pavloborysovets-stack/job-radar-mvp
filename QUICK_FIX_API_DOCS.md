# Fix: `/api/docs` Returns 404 Error 🔧

**Issue**: When accessing `https://your-replit-url/api/docs`, getting "404 Not Found"

**Expected**: Swagger UI documentation page

---

## ⚡ Quick Fix (5 minutes)

### Step 1: Check main.py configuration

Open `main.py` and verify the FastAPI app is initialized FIRST with correct parameters:

```python
# ✅ CORRECT - Should be at the TOP of main.py
from fastapi import FastAPI

app = FastAPI(
    title="Job Radar API",
    description="Job market intelligence for Trójmiasto",
    version="0.1.0",
    docs_url="/api/docs",           # Enable Swagger docs
    redoc_url="/api/redoc",         # Enable ReDoc
    openapi_url="/api/openapi.json" # OpenAPI schema endpoint
)

# Then define routes AFTER app creation
@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.get("/api/jobs")
async def get_jobs():
    ...
```

**Common Mistakes** ❌:
```python
# ❌ WRONG - Not specifying docs_url
app = FastAPI()  # This still has /docs, not /api/docs!

# ❌ WRONG - app created AFTER imports that reference it
from main import app  # Circular import!
app = FastAPI()

# ❌ WRONG - Middleware added before routes
app.add_middleware(...)  # Should be AFTER all routes
@app.get("/health")
def health():
    ...
```

### Step 2: Reload Replit application

1. Click **"Run"** button (or **"Stop"** → **"Run"**)
2. Wait 3-5 seconds for app to start
3. Look for message: `Application startup complete` in the console

### Step 3: Republish to get fresh public URL

1. Click **"Publish"** button in Replit
2. Copy the public URL: `https://job-radar-2-zip--pavloborysovets.replit.app`
3. Try accessing: `https://job-radar-2-zip--pavloborysovets.replit.app/api/docs`

---

## 🔍 Deep Troubleshooting (If quick fix doesn't work)

### Problem 1: App crashes on startup

**Symptom**: Console shows error after clicking Run

**Solution**:

```bash
# In Replit Shell, run:
python -m py_compile main.py

# If it shows SyntaxError or ImportError, fix that first
# Common issues:
# - Missing import statements
# - Circular imports
# - Typos in file names
```

**Check**:
```python
# At the top of main.py, you need:
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware

# Later routes file imports
from telegram_bot import setup_dispatcher
from models import Base
from database import init_db, SessionLocal
from ranking import JobMatcher
from sources import get_all_sources
```

### Problem 2: Routes not loading

**Symptom**: `/health` works but `/api/docs` returns 404

**Solution**: Check that app initialization has explicit paths

```python
# ✅ Correct - explicit docs_url
app = FastAPI(docs_url="/api/docs")

# ❌ Wrong - implicit default (would be /docs, not /api/docs)
app = FastAPI()
```

**Verify**: In Replit console after startup, you should see:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
```

Check if there are any error messages about routes.

### Problem 3: CORS blocking docs

**Symptom**: Docs page loads but JavaScript fails

**Solution**: Ensure CORS middleware allows documentation:

```python
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(docs_url="/api/docs")

# Add CORS AFTER app creation, BEFORE routes
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for MVP
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Then define routes
@app.get("/health")
async def health_check():
    ...
```

### Problem 4: Cache issue

**Symptom**: Shows 404 even though `/api/docs` is in code

**Solution**: Clear browser cache and Replit cache

```bash
# In Replit Shell:

# 1. Clear Python cache
find . -type d -name __pycache__ -exec rm -rf {} +
find . -type f -name "*.pyc" -delete

# 2. Delete database cache (if using file-based DB)
rm -f job_radar.db
rm -f .replit_cache*

# 3. Restart app with Ctrl+C then click "Run" again
```

In browser:
- Press `Ctrl+Shift+Delete` (or Cmd+Shift+Delete on Mac)
- Clear cache for all time
- Reload page with `Ctrl+F5` (or Cmd+Shift+R on Mac)

---

## 🧪 Verification Steps

After applying fix, verify by testing these in order:

### Test 1: Basic health check
```bash
# Should return status 200 with JSON
curl https://your-url/health
```

### Test 2: API docs page
```bash
# Should return status 200 with HTML (Swagger UI)
curl -I https://your-url/api/docs
```

If shows:
```
HTTP/2 200    ✓ FIXED
HTTP/2 404    ✗ Still broken
```

### Test 3: OpenAPI schema
```bash
# Should return status 200 with JSON schema
curl https://your-url/api/openapi.json
```

This is the actual schema that docs uses.

### Test 4: Browser access
Open in browser:
- `https://your-url/api/docs` — Should show Swagger UI
- `https://your-url/api/redoc` — Should show ReDoc alternative
- `https://your-url/api/openapi.json` — Should show raw JSON

---

## 📋 Checklist to Apply

- [ ] **Step 1a**: Verify `app = FastAPI(docs_url="/api/docs", ...)` exists at top of main.py
- [ ] **Step 1b**: Check all `@app.get()`, `@app.post()` routes are AFTER app creation
- [ ] **Step 1c**: Verify imports are correct (no circular imports)
- [ ] **Step 2a**: Click **Run** button in Replit
- [ ] **Step 2b**: Wait for "Application startup complete" message
- [ ] **Step 2c**: Check for ERROR or EXCEPTION in console
- [ ] **Step 3a**: Click **Publish** to refresh public URL
- [ ] **Step 3b**: Copy fresh URL from Publish output
- [ ] **Step 4a**: Test with `curl https://url/health` → Should return 200
- [ ] **Step 4b**: Test with `curl -I https://url/api/docs` → Should return 200
- [ ] **Step 4c**: Open `https://url/api/docs` in browser → Should show Swagger UI

---

## 🆘 If Still Not Working

Try the **Nuclear Option** (complete restart):

### 1. Delete all cache
```bash
# Run in Replit Shell:
find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null
find . -type f -name "*.pyc" -delete 2>/dev/null
rm -f job_radar.db 2>/dev/null
```

### 2. Reinstall dependencies
```bash
pip install --upgrade -r requirements.txt --force-reinstall
```

### 3. Reinitialize database
```bash
python -c "from database import init_db; init_db()"
python seed_data.py
```

### 4. Full application restart
```bash
# Stop current run (Ctrl+C in console)
# Click "Run" button
# Wait 5 seconds
```

### 5. Test everything
```bash
python diagnose.py
```

---

## 🔗 Alternative: Use ReDoc or Raw Schema

If `/api/docs` still doesn't work, use alternatives:

### Option A: ReDoc documentation
```
https://your-url/api/redoc
```
Same content, different UI (might be faster)

### Option B: Swagger Editor
Go to: https://editor.swagger.io/

Click "File" → "Import URL" and paste:
```
https://your-url/api/openapi.json
```

This loads your API schema in public Swagger editor.

### Option C: Raw JSON Schema
```
https://your-url/api/openapi.json
```
Download and view with any JSON viewer.

---

## 📞 Debug Logs

To get detailed error information:

### Enable debug logging in main.py:
```python
import logging

# Add this right after imports
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Then in routes:
@app.get("/api/docs")
async def get_docs():
    logger.debug("Docs endpoint accessed")
    ...
```

### Check Replit console for errors:
- Look for lines starting with `ERROR:` or `EXCEPTION:`
- Copy the full error message
- Search error online or in docs

---

## ✅ Expected Output

When working correctly:

```
$ curl https://job-radar-2-zip--pavloborysovets.replit.app/health
{"status":"healthy","timestamp":"2026-09-17T08:45:21.123456","version":"0.1.0"}

$ curl -I https://job-radar-2-zip--pavloborysovets.replit.app/api/docs
HTTP/2 200
Content-Type: text/html; charset=utf-8
...

$ curl https://job-radar-2-zip--pavloborysovets.replit.app/api/openapi.json | jq . | head
{
  "openapi": "3.1.0",
  "info": {
    "title": "Job Radar API",
    "description": "Job market intelligence for Trójmiasto",
    "version": "0.1.0"
  },
  ...
}
```

In browser, `https://your-url/api/docs` shows:
```
┌─────────────────────────────────────────┐
│           Swagger UI - Job Radar        │
├─────────────────────────────────────────┤
│ [/health]                               │
│ [/api/jobs]                             │
│ [/api/sources]                          │
│ [/api/docs]                             │
│ ... (all endpoints listed)              │
└─────────────────────────────────────────┘
```

---

## 🎯 Root Cause Analysis

The 404 error typically happens due to:

1. **Wrong docs_url parameter** (using default `/docs` instead of `/api/docs`)
2. **App initialization after route definitions** (routes registered before app created)
3. **Middleware interfering** (CORS or error handlers breaking docs)
4. **Browser cache** (old 404 cached, showing even though fixed)
5. **URL not published** (using old URL before hitting Publish)

---

## ✨ After Fix

Once `/api/docs` is working:
1. You'll have interactive Swagger UI
2. Can test all endpoints right from the UI
3. Full request/response documentation
4. Auto-generated schemas for all models
5. Easy to share with team members

---

**Last updated**: 2026-09-17  
**Issue severity**: Medium (blocks development experience, not production)  
**Est. fix time**: 5-10 minutes

Good luck! 🚀
