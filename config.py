"""
Job Radar MVP - Configuration Management
Environment-based settings using Pydantic
"""

from pydantic_settings import BaseSettings
from functools import lru_cache
import logging

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables

    To set these on Replit:
    1. Click "Secrets" (lock icon) in left sidebar
    2. Add key-value pairs
    3. They become environment variables accessible here
    """

    # ========== DATABASE ==========
    database_url: str = "postgresql://postgres:postgres@localhost:5432/job_radar"
    # On Replit: Generated when you add PostgreSQL from Resources tab
    # Copy the DATABASE_URL from the connection string

    # ========== API ==========
    api_port: int = 8000
    api_host: str = "0.0.0.0"
    debug: bool = False  # Set to True for development

    # ========== TELEGRAM BOT ==========
    telegram_bot_token: str = ""
    # Get from @BotFather on Telegram
    # Format: "123456789:ABCDefGhIjKlMnOpQrStUvWxYz..."

    # ========== LLM INTEGRATION ==========
    llm_provider: str = "anthropic"  # "anthropic" or "openai"

    # Anthropic/Claude configuration
    anthropic_api_key: str = ""
    # Get from https://console.anthropic.com
    # Format: "sk-ant-..."

    # OpenAI configuration
    openai_api_key: str = ""
    # Get from https://platform.openai.com/api-keys
    # Format: "sk-..."

    # ========== FEATURE FLAGS ==========
    enable_ranking_algorithm: bool = True
    enable_llm_language_detection: bool = True
    enable_llm_criteria_extraction: bool = True
    enable_telegram_webhook: bool = True
    enable_feedback_collection: bool = True

    # ========== JOB SEARCH SETTINGS ==========
    default_results_per_search: int = 3  # Jobs shown per search
    min_match_score: int = 30  # Minimum score to show (0-100)
    max_salary_displayed: int = 50000  # Max salary to show

    # ========== LOCATION SETTINGS ==========
    default_location: str = "trojmiasto"
    supported_locations: list = [
        "trojmiasto",  # Gdańsk, Gdynia, Sopot
        "warsaw",
        "krakow",
        "wroclaw",
        "remote"
    ]

    # ========== LANGUAGE SETTINGS ==========
    supported_languages: list = ["ru", "en", "pl", "uk"]
    default_language: str = "ru"

    class Config:
        env_file = ".env"  # Load from .env file if it exists
        case_sensitive = False
        extra = "ignore"  # Ignore unknown environment variables

    def validate_telegram(self):
        """Validate Telegram bot token"""
        if not self.telegram_bot_token:
            logger.warning("⚠ TELEGRAM_BOT_TOKEN not set")
            return False

        # Token format: "123456789:ABCDefGhIjKlMnOpQrStUvWxYz..."
        if ":" not in self.telegram_bot_token:
            logger.error("✗ Invalid TELEGRAM_BOT_TOKEN format")
            return False

        logger.info("✓ Telegram bot token configured")
        return True

    def validate_database(self):
        """Validate database configuration"""
        if not self.database_url:
            logger.error("✗ DATABASE_URL not set")
            return False

        if "postgresql" not in self.database_url:
            logger.warning("⚠ Not using PostgreSQL (using SQLite or other)")
        else:
            logger.info("✓ PostgreSQL database configured")

        return True

    def validate_llm(self):
        """Validate LLM configuration"""
        if self.llm_provider == "anthropic":
            if not self.anthropic_api_key:
                logger.warning("⚠ ANTHROPIC_API_KEY not set (Claude features disabled)")
                return False
            logger.info("✓ Anthropic/Claude configured")
            return True

        elif self.llm_provider == "openai":
            if not self.openai_api_key:
                logger.warning("⚠ OPENAI_API_KEY not set (GPT features disabled)")
                return False
            logger.info("✓ OpenAI/GPT configured")
            return True

        logger.warning(f"⚠ Unknown LLM_PROVIDER: {self.llm_provider}")
        return False

    def validate_all(self):
        """Validate all critical settings"""
        logger.info("Validating configuration...")

        db_ok = self.validate_database()
        tg_ok = self.validate_telegram()
        llm_ok = self.validate_llm()

        if db_ok and tg_ok:
            logger.info("✓ Configuration validation complete")
            return True
        else:
            logger.error("✗ Configuration has errors - see above")
            return False


# Global settings instance (cached)
@lru_cache()
def get_settings() -> Settings:
    """
    Get settings instance

    Cached so it's only loaded once

    Usage in routes:
        from config import get_settings

        settings = get_settings()
        api_port = settings.api_port
    """
    settings = Settings()

    # Validate on first load
    try:
        settings.validate_all()
    except Exception as e:
        logger.warning(f"Configuration validation warning: {e}")

    return settings


# ========== ENVIRONMENT VARIABLE SETUP GUIDE ==========
"""
On Replit, set these in Secrets (lock icon on left):

REQUIRED:
  DATABASE_URL=postgresql://user:password@host:port/dbname
    → Copy from Replit Resources → PostgreSQL → "Show credentials"

  TELEGRAM_BOT_TOKEN=123456789:ABCDefGhIjKlMnOpQrStUvWxYz...
    → Get from @BotFather on Telegram

OPTIONAL:
  ANTHROPIC_API_KEY=sk-ant-...
    → Get from https://console.anthropic.com (for Claude)

  OPENAI_API_KEY=sk-...
    → Get from https://platform.openai.com/api-keys (for GPT)

  DEBUG=true
    → Set to true for development (more logging)

  API_PORT=8000
    → Port to run API on (default 8000)

Example .env file for local development:
  DATABASE_URL=postgresql://postgres:postgres@localhost:5432/job_radar
  TELEGRAM_BOT_TOKEN=your_bot_token_here
  ANTHROPIC_API_KEY=sk-ant-your_key
  DEBUG=true
  API_PORT=8000
"""


# ========== SETTINGS FOR DIFFERENT ENVIRONMENTS ==========

def get_dev_settings() -> Settings:
    """Settings for development"""
    settings = get_settings()
    settings.debug = True
    return settings


def get_prod_settings() -> Settings:
    """Settings for production"""
    settings = get_settings()
    settings.debug = False
    # Add any production-specific overrides here
    return settings
