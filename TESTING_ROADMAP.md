# Job Radar MVP — Testing Roadmap 🗺️

**Current Status**: MVP deployed on Replit, ready for comprehensive testing  
**Date**: September 17, 2026  
**Version**: 0.1.0  

---

## 📊 Overall Progress

```
✅ Backend Architecture       - COMPLETE
✅ FastAPI Application        - COMPLETE & DEPLOYED
✅ Database (SQLite)          - COMPLETE & INITIALIZED
✅ Job Ranking Algorithm      - COMPLETE
✅ Telegram Bot FSM           - COMPLETE & READY
✅ LLM Integration            - COMPLETE & CONFIGURED
✅ Public Deployment          - COMPLETE (Replit)

🔄 API Testing               - IN PROGRESS (2/5 endpoints tested)
🔄 Telegram Bot Testing      - NOT STARTED
🔄 Integration Testing       - NOT STARTED

❌ Production Deployment     - PENDING
❌ Real Job Data Integration - PENDING
❌ LLM Testing               - PENDING (needs API key verification)
```

---

## 🎯 Phase 1: Core API Testing (This Week)

### Goal: Verify all REST endpoints work correctly

**Duration**: 2-3 hours  
**Owner**: Pavlo  
**Success Criteria**: All 5 endpoints return correct responses

### 1.1: Fix `/api/docs` Endpoint (HIGH PRIORITY)

**Current Issue**: Returns 404 instead of Swagger UI  
**Impact**: Blocks API exploration and documentation access

**Quick Checklist**:
1. [ ] Run `python diagnose.py` → check "FastAPI App" section
2. [ ] Review `main.py` → ensure `app = FastAPI(docs_url="/api/docs")`
3. [ ] Verify routes defined AFTER app creation
4. [ ] Restart Replit app (click "Run")
5. [ ] Click "Publish" for fresh URL
6. [ ] Test: `curl -I https://your-url/api/docs` → Should return 200

**Resources**: See `QUICK_FIX_API_DOCS.md` for detailed troubleshooting

**Time**: 5-15 minutes

### 1.2: Test `/api/sources` Endpoint

**Goal**: Verify job sources are accessible  
**Expected Response**: JSON array of 5 sources with metadata

```bash
curl -X GET "https://your-url/api/sources" \
  -H "Accept: application/json"
```

**Acceptance Criteria**:
- [ ] Status: 200 OK
- [ ] Returns array of sources
- [ ] Each source has: id, name, url, status, last_updated
- [ ] Total count matches database (should be 5)

**Time**: 5 minutes

### 1.3: Test `/api/jobs/{id}` Detail Endpoint

**Goal**: Verify single job retrieval works  
**Expected Response**: Complete job card with all fields

```bash
# Get job 1
curl -X GET "https://your-url/api/jobs/1" \
  -H "Accept: application/json"

# Try jobs 2, 3 as well
```

**Acceptance Criteria**:
- [ ] Status: 200 OK for existing IDs
- [ ] Status: 404 for non-existent IDs
- [ ] Returns: id, title, company, location, salary, contract_type, etc.
- [ ] Salary fields are numeric (not strings)
- [ ] Timestamps are ISO format

**Time**: 10 minutes

### 1.4: Test `/admin` Dashboard

**Goal**: Verify admin interface loads and displays data

```bash
# Open in browser
https://your-url/admin
```

**Acceptance Criteria**:
- [ ] Page loads without errors (HTTP 200)
- [ ] Shows statistics (users, jobs, sources)
- [ ] Tables display data from database
- [ ] No JavaScript errors in console
- [ ] CSS styling applied correctly

**Time**: 5 minutes

### 1.5: Performance Baseline

**Goal**: Measure response times for optimization baseline

```bash
# Test /health endpoint response time
time curl -s https://your-url/health > /dev/null

# Test /api/jobs response time
time curl -s https://your-url/api/jobs > /dev/null

# Test /api/docs response time (after fix)
time curl -s https://your-url/api/docs > /dev/null
```

**Expected Results**:
- `/health`: <100ms (simple endpoint)
- `/api/jobs`: <500ms (list with 3 items)
- `/api/docs`: <200ms (static HTML)

**Record baseline**: _____ms, _____ms, _____ms

