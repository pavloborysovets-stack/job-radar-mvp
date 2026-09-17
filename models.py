"""
Job Radar MVP - Database Models
SQLAlchemy ORM models for PostgreSQL
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text, ForeignKey, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

Base = declarative_base()


class User(Base):
    """Telegram user profile"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(Integer, unique=True, index=True)
    telegram_username = Column(String(255), nullable=True)
    first_name = Column(String(255), nullable=True)
    last_name = Column(String(255), nullable=True)
    language = Column(String(2), default="ru")  # ru, en, pl, uk
    geography = Column(String(50), default="trojmiasto")  # trojmiasto, other
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    profiles = relationship("SearchProfile", back_populates="user")
    feedbacks = relationship("UserFeedback", back_populates="user")
    payments = relationship("Payment", back_populates="user")

    def __repr__(self):
        return f"<User {self.telegram_id} ({self.first_name})>"


class SearchProfile(Base):
    """User's saved search preferences"""
    __tablename__ = "search_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)

    # Search criteria
    job_title = Column(String(255))  # "Python developer", "Data scientist", etc.
    min_salary = Column(Integer, nullable=True)
    max_salary = Column(Integer, nullable=True)
    currency = Column(String(3), default="PLN")

    # Job preferences
    contract_types = Column(String(255))  # "full-time,part-time,contract"
    work_location = Column(String(100))  # "remote,on-site,hybrid"
    experience_level = Column(String(50))  # "junior,mid,senior"

    # Additional preferences
    required_skills = Column(Text, nullable=True)  # JSON or comma-separated
    excluded_keywords = Column(Text, nullable=True)
    nice_to_have = Column(Text, nullable=True)

    # Status
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="profiles")
    results = relationship("SearchResult", back_populates="profile")

    def __repr__(self):
        return f"<SearchProfile {self.job_title}>"


class JobCard(Base):
    """Job listing"""
    __tablename__ = "job_cards"

    id = Column(Integer, primary_key=True, index=True)
    source_id = Column(Integer, ForeignKey("sources.id"), index=True)

    # Job information
    title = Column(String(255), index=True)
    company = Column(String(255), index=True)
    location = Column(String(255), index=True)
    description = Column(Text)

    # Salary information
    salary_min = Column(Integer, nullable=True)
    salary_max = Column(Integer, nullable=True)
    currency = Column(String(3), default="PLN")

    # Job details
    contract_type = Column(String(50))  # "full-time", "part-time", "contract"
    work_location = Column(String(50))  # "on-site", "remote", "hybrid"

    # Requirements
    required_skills = Column(Text, nullable=True)
    requirements = Column(Text, nullable=True)
    benefits = Column(Text, nullable=True)  # JSON array as string

    # External link
    url = Column(String(1024), unique=True, index=True)

    # Metadata
    published_date = Column(DateTime, nullable=True)
    scraped_date = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    source = relationship("Source", back_populates="jobs")
    results = relationship("SearchResult", back_populates="job")
    feedbacks = relationship("UserFeedback", back_populates="job")

    def __repr__(self):
        return f"<JobCard {self.title} at {self.company}>"


class Source(Base):
    """Job source (website, API, etc.)"""
    __tablename__ = "sources"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, index=True)
    url = Column(String(1024))
    type = Column(String(50))  # "website", "api", "telegram", "linkedin"
    description = Column(Text, nullable=True)

    # Configuration
    is_active = Column(Boolean, default=True)
    update_frequency = Column(String(50))  # "daily", "weekly", "on_demand"
    last_updated = Column(DateTime, nullable=True)

    # Statistics
    total_jobs = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    jobs = relationship("JobCard", back_populates="source")

    def __repr__(self):
        return f"<Source {self.name}>"


class SearchResult(Base):
    """Result of a job search (job + match score)"""
    __tablename__ = "search_results"

    id = Column(Integer, primary_key=True, index=True)
    profile_id = Column(Integer, ForeignKey("search_profiles.id"), index=True)
    job_id = Column(Integer, ForeignKey("job_cards.id"), index=True)

    # Match score (0-100)
    match_score = Column(Integer)  # 0-100

    # Scoring breakdown
    criteria_match = Column(Integer)  # Must-have criteria score
    salary_match = Column(Integer)  # Salary range match
    location_match = Column(Integer)  # Geography match
    contract_match = Column(Integer)  # Contract type match
    skills_match = Column(Integer)  # Required skills match
    language_match = Column(Integer)  # Language proficiency match
    recency_score = Column(Integer)  # How recent is the job
    exclusion_score = Column(Integer)  # Penalty for exclusions

    # Status
    is_shown = Column(Boolean, default=True)  # Whether to show to user
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    profile = relationship("SearchProfile", back_populates="results")
    job = relationship("JobCard", back_populates="results")

    def __repr__(self):
        return f"<SearchResult job={self.job_id} score={self.match_score}>"


class UserFeedbackType(str, enum.Enum):
    """Types of user feedback"""
    LIKE = "like"
    DISLIKE = "dislike"
    APPLIED = "applied"
    SAVED = "saved"
    REPORTED = "reported"


class UserFeedback(Base):
    """User feedback on jobs"""
    __tablename__ = "user_feedback"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    job_id = Column(Integer, ForeignKey("job_cards.id"), index=True)

    # Feedback type
    rating = Column(Integer)  # 1 = like, -1 = dislike, 2 = applied, etc.
    feedback_type = Column(String(50))  # like, dislike, applied, saved, reported
    notes = Column(Text, nullable=True)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="feedbacks")
    job = relationship("JobCard", back_populates="feedbacks")

    def __repr__(self):
        return f"<UserFeedback user={self.user_id} job={self.job_id} type={self.feedback_type}>"


class Payment(Base):
    """Payment and subscription information"""
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)

    # Plan information
    plan_name = Column(String(50))  # "free", "pro", "premium"
    plan_price = Column(Float)
    currency = Column(String(3), default="PLN")

    # Payment details
    payment_method = Column(String(50))  # "stripe", "paypal", "manual"
    transaction_id = Column(String(255), nullable=True, unique=True)

    # Status
    is_paid = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)

    # Dates
    start_date = Column(DateTime)
    end_date = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="payments")
    periods = relationship("ActivePeriod", back_populates="payment")

    def __repr__(self):
        return f"<Payment user={self.user_id} plan={self.plan_name}>"


class ActivePeriod(Base):
    """Active subscription period"""
    __tablename__ = "active_periods"

    id = Column(Integer, primary_key=True, index=True)
    payment_id = Column(Integer, ForeignKey("payments.id"), index=True)

    # Period information
    period_start = Column(DateTime)
    period_end = Column(DateTime)
    is_active = Column(Boolean, default=True)

    # Usage tracking
    searches_performed = Column(Integer, default=0)
    jobs_viewed = Column(Integer, default=0)
    jobs_applied = Column(Integer, default=0)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    payment = relationship("Payment", back_populates="periods")

    def __repr__(self):
        return f"<ActivePeriod {self.period_start} - {self.period_end}>"
