"""
Job Radar MVP - Database Configuration
PostgreSQL connection and session management
"""

import os
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import NullPool, QueuePool
import logging

from models import Base

logger = logging.getLogger(__name__)

# Get database URL from environment variable
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/job_radar"
)

# Validate that we're using PostgreSQL
if not DATABASE_URL.startswith("postgresql"):
    logger.warning(f"WARNING: Using non-PostgreSQL database URL: {DATABASE_URL[:30]}...")
    if DATABASE_URL.startswith("sqlite"):
        logger.error("SQLite detected! This MVP requires PostgreSQL.")
        logger.error("On Replit: Go to Resources tab and add PostgreSQL database")
        logger.error("Copy the generated DATABASE_URL to your Secrets")


# Create database engine with connection pooling
# For Replit: Use QueuePool for better connection management
engine = create_engine(
    DATABASE_URL,
    # Connection pooling configuration
    poolclass=QueuePool,
    pool_size=5,           # Number of connections to keep in pool
    max_overflow=10,       # Additional connections when pool exhausted
    pool_recycle=3600,     # Recycle connections every hour (prevents timeout)
    pool_pre_ping=True,    # Test connection before using (prevent "lost connection" errors)
    echo=False,            # Set to True for SQL debug logging
    # For PostgreSQL specific
    connect_args={
        "connect_timeout": 10,
        "application_name": "job_radar_app",
        "options": "-c statement_timeout=30000"  # 30 second statement timeout
    }
)


# Create session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    expire_on_commit=False
)


def init_db():
    """
    Initialize database: create all tables if they don't exist

    Should be called once on application startup
    """
    try:
        # Test connection
        with engine.connect() as conn:
            logger.info("✓ Database connection established")

        # Create all tables
        Base.metadata.create_all(bind=engine)
        logger.info("✓ Database tables created/verified")

        return True

    except Exception as e:
        logger.error(f"✗ Database initialization failed: {str(e)}")
        raise


def get_db() -> Session:
    """
    Get database session for dependency injection in FastAPI routes

    Usage in routes:
        @app.get("/api/endpoint")
        async def endpoint(db: Session = Depends(get_db)):
            ...
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def drop_all_tables():
    """
    Drop all tables from database (for testing/reset only)

    WARNING: This deletes all data! Use only in development.
    """
    Base.metadata.drop_all(bind=engine)
    logger.warning("✓ All tables dropped")


def seed_sample_data():
    """
    Seed database with sample data for testing
    """
    from models import User, Source, JobCard

    db = SessionLocal()
    try:
        # Check if data already exists
        if db.query(User).count() > 0:
            logger.info("Sample data already exists, skipping seed")
            return

        # Create sample sources
        sources = [
            Source(
                name="pracuj.pl",
                url="https://www.pracuj.pl",
                type="website",
                description="Polish job portal",
                is_active=True
            ),
            Source(
                name="OLX",
                url="https://www.olx.pl",
                type="website",
                description="Classified ads with jobs",
                is_active=True
            ),
            Source(
                name="LinkedIn",
                url="https://www.linkedin.com",
                type="api",
                description="Professional network",
                is_active=True
            ),
            Source(
                name="Indeed",
                url="https://www.indeed.com",
                type="website",
                description="International job board",
                is_active=True
            ),
            Source(
                name="Telegram Channels",
                url="https://telegram.org",
                type="telegram",
                description="Community job announcements",
                is_active=True
            ),
        ]

        db.add_all(sources)
        db.commit()
        logger.info(f"✓ Created {len(sources)} sample sources")

        # Create sample jobs
        jobs = [
            JobCard(
                source_id=1,
                title="Python Developer",
                company="TechCorp",
                location="Gdańsk",
                description="We are looking for an experienced Python developer for our backend team.",
                salary_min=7000,
                salary_max=11000,
                currency="PLN",
                contract_type="full-time",
                work_location="on-site",
                required_skills="Python, FastAPI, PostgreSQL",
                requirements="3+ years experience, BS in CS or equivalent",
                benefits='["Health insurance", "Remote days", "Training budget"]',
                url="https://example.com/job/1",
                published_date="2026-09-15T10:00:00"
            ),
            JobCard(
                source_id=2,
                title="Data Scientist",
                company="DataWorks",
                location="Gdynia",
                description="Join our data science team to build predictive models.",
                salary_min=8000,
                salary_max=12000,
                currency="PLN",
                contract_type="full-time",
                work_location="hybrid",
                required_skills="Python, SQL, Machine Learning, TensorFlow",
                requirements="Masters in related field, 2+ years experience",
                benefits='["Flexible hours", "Home office", "Gym membership"]',
                url="https://example.com/job/2",
                published_date="2026-09-16T14:30:00"
            ),
            JobCard(
                source_id=1,
                title="Frontend Developer",
                company="WebStudio",
                location="Sopot",
                description="Build beautiful user interfaces with React and TypeScript.",
                salary_min=6000,
                salary_max=9000,
                currency="PLN",
                contract_type="full-time",
                work_location="remote",
                required_skills="React, TypeScript, CSS, Figma",
                requirements="Portfolio required, 1+ years experience",
                benefits='["Flexible schedule", "Remote", "Stock options"]',
                url="https://example.com/job/3",
                published_date="2026-09-17T09:00:00"
            ),
        ]

        db.add_all(jobs)
        db.commit()
        logger.info(f"✓ Created {len(jobs)} sample job cards")

    except Exception as e:
        logger.error(f"✗ Sample data seeding failed: {str(e)}")
        db.rollback()
        raise
    finally:
        db.close()


# Connection monitoring (for debugging)
@event.listens_for(engine, "connect")
def receive_connect(dbapi_conn, connection_record):
    """Log successful connections"""
    logger.debug("PostgreSQL connection established")


@event.listens_for(engine, "close")
def receive_close(dbapi_conn, connection_record):
    """Log connection close"""
    logger.debug("PostgreSQL connection closed")


@event.listens_for(engine, "checkin")
def receive_checkin(dbapi_conn, connection_record):
    """Log connection return to pool"""
    logger.debug("Connection returned to pool")