**Time**: 10 minutes

---

## 🤖 Phase 2: Telegram Bot Integration Testing (This Week)

### Goal: Verify bot can receive and respond to messages

**Duration**: 2-3 hours  
**Owner**: Pavlo  
**Success Criteria**: Full FSM flow works end-to-end

### 2.1: Webhook Configuration

**Goal**: Set up Telegram webhook for production mode

**Steps**:
1. [ ] Verify bot token in Replit Secrets
2. [ ] Verify app is running (Replit "Run" button)
3. [ ] Click "Publish" to get public URL
4. [ ] Run webhook setup command:
   ```bash
   curl -X POST "https://api.telegram.org/bot<TOKEN>/setWebhook" \
     -d "url=https://your-url/webhook/telegram"
   ```
5. [ ] Verify: `curl -X GET "https://api.telegram.org/bot<TOKEN>/getWebhookInfo"`

**Resources**: See `TELEGRAM_WEBHOOK_SETUP.md` for complete setup guide

**Time**: 10 minutes

### 2.2: Basic Bot Responsiveness

**Goal**: Verify bot responds to simple commands

**Test**:
1. [ ] Open Telegram
2. [ ] Find your bot (search name)
3. [ ] Send: `/start`
4. [ ] **Expected**: Bot responds with language selection in <2 seconds

**Acceptance Criteria**:
- [ ] Message received within 2 seconds
- [ ] Language selection buttons appear
- [ ] No error messages in Replit console

**Record Response Time**: _____ ms

**Time**: 5 minutes

### 2.3: FSM State Flow

**Goal**: Test complete state machine transitions

**Conversation Flow Test**:

```
1. /start
   ↓ [Select Language: Русский]
2. Language Confirmation
   ↓ [Confirm Geography: Trójmiasto]
3. Geography Confirmation
   ↓ [Input Job Type: "Python developer"]
4. Job Type Input
   ↓ [Confirm Criteria]
5. Criteria Confirmation
   ↓ [View Results]
6. Results Display (3 jobs)
   ↓ [Rate: 👍/👎]
7. After 3 jobs → Upsell
   ↓ [Plan Selection]
8. Plan Selection / Finish
```

**For Each State**:
- [ ] Message arrives in <2 seconds
- [ ] Correct state transition occurs
- [ ] Buttons/keyboards displayed correctly
- [ ] No crashes or errors
- [ ] Database is updated (optional: verify in shell)

**Time**: 20-30 minutes

### 2.4: Results Quality

**Goal**: Verify job matching algorithm works correctly

**Scenario**: Search for Python developer, 7000+ PLN, full-time, Gdańsk/Gdynia

**Expected Results**:
- [ ] Get 3 job cards (from mock data)
- [ ] Each card has: title, company, location, salary, contract type
- [ ] Cards are formatted nicely (emoji icons, clear text)
- [ ] Salary ranges shown correctly
- [ ] Match score visible (0-100)

**Acceptance Criteria**:
- [ ] At least 1 job is highly relevant (80+ score)
- [ ] All jobs match basic criteria
- [ ] No duplicate jobs
- [ ] Results appear in <3 seconds

**Time**: 10 minutes

### 2.5: Feedback Collection

**Goal**: Verify user feedback is saved to database

**Test**:
1. [ ] Get to results (cards with 👍/👎 buttons)
2. [ ] Click 👍 on first card
3. [ ] Verify response: "Thanks for feedback" or similar
4. [ ] Verify in database:
   ```bash
   # In Replit Shell
   python -c "
   from database import SessionLocal
   from models import UserFeedback
   with SessionLocal() as db:
       fb = db.query(UserFeedback).all()
       print(f'Total feedback entries: {len(fb)}')
       for f in fb[-3:]:
           print(f'  Job {f.job_id}: {f.rating}')
   "
   ```

**Acceptance Criteria**:
- [ ] Feedback is recorded in database
- [ ] Rating is saved (1=like, -1=dislike)
- [ ] Associated with correct user and job

**Time**: 10 minutes

---

## 🧠 Phase 3: Business Logic Testing (Next Week)

### Goal: Verify ranking algorithm and LLM features work correctly

**Duration**: 2-3 hours  
**Owner**: Pavlo  
**Success Criteria**: Algorithm produces sensible results

