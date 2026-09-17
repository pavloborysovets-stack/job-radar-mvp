"""
Job Radar MVP - FastAPI Backend
Production-ready with PostgreSQL support
"""

from fastapi import FastAPI, HTTPException, Query, Depends
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
from datetime import datetime

from database import init_db, SessionLocal
from models import Base
from config import get_settings
from telegram_bot import TelegramBotHandler

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

settings = get_settings()

# Global reference so we can stop it cleanly on shutdown
bot_handler: TelegramBotHandler | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    # Startup
    global bot_handler
    logger.info("🚀 Job Radar MVP Starting...")
    try:
        init_db()
        logger.info("✅ Database initialized")
    except Exception as e:
        logger.error(f"❌ Database init failed: {e}")

    if settings.telegram_bot_token:
        try:
            bot_handler = TelegramBotHandler(settings.telegram_bot_token)
            await bot_handler.start_polling_background()
        except Exception as e:
            logger.error(f"❌ Telegram bot failed to start: {e}")
    else:
        logger.warning("⚠ TELEGRAM_BOT_TOKEN not set - bot not started")

    yield
    # Shutdown
    if bot_handler:
        await bot_handler.stop()
    logger.info("🛑 Job Radar MVP Shutting down...")


# Initialize FastAPI app with CORRECT docs configuration
app = FastAPI(
    title="Job Radar API",
    description="Job market intelligence platform for Trójmiasto region",
    version="0.1.0",
    docs_url="/api/docs",           # ✅ Swagger UI
    redoc_url="/api/redoc",         # ✅ ReDoc
    openapi_url="/api/openapi.json", # ✅ OpenAPI schema
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# HEALTH CHECK ENDPOINT
# ============================================================================

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "0.1.0",
        "service": "Job Radar MVP"
    }


# ============================================================================
# API ENDPOINTS
# ============================================================================

@app.get("/api/jobs")
async def get_jobs(limit: int = Query(10, ge=1, le=100), offset: int = Query(0, ge=0)):
    """Get list of jobs with pagination"""
    from models import JobCard

    db = SessionLocal()
    try:
        total = db.query(JobCard).count()
        jobs = db.query(JobCard).limit(limit).offset(offset).all()

        return {
            "total": total,
            "limit": limit,
            "offset": offset,
            "items": [
                {
                    "id": job.id,
                    "title": job.title,
                    "company": job.company,
                    "location": job.location,
                    "salary_min": job.salary_min,
                    "salary_max": job.salary_max,
                    "currency": job.currency,
                    "contract_type": job.contract_type,
                    "url": job.url,
                    "published_date": job.published_date.isoformat() if job.published_date else None,
                }
                for job in jobs
            ]
        }
    finally:
        db.close()


@app.get("/api/jobs/{job_id}")
async def get_job(job_id: int):
    """Get single job by ID"""
    from models import JobCard

    db = SessionLocal()
    try:
        job = db.query(JobCard).filter(JobCard.id == job_id).first()
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")

        return {
            "id": job.id,
            "title": job.title,
            "company": job.company,
            "location": job.location,
            "salary_min": job.salary_min,
            "salary_max": job.salary_max,
            "currency": job.currency,
            "contract_type": job.contract_type,
            "description": job.description,
            "requirements": job.requirements,
            "benefits": job.benefits or [],
            "url": job.url,
            "published_date": job.published_date.isoformat() if job.published_date else None,
        }
    finally:
        db.close()


@app.get("/api/sources")
async def get_sources():
    """Get list of job sources"""
    from models import Source

    db = SessionLocal()
    try:
        sources = db.query(Source).all()
        return {
            "total": len(sources),
            "sources": [
                {
                    "id": source.id,
                    "name": source.name,
                    "url": source.url,
                    "type": source.type,
                    "status": "active",
                    "last_updated": source.updated_at.isoformat() if source.updated_at else None,
                }
                for source in sources
            ]
        }
    finally:
        db.close()


# ============================================================================
# ADMIN DASHBOARD
# ============================================================================

