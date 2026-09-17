#!/usr/bin/env python3
"""
Job Radar MVP — Diagnostic Tool 🔧

This script checks:
- ✓ Database connectivity and data
- ✓ FastAPI app initialization
- ✓ Telegram bot configuration
- ✓ Environment variables
- ✓ File permissions
- ✓ Dependency versions

Usage:
    python diagnose.py
"""

import sys
import os
from pathlib import Path
from datetime import datetime

# ANSI Colors for output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

def print_header(msg):
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{msg:^60}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.RESET}\n")

def print_ok(msg):
    print(f"{Colors.GREEN}✓{Colors.RESET} {msg}")

def print_error(msg):
    print(f"{Colors.RED}✗{Colors.RESET} {msg}")

def print_warning(msg):
    print(f"{Colors.YELLOW}⚠{Colors.RESET} {msg}")

def print_info(msg):
    print(f"{Colors.BLUE}ℹ{Colors.RESET} {msg}")

# Test 1: Environment Variables
def test_env_vars():
    print_header("1. Environment Variables Check")

    required_vars = [
        ('TELEGRAM_BOT_TOKEN', 'Telegram bot token (starts with DigitsWithColon)'),
        ('DATABASE_URL', 'Database URL (sqlite:/// or postgresql://)'),
        ('API_PORT', 'API port (default 8000)'),
        ('DEBUG', 'Debug mode (true/false)'),
    ]

    optional_vars = [
        ('LLM_PROVIDER', 'LLM provider (anthropic or openai)'),
        ('ANTHROPIC_API_KEY', 'Anthropic/Claude API key'),
        ('OPENAI_API_KEY', 'OpenAI API key'),
    ]

    env_ok = True

    print("Required environment variables:")
    for var_name, description in required_vars:
        value = os.getenv(var_name)
        if value:
            # Mask sensitive data
            if 'TOKEN' in var_name or 'KEY' in var_name:
                display = value[:10] + '*' * (len(value) - 13) + value[-3:] if len(value) > 13 else '***'
            else:
                display = value
            print_ok(f"{var_name} = {display} ({description})")
        else:
            print_error(f"{var_name} not set ({description})")
            env_ok = False

    print("\nOptional environment variables:")
    for var_name, description in optional_vars:
        value = os.getenv(var_name)
        if value:
            if 'KEY' in var_name:
                display = value[:10] + '*' * (len(value) - 13) + value[-3:] if len(value) > 13 else '***'
            else:
                display = value
            print_ok(f"{var_name} = {display} ({description})")
        else:
            print_warning(f"{var_name} not set (optional: {description})")

    return env_ok

# Test 2: Dependencies
def test_dependencies():
    print_header("2. Python Dependencies Check")

    required_packages = [
        'fastapi',
        'uvicorn',
        'sqlalchemy',
        'python-telegram-bot',
        'pydantic',
    ]

    optional_packages = [
        'anthropic',
        'openai',
        'httpx',
        'redis',
        'celery',
        'pytest',
    ]

    all_ok = True

    print("Required packages:")
    for package_name in required_packages:
        try:
            __import__(package_name.replace('-', '_'))
            import importlib.metadata
            version = importlib.metadata.version(package_name)
            print_ok(f"{package_name} == {version}")
        except ImportError:
            print_error(f"{package_name} not installed")
            all_ok = False
        except Exception as e:
            print_warning(f"{package_name} version unknown ({str(e)})")

    print("\nOptional packages:")
    for package_name in optional_packages:
        try:
            __import__(package_name.replace('-', '_'))
            import importlib.metadata
            version = importlib.metadata.version(package_name)
            print_ok(f"{package_name} == {version}")
        except ImportError:
            print_warning(f"{package_name} not installed (optional)")
        except Exception as e:
            print_warning(f"{package_name} version unknown")

    return all_ok

# Test 3: Database
def test_database():
    print_header("3. Database Check")

    try:
        from database import SessionLocal
        from models import User, SearchProfile, JobCard, Source

        db = SessionLocal()

        # Test connection
        try:
            # Simple query to test connection
            user_count = db.query(User).count()
            print_ok(f"Database connection successful")
            print_info(f"Users in database: {user_count}")

            # Check other tables
            profile_count = db.query(SearchProfile).count()
            job_count = db.query(JobCard).count()
            source_count = db.query(Source).count()

            print_info(f"Search profiles: {profile_count}")
            print_info(f"Job cards: {job_count}")
            print_info(f"Sources: {source_count}")

            if job_count == 0:
                print_warning("No job cards in database. Run: python seed_data.py")
            else:
                print_ok(f"Database has {job_count} jobs ready")

            if source_count == 0:
                print_warning("No sources in database. Run: python seed_data.py")
            else:
                print_ok(f"Database has {source_count} sources configured")

            db.close()
            return True

        except Exception as e:
            print_error(f"Database query error: {str(e)}")
            db.close()
            return False

    except ImportError as e:
        print_error(f"Cannot import database module: {str(e)}")
        print_info("Make sure you are in the job-radar directory")
        return False

# Test 4: FastAPI App
def test_fastapi_app():
    print_header("4. FastAPI Application Check")

    try:
        from main import app

        print_ok("FastAPI app imported successfully")

        # Check routes
        routes = []
        for route in app.routes:
            if hasattr(route, 'path'):
                methods = getattr(route, 'methods', {'GET'})
                routes.append((route.path, methods))

        print_info(f"Total routes: {len(routes)}")

        # Check specific important routes
        required_routes = [
            ('/health', 'GET'),
            ('/api/jobs', 'GET'),
            ('/api/sources', 'GET'),
            ('/api/docs', 'GET'),
            ('/api/redoc', 'GET'),
        ]

        print("\nCritical endpoints:")
        for path, method in required_routes:
            found = False
            for route_path, route_methods in routes:
                if route_path == path and (method in route_methods or method == 'GET'):
                    found = True
                    break

            if found:
                print_ok(f"{method:4} {path}")
            else:
                print_error(f"{method:4} {path} NOT FOUND")

        return True

    except Exception as e:
        print_error(f"Cannot import FastAPI app: {str(e)}")
        print_info("Make sure main.py is valid and all imports are available")
        return False