### 3.1: Ranking Algorithm Verification

**Goal**: Test all 8 scoring factors

**Scenarios to test**:

**Scenario A: Perfect Match**
- Criteria: Python dev, 7000-12000 PLN, Gdańsk, full-time
- Expected: High score (90+)

**Scenario B: Partial Match**
- Criteria: Python dev, 10000+ PLN, Kraków, part-time
- Expected: Lower score (40-60)

**Scenario C: No Match**
- Criteria: Java dev, <5000 PLN, Warsaw
- Expected: Very low score (0-20)

**Verification**:
```bash
# Check results in Telegram to see scores
# Or query database:
python -c "
from database import SessionLocal
from models import SearchResult
with SessionLocal() as db:
    results = db.query(SearchResult).all()
    for r in results:
        print(f'Job {r.job_id}: {r.match_score}')
"
```

**Time**: 20 minutes

### 3.2: LLM Integration Test (If API keys set)

**Goal**: Verify Claude/GPT integration works

**Prerequisites**:
- [ ] `ANTHROPIC_API_KEY` set in Replit Secrets OR
- [ ] `OPENAI_API_KEY` set in Replit Secrets
- [ ] `LLM_PROVIDER` set to `anthropic` or `openai`

**Test**:
1. Run Python script to test LLM service:
   ```bash
   python -c "
   from llm_service import get_llm_service
   
   service = get_llm_service()
   
   # Test language detection
   result = service.detect_language('Я ищу работу')
   print(f'Language: {result}')
   
   # Test criteria extraction
   criteria = service.extract_search_criteria('Python dev, 7000+, Gdańsk')
   print(f'Criteria: {criteria}')
   "
   ```

**Expected Output**:
```
Language: russian
Criteria: {'role': 'Python developer', 'min_salary': 7000, 'location': 'Gdańsk'}
```

**Acceptance Criteria**:
- [ ] Language detection accurate
- [ ] Criteria extraction correct
- [ ] No API errors
- [ ] Response time <5 seconds

**Time**: 15 minutes

### 3.3: Multi-Language Support

**Goal**: Test bot in all 4 languages

**Languages**: Russian (RU), English (EN), Polish (PL), Ukrainian (UK)

**For Each Language**:
1. [ ] Send `/start`
2. [ ] Select language
3. [ ] Verify all responses in that language
4. [ ] Complete 1-2 searches
5. [ ] Check results formatting

**Acceptance Criteria**:
- [ ] All messages translated correctly
- [ ] No mixed languages
- [ ] Special characters (ą, ć, ł, ń, ó, ś, ź, ż for Polish) display correctly

**Time**: 30 minutes (5 min per language + 5 setup)

---

## 🔌 Phase 4: Integration Testing (Next Week)

### Goal: Test all components working together

**Duration**: 2-3 hours

### 4.1: Database Persistence

**Goal**: Verify user data persists across sessions

**Test**:
1. [ ] Start new conversation with bot (user creates profile)
2. [ ] Get some search results
3. [ ] Rate some jobs (👍/👎)
4. [ ] Close Telegram (simulate session end)
5. [ ] Start conversation again with same bot
6. [ ] Verify: Previous searches visible, feedback persisted

**Acceptance Criteria**:
- [ ] User profile exists in database
- [ ] Search history preserved
- [ ] Feedback stored and retrievable

**Time**: 15 minutes

### 4.2: Concurrent Users

**Goal**: Test bot with multiple users simultaneously

**Test**:
1. [ ] Have 3-5 people send `/start` at same time
2. [ ] Each person progresses through FSM
3. [ ] Monitor for crashes or data corruption

**Acceptance Criteria**:
- [ ] No race conditions
- [ ] Each user has separate state
- [ ] Database consistency maintained
- [ ] No performance degradation

**Time**: 20 minutes

### 4.3: Error Handling

**Goal**: Verify graceful error handling

**Test Invalid Inputs**:
- [ ] Send empty message
- [ ] Send very long message (>4000 chars)
- [ ] Send special characters: 🎉 emoji, `<script>`, SQL injection attempts
- [ ] Send bot 10 messages in rapid succession (rate limiting)
- [ ] Disconnect during conversation (simulate network error)

