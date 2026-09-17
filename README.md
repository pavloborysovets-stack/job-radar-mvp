# Job Radar MVP 🎯

**A multilingual job market intelligence platform for Trójmiasto region**

- 🤖 **Telegram Bot** with natural language search
- 🏆 **Smart Job Ranking** with 8 scoring factors
- 🌍 **4 Languages**: Russian, English, Polish, Ukrainian
- ⚡ **FastAPI Backend** with PostgreSQL
- 🧠 **LLM Integration** (Claude/OpenAI)

---

## Quick Start (5 minutes)

### Prerequisites
- ✅ Replit account (free at replit.com)
- ✅ Telegram app installed
- ✅ Bot token from @BotFather (optional, for full testing)

### Step 1: Create Replit Project

1. Go to [replit.com](https://replit.com)
2. Click **"Create"** → **"Import from GitHub"**
3. Paste this repo URL: `https://github.com/your/job-radar` (or upload files)
4. Wait for import to complete

### Step 2: Set Up PostgreSQL Database

1. In Replit, click **"Resources"** tab (top menu)
2. Click **"Create Database"** → **PostgreSQL**
3. Wait ~30 seconds for database to initialize
4. Click on database name to view credentials
5. Click **"Show credentials"** and copy the connection string
6. In Replit, click **"Secrets"** (lock icon) in left sidebar
7. Add new secret:
   - **Key**: `DATABASE_URL`
   - **Value**: Paste the connection string from step 5
8. Click **"Add secret"**

### Step 3: Set Up Telegram Bot (Optional but Recommended)

1. Open Telegram app
2. Search for **@BotFather**
3. Send: `/newbot`
4. Follow prompts:
   - Bot name: `Job Radar Bot` (or your choice)
   - Bot username: `job_radar_yourname_bot` (must be unique)
5. BotFather sends you a token
6. Copy the token and add to Replit Secrets:
   - **Key**: `TELEGRAM_BOT_TOKEN`
   - **Value**: Paste the token
   - Click **"Add secret"**

### Step 4: Start the Application

1. Click **"Run"** button in Replit
2. Wait for "Application startup complete" message
3. Click **"Publish"** to get public URL
4. Copy the public URL: `https://job-radar-xxx.replit.app`

### Step 5: Set Up Telegram Webhook (Optional)

In Replit Shell, run:

```bash
curl -X POST "https://api.telegram.org/bot<YOUR_BOT_TOKEN>/setWebhook" \
  -d "url=https://your-replit-url/webhook/telegram"
```

Replace:
- `<YOUR_BOT_TOKEN>` with your actual token
- `https://your-replit-url` with your Replit public URL

### Step 6: Test Everything

1. **Test API**: Visit `https://your-url/health` → Should return JSON
2. **Test Docs**: Visit `https://your-url/api/docs` → Should show Swagger UI
3. **Test Bot**: Open Telegram, find your bot, send `/start`

---

## Architecture

```
┌─────────────────────────────────────────────────┐
│         Telegram Bot (telegram_bot.py)          │
│  14-state FSM with multilingual support         │
└──────────────┬──────────────────────────────────┘
               │
┌──────────────▼──────────────────────────────────┐
│      FastAPI Backend (main.py)                  │
│  ├─ /health               - Health check        │
│  ├─ /api/jobs             - Get jobs list       │
│  ├─ /api/jobs/{id}        - Get job detail      │
│  ├─ /api/sources          - Get job sources     │
│  ├─ /admin                - Admin dashboard     │
│  ├─ /api/docs             - Swagger UI          │
│  └─ /webhook/telegram     - Telegram webhook    │
└──────────────┬──────────────────────────────────┘
               │
┌──────────────▼──────────────────────────────────┐
│    Business Logic Layer                         │
│  ├─ ranking.py            - Job ranking (8 factors)
│  ├─ sources.py            - Job sources adapter │
│  ├─ llm_service.py        - LLM integration     │
│  └─ config.py             - Configuration      │
└──────────────┬──────────────────────────────────┘
               │
┌──────────────▼──────────────────────────────────┐
│    Data Layer                                   │
│  ├─ models.py             - SQLAlchemy ORM      │
│  ├─ database.py           - PostgreSQL conn     │
│  └─ PostgreSQL Database   - Job data storage    │
└─────────────────────────────────────────────────┘
```

---

## Project Structure

```
job-radar/
├── main.py                 # FastAPI application
├── models.py              # Database models (User, Job, etc)
├── database.py            # PostgreSQL configuration
├── config.py              # Environment configuration
├── telegram_bot.py        # Telegram bot FSM (14 states)
├── ranking.py             # Job ranking algorithm (8 factors)
├── sources.py             # Job source adapters (5 sources)
├── llm_service.py         # LLM integration (Claude/GPT)
├── requirements.txt       # Python dependencies
├── .env.example           # Environment variables template
├── README.md              # This file
│
├── docs/
│   ├── ARCHITECTURE.md    # Detailed architecture
│   ├── TESTING_ROADMAP.md # Testing guide
│   └── QUICK_FIX_API_DOCS.md # Troubleshooting
│
└── tests/
    ├── test_ranking.py
    ├── test_sources.py
    └── test_telegram_bot.py
```

---

## Telegram Bot Flow (14 States)

```
/start
  ↓
1. LANGUAGE_SELECT (Русский, English, Polski, Українська)
  ↓
2. GEOGRAPHY_CONFIRM (Трójmiasto?)
  ↓
3. JOB_TYPE_INPUT ("Python developer, 7000+, Gdańsk")
  ↓
4. SALARY_INPUT (7000)
  ↓
5. CONTRACT_SELECT (Full-time, Part-time, Contract)
  ↓
6. CRITERIA_CONFIRM (Confirm search criteria)
  ↓
7. RESULTS_DISPLAY (Show job 1/3)
  ↓
8-11. FEEDBACK (👍 Like / 👎 Dislike)
  ↓
(Next job...)
  ↓
12. PLAN_SELECT (Upsell to premium)
  ↓
13. PAYMENT (Handle payment - future)
  ↓
14. END (Goodbye)
```

---

## Job Ranking Algorithm (8 Factors)

Each job gets a score 0-100 based on:

| Factor | Weight | Explanation |
|--------|--------|-------------|
| **Criteria Match** | 25% | Must-have role requirements |
| **Salary Match** | 20% | Salary range alignment |
| **Location Match** | 15% | Geographic preference |
| **Contract Type** | 15% | Employment type preference |
| **Skills Match** | 10% | Required technical skills |
| **Language** | 5% | Language requirements |
| **Recency** | 5% | How recent is the posting |
| **Exclusions** | -10% | Penalty for excluded keywords |

**Example**:
```
Python Developer job:
- Criteria Match: 95 (exact role)
- Salary Match: 100 (8000 PLN, user wanted 7000+)
- Location Match: 100 (Gdańsk, Trójmiasto)
- Contract Match: 100 (full-time)
- Skills Match: 90 (Python, FastAPI, SQL - has all)
- Language Match: 80 (job description in English)
- Recency: 100 (posted 2 days ago)
- Exclusions: 0 (no excluded keywords)

FINAL SCORE: 88/100 ⭐
```

---

## Environment Variables

Required:
- `DATABASE_URL` - PostgreSQL connection string
- `TELEGRAM_BOT_TOKEN` - Telegram bot token

Optional:
- `ANTHROPIC_API_KEY` - Claude API (for LLM features)
- `OPENAI_API_KEY` - GPT API (alternative)
- `LLM_PROVIDER` - "anthropic" or "openai"
- `DEBUG` - true/false
- `API_PORT` - 8000

See `.env.example` for full list.

---

## API Endpoints

### Health Check
```bash
GET /health
# Response: {"status": "healthy", "version": "0.1.0"}
```

### Get Jobs List
```bash
GET /api/jobs?limit=10&offset=0
# Response: {"total": 45, "items": [...]}
```

### Get Job Details
```bash
GET /api/jobs/1
# Response: {"id": 1, "title": "Python Dev", "company": "TechCorp", ...}
```

### Get Job Sources
```bash
GET /api/sources
# Response: {"total": 5, "sources": [...]}
```

### Admin Dashboard
```bash
GET /admin
# Response: HTML dashboard with stats
```

### Documentation
```
GET /api/docs       # Swagger UI
GET /api/redoc      # ReDoc
GET /api/openapi.json  # OpenAPI schema
```

---

## Testing

### Test Endpoints with cURL

```bash
# Test health
curl https://your-url/health

# Test jobs
curl https://your-url/api/jobs

# Test docs
curl -I https://your-url/api/docs
```

### Test Telegram Bot

1. Find your bot in Telegram (search by username)
2. Send `/start`
3. Should see language selection buttons
4. Follow the conversation flow

### Automated Tests

```bash
# Run tests
pytest tests/

# With coverage
pytest --cov=. tests/
```

---

## Troubleshooting

### Problem: Database connection error

**Solution**:
1. Check DATABASE_URL is set in Secrets
2. Verify PostgreSQL is active in Replit Resources
3. Restart Replit app (click Run)

### Problem: /api/docs returns 404

**Solution**:
1. Check `docs_url="/api/docs"` is in main.py FastAPI config
2. Restart Replit app
3. Click "Publish" for fresh URL

### Problem: Telegram bot not responding

**Solution**:
1. Check TELEGRAM_BOT_TOKEN is set correctly
2. Webhook configured? Run: 
   ```bash
   curl -X GET "https://api.telegram.org/bot<TOKEN>/getWebhookInfo"
   ```
3. Check Replit console for errors

### Problem: LLM features not working

**Solution**:
- LLM is optional! Bot works without it
- To enable: Set ANTHROPIC_API_KEY or OPENAI_API_KEY

See `QUICK_FIX_API_DOCS.md` for more troubleshooting.

---

## Deployment to Production

After testing on Replit:

### Option 1: Keep on Replit (Easy)
- Replit projects stay online 24/7 with Boost
- Simple to manage and update

### Option 2: Deploy to AWS/DigitalOcean (Scalable)
- Better performance
- More control over infrastructure
- Requires: Docker, server setup

### Option 3: Use Heroku (Simple)
- Free tier available
- Automatic deployments from GitHub
- See `docs/DEPLOYMENT.md`

---

## Performance Targets

| Metric | Target | Status |
|--------|--------|--------|
| API response time | <500ms | ✅ |
| Bot response time | <2s | ✅ |
| Database query | <100ms | ✅ |
| Webhook latency | <1s | ✅ |
| Job ranking | <500ms | ✅ |

---

## Monitoring & Logs

View logs in Replit console:

```bash
# Follow logs in real-time
tail -f /tmp/job_radar.log

# View recent errors
grep ERROR /tmp/job_radar.log

# View debug info
grep DEBUG /tmp/job_radar.log
```

---

## Database Schema

8 tables:
1. **users** - Telegram users
2. **search_profiles** - User search preferences
3. **job_cards** - Job listings
4. **sources** - Job sources
5. **search_results** - Ranked results
6. **user_feedback** - User ratings
7. **payments** - Subscription info (future)
8. **active_periods** - Active subscriptions (future)

---

## Future Enhancements

### Phase 2: Real Data
- Connect to pracuj.pl API
- Add OLX scraping
- LinkedIn integration
- Real job data instead of mock

### Phase 3: Intelligence
- Improved ranking algorithm
- Better NLP/LLM integration
- Notification system
- Saved job searches

### Phase 4: Monetization
- Premium subscription plans
- Better job matching
- API for other platforms
- White-label options

---

## Support

**Having issues?**

1. Check `QUICK_FIX_API_DOCS.md` for common problems
2. Review `TESTING_ROADMAP.md` for testing guide
3. Check Replit console for error messages
4. Run `python diagnose.py` to check system status

**Need help?**

- 📖 Documentation: See `docs/` folder
- 🐛 Bug report: Check existing issues or create new one
- 💬 Questions: Start a discussion

---

## License

MIT License - See LICENSE file

---

## Changelog

### v0.1.0 (MVP)
- ✅ FastAPI backend
- ✅ Telegram bot with FSM
- ✅ Job ranking algorithm (8 factors)
- ✅ PostgreSQL database
- ✅ LLM integration (Claude/GPT)
- ✅ 4 language support
- ✅ Mock job data
- ✅ Admin dashboard

### v0.2.0 (Planned)
- Real job scraping
- Payment integration
- Notification system
- Advanced search filters

---

## Credits

**Built with**:
- FastAPI - Web framework
- Telegram Bot API - Chat interface
- PostgreSQL - Database
- Anthropic Claude - LLM
- OpenAI GPT - LLM alternative

---

## Questions?

Start with these resources:
1. **Installation**: This README
2. **Testing**: `TESTING_ROADMAP.md`
3. **Architecture**: `docs/ARCHITECTURE.md`
4. **Troubleshooting**: `QUICK_FIX_API_DOCS.md`
5. **API Setup**: `TELEGRAM_WEBHOOK_SETUP.md`

**Status**: 🟢 Ready for testing on Replit

Good luck! 🚀