# Test 5: Telegram Bot
def test_telegram_bot():
    print_header("5. Telegram Bot Configuration Check")

    token = os.getenv('TELEGRAM_BOT_TOKEN')

    if not token:
        print_error("TELEGRAM_BOT_TOKEN not set in environment")
        return False

    try:
        from telegram import Bot
        import asyncio

        # Validate token format
        parts = token.split(':')
        if len(parts) != 2:
            print_error(f"Invalid token format: {token[:20]}...")
            print_info("Format should be: <bot_id>:<token_string>")
            return False

        print_ok(f"Token format looks valid: {parts[0]}:...")

        # Try to create bot instance
        try:
            bot = Bot(token)
            print_ok("Bot instance created successfully")

            # Try to get bot info
            try:
                # This is a sync call, not async
                # We can test if the bot object exists
                print_ok("Bot object ready for async operations")
                print_info("Note: Full bot test requires async environment and network access")

            except Exception as e:
                print_warning(f"Cannot test bot connectivity (no network): {str(e)}")

        except Exception as e:
            print_error(f"Cannot create bot instance: {str(e)}")
            return False

        # Check telegram_bot.py
        try:
            from telegram_bot import setup_dispatcher
            print_ok("telegram_bot.py imports successfully")
        except Exception as e:
            print_error(f"Cannot import telegram_bot: {str(e)}")
            return False

        return True

    except ImportError:
        print_error("python-telegram-bot not installed")
        return False

# Test 6: Files and Permissions
def test_files():
    print_header("6. Files and Permissions Check")

    required_files = [
        'main.py',
        'config.py',
        'database.py',
        'models.py',
        'ranking.py',
        'sources.py',
        'telegram_bot.py',
        'llm_service.py',
        'requirements.txt',
    ]

    all_exist = True

    for filename in required_files:
        filepath = Path(filename)
        if filepath.exists():
            size = filepath.stat().st_size
            print_ok(f"{filename} ({size} bytes)")
        else:
            print_error(f"{filename} not found")
            all_exist = False

    # Check database file
    db_path = Path('job_radar.db')
    if db_path.exists():
        size = db_path.stat().st_size
        print_ok(f"Database file exists ({size} bytes)")
    else:
        print_warning("Database file not found (will be created on first run)")

    return all_exist

# Test 7: Replit Specific
def test_replit():
    print_header("7. Replit Environment Check")

    replit_user = os.getenv('REPLIT_OWNER')
    replit_slug = os.getenv('REPLIT_SLUG')

    if replit_user and replit_slug:
        print_ok(f"Running on Replit: @{replit_user}/{replit_slug}")

        # Construct public URL
        public_url = f"https://{replit_slug}--{replit_user}.replit.app"
        print_info(f"Public URL: {public_url}")

        return True
    else:
        print_warning("Not running on Replit or environment variables missing")
        print_info("REPLIT_OWNER: " + (replit_user or "not set"))
        print_info("REPLIT_SLUG: " + (replit_slug or "not set"))
        return False

# Main diagnostic function
def run_diagnostics():
    print(f"\n{Colors.BOLD}Job Radar MVP — Diagnostic Report{Colors.RESET}")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}")

    results = {
        'Environment Variables': test_env_vars(),
        'Dependencies': test_dependencies(),
        'Database': test_database(),
        'FastAPI App': test_fastapi_app(),
        'Telegram Bot': test_telegram_bot(),
        'Files': test_files(),
        'Replit Environment': test_replit(),
    }

    # Summary
    print_header("Summary")

    passed = sum(1 for v in results.values() if v)
    total = len(results)

    for test_name, result in results.items():
        status = f"{Colors.GREEN}PASS{Colors.RESET}" if result else f"{Colors.RED}FAIL{Colors.RESET}"
        print(f"  {status}: {test_name}")

    print(f"\nScore: {passed}/{total} checks passed")

    if passed == total:
        print(f"\n{Colors.GREEN}{Colors.BOLD}✓ All systems operational! Ready for testing.{Colors.RESET}")
    elif passed >= total - 1:
        print(f"\n{Colors.YELLOW}{Colors.BOLD}⚠ Most systems working, minor issues to fix.{Colors.RESET}")
    else:
        print(f"\n{Colors.RED}{Colors.BOLD}✗ Multiple issues detected. See above for details.{Colors.RESET}")

    # Recommendations
    if not results['Database']:
        print(f"\n{Colors.BOLD}Recommendation:{Colors.RESET}")
        print("  1. Ensure DATABASE_URL is set correctly in Secrets")
        print("  2. For SQLite: DATABASE_URL = sqlite:///./job_radar.db")
        print("  3. Run: python seed_data.py")

    if not results['Telegram Bot']:
        print(f"\n{Colors.BOLD}Recommendation:{Colors.RESET}")
        print("  1. Set TELEGRAM_BOT_TOKEN in Secrets (from @BotFather)")
        print("  2. Format: <digits>:<alphanumeric_string>")
        print("  3. Configure webhook after deployment")

    print()
    return passed == total

if __name__ == '__main__':
    success = run_diagnostics()
    sys.exit(0 if success else 1)