**Acceptance Criteria**:
- [ ] Bot handles gracefully (no crashes)
- [ ] User gets helpful error message
- [ ] System stays stable

**Time**: 15 minutes

---

## 📊 Testing Summary Template

After completing each phase, fill in this table:

### Phase 1: API Testing
| Endpoint | Status | Response Time | Notes |
|----------|--------|---------------|-------|
| `/health` | ✅ PASS | <100ms | Working |
| `/api/jobs` | ✅ PASS | <500ms | Returns 3 items |
| `/api/docs` | ⏳ TODO | — | Needs fix |
| `/api/sources` | ⏳ TODO | — | Not tested |
| `/admin` | ⏳ TODO | — | Not tested |

### Phase 2: Bot Testing
| Feature | Status | Duration | Notes |
|---------|--------|----------|-------|
| Webhook setup | ⏳ TODO | — | — |
| /start command | ⏳ TODO | — | — |
| FSM flow | ⏳ TODO | — | — |
| Results display | ⏳ TODO | — | — |
| Feedback saving | ⏳ TODO | — | — |

---

## 🚀 Critical Path (Minimum to Launch)

These tasks MUST complete before launch:

1. [ ] **Fix `/api/docs`** (5 min)
2. [ ] **Telegram webhook setup** (10 min)
3. [ ] **Bot /start command works** (5 min)
4. [ ] **Full FSM flow works** (30 min)
5. [ ] **Results display correctly** (10 min)
6. [ ] **Database persistence verified** (10 min)
7. [ ] **No crashes under normal load** (20 min)

**Total**: ~90 minutes of focused testing

**Estimated Completion**: Today (4-5 PM)

---

## 📈 Success Metrics

After all testing completes, verify:

```
Performance:
  - API response time: <500ms ✓
  - Bot response time: <2000ms ✓
  - Database query time: <100ms ✓

Reliability:
  - 100% of requests return valid response ✓
  - 0 crashes during testing ✓
  - 0 data corruption issues ✓

User Experience:
  - FSM flow intuitive and fast ✓
  - Error messages helpful ✓
  - Results accurately ranked ✓

Completeness:
  - All 5 API endpoints working ✓
  - All 14 FSM states functioning ✓
  - All 4 languages supported ✓
```

---

## 📋 Before/After Checklist

### Before Testing
- [ ] Replit app running
- [ ] Database initialized (run `seed_data.py` if needed)
- [ ] Environment variables set (TELEGRAM_BOT_TOKEN, etc.)
- [ ] Bot token obtained from @BotFather
- [ ] Public URL obtained (click Publish)
- [ ] `diagnose.py` ran successfully

### After Testing
- [ ] All critical path items completed
- [ ] Testing summary filled in
- [ ] Known issues documented
- [ ] Next steps identified
- [ ] Ready for production OR identified blockers

---

## 🎯 Next Phase (After Testing)

Once testing is complete and MVP verified:

1. **Real Data Integration** (1-2 weeks)
   - Connect real job sources (pracuj.pl, OLX, etc.)
   - Replace mock data with live scraping

2. **Performance Optimization** (1 week)
   - Cache job results
   - Optimize database queries
   - Add background job processing

3. **Monitoring & Observability** (1 week)
   - Add logging (structured JSON)
   - Add error tracking (Sentry)
   - Add performance monitoring
   - Create admin dashboard

4. **Production Deployment** (1 week)
   - Deploy to production server (AWS/DigitalOcean)
   - Set up CI/CD pipeline
   - Configure domain/SSL
   - Set up automated backups

---

## 📞 Support & Questions

**Issues with testing?**
- Check `TESTING_GUIDE.md` for detailed steps
- Run `diagnose.py` for system status
- Review `QUICK_FIX_API_DOCS.md` for common issues
- Check Replit console for error messages

**Questions about features?**
- Review `ARCHITECTURE.md` in project docs
- Check `README.md` for API documentation
- Look at source code comments for implementation details

---

**Status**: 🧪 Testing Phase Initialized  
**Owner**: Pavlo  
**Last Updated**: 2026-09-17  
**Estimated Completion**: 2026-09-17 (same day)

Ready to start testing? Begin with **Phase 1: Core API Testing**! 🚀