@app.get("/admin")
async def admin_dashboard():
    """Admin dashboard with statistics"""
    from models import User, JobCard, Source, UserFeedback

    db = SessionLocal()
    try:
        users_count = db.query(User).count()
        jobs_count = db.query(JobCard).count()
        sources_count = db.query(Source).count()
        feedback_count = db.query(UserFeedback).count()

        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Job Radar Admin Dashboard</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }}
                .dashboard {{ max-width: 1200px; margin: 0 auto; }}
                .header {{ background: #2c3e50; color: white; padding: 20px; border-radius: 5px; margin-bottom: 20px; }}
                .stats {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin-bottom: 20px; }}
                .stat-card {{ background: white; padding: 20px; border-radius: 5px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }}
                .stat-number {{ font-size: 32px; font-weight: bold; color: #3498db; }}
                .stat-label {{ color: #7f8c8d; margin-top: 10px; }}
                table {{ width: 100%; border-collapse: collapse; background: white; }}
                th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }}
                th {{ background: #34495e; color: white; }}
            </style>
        </head>
        <body>
            <div class="dashboard">
                <div class="header">
                    <h1>📊 Job Radar Admin Dashboard</h1>
                    <p>Real-time statistics and monitoring</p>
                </div>

                <div class="stats">
                    <div class="stat-card">
                        <div class="stat-number">{users_count}</div>
                        <div class="stat-label">👥 Total Users</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number">{jobs_count}</div>
                        <div class="stat-label">💼 Job Cards</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number">{sources_count}</div>
                        <div class="stat-label">📍 Sources</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number">{feedback_count}</div>
                        <div class="stat-label">💬 Feedback Items</div>
                    </div>
                </div>

                <h2>System Status</h2>
                <table>
                    <tr>
                        <th>Component</th>
                        <th>Status</th>
                        <th>Value</th>
                    </tr>
                    <tr>
                        <td>Database</td>
                        <td>✅ Connected</td>
                        <td>PostgreSQL</td>
                    </tr>
                    <tr>
                        <td>API Health</td>
                        <td>✅ Running</td>
                        <td>Job Radar MVP v0.1.0</td>
                    </tr>
                    <tr>
                        <td>Timestamp</td>
                        <td>✅ Synced</td>
                        <td>{datetime.utcnow().isoformat()}</td>
                    </tr>
                </table>
            </div>
        </body>
        </html>
        """
        return HTMLResponse(content=html)
    finally:
        db.close()


# ============================================================================
# TELEGRAM WEBHOOK
# ============================================================================

@app.post("/webhook/telegram")
async def telegram_webhook(update: dict):
    """Handle Telegram webhook updates"""
    logger.info(f"Received Telegram update: {update}")
    # TODO: Implement telegram bot handler
    return {"ok": True}


# ============================================================================
# ROOT ENDPOINT
# ============================================================================

@app.get("/")
async def root():
    """Root endpoint with documentation links"""
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Job Radar MVP</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; background: #f0f2f5; }
            .container { max-width: 600px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
            h1 { color: #2c3e50; }
            .link { display: block; margin: 10px 0; padding: 10px; background: #3498db; color: white; text-decoration: none; border-radius: 5px; }
            .link:hover { background: #2980b9; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🎯 Job Radar MVP</h1>
            <p>Job market intelligence platform for Trójmiasto region</p>
            <p><strong>Version 0.1.0</strong></p>

            <h2>📚 Documentation</h2>
            <a class="link" href="/api/docs">📖 Swagger UI Documentation</a>
            <a class="link" href="/api/redoc">📚 ReDoc Documentation</a>
            <a class="link" href="/api/openapi.json">🔗 OpenAPI Schema</a>

            <h2>🔧 Management</h2>
            <a class="link" href="/admin">📊 Admin Dashboard</a>

            <h2>✅ Health Check</h2>
            <a class="link" href="/health">💚 System Health</a>
        </div>
    </body>
    </html>
    """
    return HTMLResponse(content=html)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=settings.api_port, reload=settings.debug)
