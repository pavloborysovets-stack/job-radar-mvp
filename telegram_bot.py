"""
Job Radar MVP - Telegram Bot with FSM
14-state Finite State Machine for user interactions
Supports: Russian, English, Polish, Ukrainian
"""

import logging
from enum import Enum
from typing import Dict
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ConversationHandler,
    filters,
    ContextTypes,
    BaseHandler,
)
from datetime import datetime

logger = logging.getLogger(__name__)

# ========== FSM STATES ==========
class BotState(str, Enum):
    """Telegram bot states in FSM"""
    START = "START"
    LANGUAGE_SELECT = "LANGUAGE_SELECT"
    GEOGRAPHY_CONFIRM = "GEOGRAPHY_CONFIRM"
    JOB_TYPE_INPUT = "JOB_TYPE_INPUT"
    SALARY_INPUT = "SALARY_INPUT"
    CONTRACT_SELECT = "CONTRACT_SELECT"
    CRITERIA_CONFIRM = "CRITERIA_CONFIRM"
    RESULTS_DISPLAY = "RESULTS_DISPLAY"
    FEEDBACK = "FEEDBACK"
    PLAN_SELECT = "PLAN_SELECT"
    PAYMENT = "PAYMENT"
    SAVED_JOBS = "SAVED_JOBS"
    END = "END"


# ========== TRANSLATIONS ==========
TRANSLATIONS = {
    "ru": {
        "welcome": "Привет! 👋 Добро пожаловать в Job Radar\n\nЭто быстрый способ найти работу в Trójmiasto",
        "select_language": "Выберите язык:",
        "select_geography": "Вы ищите работу в Trójmiasto (Gdańsk, Gdynia, Sopot)?",
        "enter_job_type": "Какую должность вы ищите? (например: Python Developer)",
        "enter_min_salary": "Какая минимальная зарплата? (в PLN)",
        "select_contract": "Тип контракта:",
        "confirm_criteria": "Ваши критерии поиска:\n{criteria}\n\nВсе верно?",
        "searching": "🔍 Ищу вакансии...",
        "no_results": "Извините, работы не найдены по вашим критериям",
        "job_found": "💼 Вакансия {num}/{total}:\n\n{job}",
        "rate_job": "Вам нравится эта вакансия?",
        "thanks_feedback": "Спасибо за обратную связь!",
        "search_again": "Хотите провести еще один поиск?",
        "goodbye": "До свидания! 👋",
    },
    "en": {
        "welcome": "Hi! 👋 Welcome to Job Radar\n\nQuick way to find jobs in Trójmiasto",
        "select_language": "Select language:",
        "select_geography": "Looking for jobs in Trójmiasto (Gdańsk, Gdynia, Sopot)?",
        "enter_job_type": "What job are you looking for? (e.g.: Python Developer)",
        "enter_min_salary": "What's the minimum salary? (in PLN)",
        "select_contract": "Contract type:",
        "confirm_criteria": "Your search criteria:\n{criteria}\n\nLooks good?",
        "searching": "🔍 Searching for jobs...",
        "no_results": "Sorry, no jobs found matching your criteria",
        "job_found": "💼 Job {num}/{total}:\n\n{job}",
        "rate_job": "Do you like this job?",
        "thanks_feedback": "Thanks for the feedback!",
        "search_again": "Want to search again?",
        "goodbye": "Goodbye! 👋",
    },
    "pl": {
        "welcome": "Cześć! 👋 Witamy w Job Radar\n\nSzybki sposób na znalezienie pracy w Trójmieście",
        "select_language": "Wybierz język:",
        "select_geography": "Szukasz pracy w Trójmieście (Gdańsk, Gdynia, Sopot)?",
        "enter_job_type": "Jaką pozycję szukasz? (np: Python Developer)",
        "enter_min_salary": "Jaka minimalna pensja? (w PLN)",
        "select_contract": "Typ umowy:",
        "confirm_criteria": "Twoje kryteria wyszukiwania:\n{criteria}\n\nWszystko OK?",
        "searching": "🔍 Szukam prac...",
        "no_results": "Przepraszam, nie znaleziono prac spełniających Twoje kryteria",
        "job_found": "💼 Praca {num}/{total}:\n\n{job}",
        "rate_job": "Czy podoba Ci się ta praca?",
        "thanks_feedback": "Dziękuję za opinię!",
        "search_again": "Chcesz wyszukać ponownie?",
        "goodbye": "Do widzenia! 👋",
    },
    "uk": {
        "welcome": "Привіт! 👋 Ласкаво просимо до Job Radar\n\nШвидкий спосіб знайти роботу у Трьохмісті",
        "select_language": "Виберіть мову:",
        "select_geography": "Ви шукаєте роботу в Трьохмісті (Гданськ, Гдиня, Сопот)?",
        "enter_job_type": "Яку посаду ви шукаєте? (наприклад: Python Developer)",
        "enter_min_salary": "Яка мінімальна зарплата? (в PLN)",
        "select_contract": "Тип контракту:",
        "confirm_criteria": "Ваші критерії пошуку:\n{criteria}\n\nВсе вірно?",
        "searching": "🔍 Шукаю вакансії...",
        "no_results": "Вибачте, роботи за вашими критеріями не знайдені",
        "job_found": "💼 Вакансія {num}/{total}:\n\n{job}",
        "rate_job": "Вам подобається ця вакансія?",
        "thanks_feedback": "Спасибі за відгук!",
        "search_again": "Хочете шукати ще?",
        "goodbye": "До побачення! 👋",
    }
}


# ========== TELEGRAM BOT HANDLER ==========
class TelegramBotHandler:
    """Main Telegram bot handler"""

    def __init__(self, token: str):
        """
        Initialize bot

        Args:
            token: Telegram bot token
        """
        self.token = token
        self.application = None

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
        """Handle /start command"""
        user = update.effective_user
        logger.info(f"User {user.id} started bot")

        # Store user language (will be set when they select)
        context.user_data["user_id"] = user.id
        context.user_data["first_name"] = user.first_name

        # Get text
        text = self._get_text("welcome", "en")

        # Language selection keyboard
        keyboard = [
            [
                InlineKeyboardButton("🇷🇺 Русский", callback_data="lang_ru"),
                InlineKeyboardButton("🇬🇧 English", callback_data="lang_en"),
            ],
            [
                InlineKeyboardButton("🇵🇱 Polski", callback_data="lang_pl"),
                InlineKeyboardButton("🇺🇦 Українська", callback_data="lang_uk"),
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(
            text,
            reply_markup=reply_markup
        )

        return BotState.LANGUAGE_SELECT

    async def select_language(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
        """Handle language selection"""
        query = update.callback_query
        await query.answer()

        # Extract language
        language = query.data.split("_")[1]
        context.user_data["language"] = language

        logger.info(f"User selected language: {language}")

        # Geography question
        text = self._get_text("select_geography", language)
        keyboard = [
            [
                InlineKeyboardButton("✅ Да / Yes / Tak / Так", callback_data="geo_yes"),
                InlineKeyboardButton("❌ Нет / No / Nie / Ні", callback_data="geo_no"),
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(
            text,
            reply_markup=reply_markup
        )

        return BotState.GEOGRAPHY_CONFIRM

    async def confirm_geography(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
        """Handle geography confirmation"""
        query = update.callback_query
        await query.answer()

        language = context.user_data.get("language", "en")
        geography = "trojmiasto" if query.data == "geo_yes" else "other"
        context.user_data["geography"] = geography

        logger.info(f"User geography: {geography}")

        # Job type input
        text = self._get_text("enter_job_type", language)
        await query.edit_message_text(text)

        return BotState.JOB_TYPE_INPUT

    async def input_job_type(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
        """Handle job type input"""
        job_type = update.message.text
        language = context.user_data.get("language", "en")
        context.user_data["job_type"] = job_type

        logger.info(f"Job type: {job_type}")

        # Salary input
        text = self._get_text("enter_min_salary", language)
        await update.message.reply_text(text)

        return BotState.SALARY_INPUT

    async def input_salary(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
        """Handle salary input"""
        try:
            min_salary = int(update.message.text)
            context.user_data["min_salary"] = min_salary
            logger.info(f"Min salary: {min_salary}")
        except ValueError:
            language = context.user_data.get("language", "en")
            await update.message.reply_text("❌ Please enter a valid number")
            return BotState.SALARY_INPUT

        language = context.user_data.get("language", "en")

        # Contract type selection
        text = self._get_text("select_contract", language)
        keyboard = [
            [
                InlineKeyboardButton("💼 Full-time", callback_data="contract_fulltime"),
                InlineKeyboardButton("🕒 Part-time", callback_data="contract_parttime"),
            ],
            [
                InlineKeyboardButton("📋 Contract", callback_data="contract_contract"),
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(
            text,
            reply_markup=reply_markup
        )

        return BotState.CONTRACT_SELECT

    async def select_contract(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
        """Handle contract type selection"""
        query = update.callback_query
        await query.answer()

        contract = query.data.split("_")[1]
        context.user_data["contract_type"] = contract
        language = context.user_data.get("language", "en")

        logger.info(f"Contract type: {contract}")

        # Confirm criteria
        criteria_text = self._format_criteria(context.user_data)
        text = self._get_text("confirm_criteria", language).format(criteria=criteria_text)

        keyboard = [
            [
              InlineKeyboardButton("✅ Yes / Да / Tak / Так", callback_data="confirm_yes"),
                InlineKeyboardButton("❌ No / Нет / Nie / Ні", callback_data="confirm_no"),
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(
            text,
            reply_markup=reply_markup
        )

        return BotState.CRITERIA_CONFIRM

    async def confirm_criteria(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
        """Handle criteria confirmation"""
        query = update.callback_query
        await query.answer()

        language = context.user_data.get("language", "en")

        if query.data == "confirm_no":
            # Start over
            await query.edit_message_text(self._get_text("welcome", language))
            return BotState.START

        # Search for jobs
        text = self._get_text("searching", language)
        await query.edit_message_text(text)

        # In production: fetch real jobs and rank them
        # For MVP: use mock data
        jobs = self._get_mock_jobs()
        context.user_data["jobs"] = jobs
        context.user_data["current_job_index"] = 0

        if not jobs:
            text = self._get_text("no_results", language)
            await query.edit_message_text(text)
            return BotState.END

        # Show first job
        return await self._show_job(update, context)

    async def _show_job(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
        """Show current job"""
        language = context.user_data.get("language", "en")
        jobs = context.user_data.get("jobs", [])
        index = context.user_data.get("current_job_index", 0)

        if index >= len(jobs):
            # No more jobs
            text = self._get_text("search_again", language)
            keyboard = [
                [
                    InlineKeyboardButton("🔍 Search", callback_data="search_again"),
                    InlineKeyboardButton("❌ Exit", callback_data="exit"),
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            if update.callback_query:
                await update.callback_query.edit_message_text(text, reply_markup=reply_markup)
            else:
                await update.message.reply_text(text, reply_markup=reply_markup)

            return BotState.END

        job = jobs[index]

        # Format job text
        job_text = f"""
<b>{job['title']}</b>
{job['company']} • {job['location']}

💰 {job['salary_min']:,} - {job['salary_max']:,} PLN
📋 {job['contract_type']}
📍 {job['work_location']}

<b>Requirements:</b>
{job['required_skills']}

<a href="{job['url']}">View Full Job →</a>
"""

        text = self._get_text("job_found", language).format(
            num=index + 1,
            total=len(jobs),
            job=job_text
        )

        keyboard = [
            [
                InlineKeyboardButton("👍 Like", callback_data="rate_like"),
                InlineKeyboardButton("👎 Dislike", callback_data="rate_dislike"),
            ],
            [
                InlineKeyboardButton("➡️ Next", callback_data="next_job"),
                InlineKeyboardButton("⬅��� Back", callback_data="prev_job"),
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        if update.callback_query:
            await update.callback_query.edit_message_text(
                text,
                reply_markup=reply_markup,
                parse_mode="HTML"
            )
        else:
            await update.message.reply_text(
                text,
                reply_markup=reply_markup,
                parse_mode="HTML"
            )

        return BotState.RESULTS_DISPLAY

    async def handle_feedback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
        """Handle job rating feedback"""
        query = update.callback_query
        await query.answer()

        language = context.user_data.get("language", "en")
        jobs = context.user_data.get("jobs", [])
        index = context.user_data.get("current_job_index", 0)

        if index < len(jobs):
            job = jobs[index]
            # In production: save feedback to database
            logger.info(f"Feedback: {query.data} for job {job['title']}")

        if "next" in query.data or "like" in query.data or "dislike" in query.data:
            context.user_data["current_job_index"] = index + 1
        elif "prev" in query.data:
            context.user_data["current_job_index"] = max(0, index - 1)

        # Show next job or end
        return await self._show_job(update, context)

    async def handle_end(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle conversation end"""
        query = update.callback_query
        await query.answer()

        language = context.user_data.get("language", "en")

        if query.data == "search_again":
            return await self.start(update, context)
        else:
            text = self._get_text("goodbye", language)
            await query.edit_message_text(text)
            return -1  # End conversation

    # ========== HELPER METHODS ==========

    def _get_text(self, key: str, language: str) -> str:
        """Get translated text"""
        return TRANSLATIONS.get(language, TRANSLATIONS["en"]).get(key, "")

    def _format_criteria(self, user_data: Dict) -> str:
        """Format user criteria for display"""
        return f"""
• Job: {user_data.get('job_type', 'Any')}
• Min Salary: {user_data.get('min_salary', 'Any')} PLN
• Type: {user_data.get('contract_type', 'Any')}
• Location: {user_data.get('geography', 'trojmiasto')}
"""

    def _get_mock_jobs(self) -> list:
        """Get mock jobs for MVP"""
        return [
            {
                "title": "Python Backend Developer",
                "company": "TechCorp",
                "location": "Gdańsk",
                "salary_min": 8000,
                "salary_max": 12000,
                "contract_type": "Full-time",
                "work_location": "On-site",
                "required_skills": "Python, FastAPI, PostgreSQL",
                "url": "https://example.com/job/1",
            },
            {
                "title": "Frontend Developer",
                "company": "WebStudio",
                "location": "Sopot",
                "salary_min": 6500,
                "salary_max": 9500,
                "contract_type": "Full-time",
                "work_location": "Hybrid",
                "required_skills": "React, TypeScript, CSS",
                "url": "https://example.com/job/2",
            },
            {
                "title": "Data Scientist",
                "company": "DataWorks",
                "location": "Gdynia",
                "salary_min": 9000,
                "salary_max": 15000,
                "contract_type": "Full-time",
                "work_location": "Hybrid",
                "required_skills": "Python, SQL, ML, TensorFlow",
                "url": "https://example.com/job/3",
            },
        ]

    async def setup(self):
        """Set up conversation handler"""
        # Define conversation handler
        conv_handler = ConversationHandler(
            entry_points=[CommandHandler("start", self.start)],
            states={
                BotState.LANGUAGE_SELECT: [
                    CallbackQueryHandler(self.select_language)
                ],
                BotState.GEOGRAPHY_CONFIRM: [
                    CallbackQueryHandler(self.confirm_geography)
                ],
                BotState.JOB_TYPE_INPUT: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.input_job_type)
                ],
                BotState.SALARY_INPUT: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.input_salary)
                ],
                BotState.CONTRACT_SELECT: [
                    CallbackQueryHandler(self.select_contract)
                ],
                BotState.CRITERIA_CONFIRM: [
                    CallbackQueryHandler(self.confirm_criteria)
                ],
                BotState.RESULTS_DISPLAY: [
                    CallbackQueryHandler(self.handle_feedback)
                ],
                BotState.END: [
                    CallbackQueryHandler(self.handle_end)
                ],
            },
            fallbacks=[CommandHandler("start", self.start)],
        )

        # Add handler to application
        self.application.add_handler(conv_handler)

    async def start_polling(self):
        """Start bot in polling mode"""
        self.application = Application.builder().token(self.token).build()
        await self.setup()
        await self.application.run_polling()

    async def start_webhook(self, url: str):
        """Start bot in webhook mode"""
        self.application = Application.builder().token(self.token).build()
        await self.setup()
        await self.application.run_webhook(url)

    async def start_polling_background(self):
        """
        Start bot in polling mode WITHOUT blocking the current event loop.
        Safe to call from inside a FastAPI lifespan startup handler,
        since it only awaits non-blocking initialize/start calls instead
        of the high-level run_polling() (which blocks until a stop signal).
        """
        self.application = Application.builder().token(self.token).build()
        await self.setup()

        # Make sure no webhook is registered - polling and webhooks
        # cannot be used for the same bot token at the same time.
        await self.application.bot.delete_webhook(drop_pending_updates=True)

        await self.application.initialize()
        await self.application.start()
        await self.application.updater.start_polling()
        logger.info("✅ Telegram bot polling started")

    async def stop(self):
        """Gracefully stop the bot (call on FastAPI shutdown)"""
        if not self.application:
            return
        try:
            if self.application.updater and self.application.updater.running:
                await self.application.updater.stop()
            await self.application.stop()
            await self.application.shutdown()
            logger.info("🛑 Telegram bot stopped")
        except Exception as e:
            logger.error(f"Error stopping Telegram bot: {e}")


# ========== STANDALONE USAGE ==========
"""
import asyncio
from config import get_settings

async def main():
    settings = get_settings()
    bot = TelegramBotHandler(settings.telegram_bot_token)
    await bot.start_polling()

asyncio.run(main())
"""
"""
Job Radar MVP - Telegram Bot with FSM
14-state Finite State Machine for user interactions
Supports: Russian, English, Polish, Ukrainian
"""

import logging
from enum import Enum
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ConversationHandler,
    filters,
    ContextTypes,
    BaseHandler,
)
from datetime import datetime

logger = logging.getLogger(__name__)

# ========== FSM STATES ==========
class BotState(str, Enum):
    """Telegram bot states in FSM"""
    START = "START"
    LANGUAGE_SELECT = "LANGUAGE_SELECT"
    GEOGRAPHY_CONFIRM = "GEOGRAPHY_CONFIRM"
    JOB_TYPE_INPUT = "JOB_TYPE_INPUT"
    SALARY_INPUT = "SALARY_INPUT"
    CONTRACT_SELECT = "CONTRACT_SELECT"
    CRITERIA_CONFIRM = "CRITERIA_CONFIRM"
    RESULTS_DISPLAY = "RESULTS_DISPLAY"
    FEEDBACK = "FEEDBACK"
    PLAN_SELECT = "PLAN_SELECT"
    PAYMENT = "PAYMENT"
    SAVED_JOBS = "SAVED_JOBS"
    END = "END"


# ========== TRANSLATIONS ==========
TRANSLATIONS = {
    "ru": {
        "welcome": "Привет! 👋 Добро пожаловать в Job Radar\n\nЭто быстрый способ найти работу в Trójmiasto",
        "select_language": "Выберите язык:",
        "select_geography": "Вы ищите работу в Trójmiasto (Gdańsk, Gdynia, Sopot)?",
        "enter_job_type": "Какую должность вы ищите? (например: Python Developer)",
        "enter_min_salary": "Какая минимальная зарплата? (в PLN)",
        "select_contract": "Тип контракта:",
        "confirm_criteria": "Ваши критерии поиска:\n{criteria}\n\nВсе верно?",
        "searching": "🔍 Ищу вакансии...",
        "no_results": "Извините, работы не найдены по вашим критериям",
        "job_found": "💼 Вакансия {num}/{total}:\n\n{job}",
        "rate_job": "Вам нравится эта вакансия?",
        "thanks_feedback": "Спасибо за обратную связь!",
        "search_again": "Хотите провести еще один поиск?",
        "goodbye": "До свидания! 👋",
    },
    "en": {
        "welcome": "Hi! 👋 Welcome to Job Radar\n\nQuick way to find jobs in Trójmiasto",
        "select_language": "Select language:",
        "select_geography": "Looking for jobs in Trójmiasto (Gdańsk, Gdynia, Sopot)?",
        "enter_job_type": "What job are you looking for? (e.g.: Python Developer)",
        "enter_min_salary": "What's the minimum salary? (in PLN)",
        "select_contract": "Contract type:",
        "confirm_criteria": "Your search criteria:\n{criteria}\n\nLooks good?",
        "searching": "🔍 Searching for jobs...",
        "no_results": "Sorry, no jobs found matching your criteria",
        "job_found": "💼 Job {num}/{total}:\n\n{job}",
        "rate_job": "Do you like this job?",
        "thanks_feedback": "Thanks for the feedback!",
        "search_again": "Want to search again?",
        "goodbye": "Goodbye! 👋",
    },
    "pl": {
        "welcome": "Cześć! 👋 Witamy w Job Radar\n\nSzybki sposób na znalezienie pracy w Trójmieście",
        "select_language": "Wybierz język:",
        "select_geography": "Szukasz pracy w Trójmieście (Gdańsk, Gdynia, Sopot)?",
        "enter_job_type": "Jaką pozycję szukasz? (np: Python Developer)",
        "enter_min_salary": "Jaka minimalna pensja? (w PLN)",
        "select_contract": "Typ umowy:",
        "confirm_criteria": "Twoje kryteria wyszukiwania:\n{criteria}\n\nWszystko OK?",
        "searching": "🔍 Szukam prac...",
        "no_results": "Przepraszam, nie znaleziono prac spełniających Twoje kryteria",
        "job_found": "💼 Praca {num}/{total}:\n\n{job}",
        "rate_job": "Czy podoba Ci się ta praca?",
        "thanks_feedback": "Dziękuję za opinię!",
        "search_again": "Chcesz wyszukać ponownie?",
        "goodbye": "Do widzenia! 👋",
    },
    "uk": {
        "welcome": "Привіт! 👋 Ласкаво просимо до Job Radar\n\nШвидкий спосіб знайти роботу у Трьохмісті",
        "select_language": "Виберіть мову:",
        "select_geography": "Ви шукаєте роботу в Трьохмісті (Гданськ, Гдиня, Сопот)?",
        "enter_job_type": "Яку посаду ви шукаєте? (наприклад: Python Developer)",
        "enter_min_salary": "Яка мінімальна зарплата? (в PLN)",
        "select_contract": "Тип контракту:",
        "confirm_criteria": "Ваші критерії пошуку:\n{criteria}\n\nВсе вірно?",
        "searching": "🔍 Шукаю вакансії...",
        "no_results": "Вибачте, роботи за вашими критеріями не знайдені",
        "job_found": "💼 Вакансія {num}/{total}:\n\n{job}",
        "rate_job": "Вам подобається ця вакансія?",
        "thanks_feedback": "Спасибі за відгук!",
        "search_again": "Хочете шукати ще?",
        "goodbye": "До побачення! 👋",
    }
}


# ========== TELEGRAM BOT HANDLER ==========
class TelegramBotHandler:
    """Main Telegram bot handler"""

    def __init__(self, token: str):
        """
        Initialize bot

        Args:
            token: Telegram bot token
        """
        self.token = token
        self.application = None

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
        """Handle /start command"""
        user = update.effective_user
        logger.info(f"User {user.id} started bot")

        # Store user language (will be set when they select)
        context.user_data["user_id"] = user.id
        context.user_data["first_name"] = user.first_name

        # Get text
        text = self._get_text("welcome", "en")

        # Language selection keyboard
        keyboard = [
            [
                InlineKeyboardButton("🇷🇺 Русский", callback_data="lang_ru"),
                InlineKeyboardButton("🇬🇧 English", callback_data="lang_en"),
            ],
            [
                InlineKeyboardButton("🇵🇱 Polski", callback_data="lang_pl"),
                InlineKeyboardButton("🇺🇦 Українська", callback_data="lang_uk"),
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(
            text,
            reply_markup=reply_markup
        )

        return BotState.LANGUAGE_SELECT

    async def select_language(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
        """Handle language selection"""
        query = update.callback_query
        await query.answer()

        # Extract language
        language = query.data.split("_")[1]
        context.user_data["language"] = language

        logger.info(f"User selected language: {language}")

        # Geography question
        text = self._get_text("select_geography", language)
        keyboard = [
            [
                InlineKeyboardButton("✅ Да / Yes / Tak / Так", callback_data="geo_yes"),
                InlineKeyboardButton("❌ Нет / No / Nie / Ні", callback_data="geo_no"),
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(
            text,
            reply_markup=reply_markup
        )

        return BotState.GEOGRAPHY_CONFIRM

    async def confirm_geography(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
        """Handle geography confirmation"""
        query = update.callback_query
        await query.answer()

        language = context.user_data.get("language", "en")
        geography = "trojmiasto" if query.data == "geo_yes" else "other"
        context.user_data["geography"] = geography

        logger.info(f"User geography: {geography}")

        # Job type input
        text = self._get_text("enter_job_type", language)
        await query.edit_message_text(text)

        return BotState.JOB_TYPE_INPUT

    async def input_job_type(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
        """Handle job type input"""
        job_type = update.message.text
        language = context.user_data.get("language", "en")
        context.user_data["job_type"] = job_type

        logger.info(f"Job type: {job_type}")

        # Salary input
        text = self._get_text("enter_min_salary", language)
        await update.message.reply_text(text)

        return BotState.SALARY_INPUT

    async def input_salary(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
        """Handle salary input"""
        try:
            min_salary = int(update.message.text)
            context.user_data["min_salary"] = min_salary
            logger.info(f"Min salary: {min_salary}")
        except ValueError:
            language = context.user_data.get("language", "en")
            await update.message.reply_text("❌ Please enter a valid number")
            return BotState.SALARY_INPUT

        language = context.user_data.get("language", "en")

        # Contract type selection
        text = self._get_text("select_contract", language)
        keyboard = [
            [
                InlineKeyboardButton("💼 Full-time", callback_data="contract_fulltime"),
                InlineKeyboardButton("🕒 Part-time", callback_data="contract_parttime"),
            ],
            [
                InlineKeyboardButton("📋 Contract", callback_data="contract_contract"),
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(
            text,
            reply_markup=reply_markup
        )

        return BotState.CONTRACT_SELECT

    async def select_contract(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
        """Handle contract type selection"""
        query = update.callback_query
        await query.answer()

        contract = query.data.split("_")[1]
        context.user_data["contract_type"] = contract
        language = context.user_data.get("language", "en")

        logger.info(f"Contract type: {contract}")

        # Confirm criteria
        criteria_text = self._format_criteria(context.user_data)
        text = self._get_text("confirm_criteria", language).format(criteria=criteria_text)

        keyboard = [
            [
                InlineKeyboardButton("✅ Yes / Да / Tak / Так", callback_data="confirm_yes"),
                InlineKeyboardButton("❌ No / Нет / Nie / Ні", callback_data="confirm_no"),
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(
            text,
            reply_markup=reply_markup
        )

        return BotState.CRITERIA_CONFIRM

    async def confirm_criteria(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
        """Handle criteria confirmation"""
        query = update.callback_query
        await query.answer()

        language = context.user_data.get("language", "en")

        if query.data == "confirm_no":
            # Start over
            await query.edit_message_text(self._get_text("welcome", language))
            return BotState.START

        # Search for jobs
        text = self._get_text("searching", language)
        await query.edit_message_text(text)

        # In production: fetch real jobs and rank them
        # For MVP: use mock data
        jobs = self._get_mock_jobs()
        context.user_data["jobs"] = jobs
        context.user_data["current_job_index"] = 0

        if not jobs:
            text = self._get_text("no_results", language)
            await query.edit_message_text(text)
            return BotState.END

        # Show first job
        return await self._show_job(update, context)

    async def _show_job(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
        """Show current job"""
        language = context.user_data.get("language", "en")
        jobs = context.user_data.get("jobs", [])
        index = context.user_data.get("current_job_index", 0)

        if index >= len(jobs):
            # No more jobs
            text = self._get_text("search_again", language)
            keyboard = [
                [
                    InlineKeyboardButton("🔍 Search", callback_data="search_again"),
                    InlineKeyboardButton("❌ Exit", callback_data="exit"),
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            if update.callback_query:
                await update.callback_query.edit_message_text(text, reply_markup=reply_markup)
            else:
                await update.message.reply_text(text, reply_markup=reply_markup)

            return BotState.END

        job = jobs[index]

        # Format job text
        job_text = f"""
<b>{job['title']}</b>
{job['company']} • {job['location']}

💰 {job['salary_min']:,} - {job['salary_max']:,} PLN
📋 {job['contract_type']}
📍 {job['work_location']}

<b>Requirements:</b>
{job['required_skills']}

<a href="{job['url']}">View Full Job →</a>
"""

        text = self._get_text("job_found", language).format(
            num=index + 1,
            total=len(jobs),
            job=job_text
        )

        keyboard = [
            [
                InlineKeyboardButton("👍 Like", callback_data="rate_like"),
                InlineKeyboardButton("👎 Dislike", callback_data="rate_dislike"),
            ],
            [
                InlineKeyboardButton("➡️ Next", callback_data="next_job"),
                InlineKeyboardButton("⬅️ Back", callback_data="prev_job"),
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        if update.callback_query:
            await update.callback_query.edit_message_text(
                text,
                reply_markup=reply_markup,
                parse_mode="HTML"
            )
        else:
            await update.message.reply_text(
                text,
                reply_markup=reply_markup,
                parse_mode="HTML"
            )

        return BotState.RESULTS_DISPLAY

    async def handle_feedback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
        """Handle job rating feedback"""
        query = update.callback_query
        await query.answer()

        language = context.user_data.get("language", "en")
        jobs = context.user_data.get("jobs", [])
        index = context.user_data.get("current_job_index", 0)

        if index < len(jobs):
            job = jobs[index]
            # In production: save feedback to database
            logger.info(f"Feedback: {query.data} for job {job['title']}")

        if "next" in query.data or "like" in query.data or "dislike" in query.data:
            context.user_data["current_job_index"] = index + 1
        elif "prev" in query.data:
            context.user_data["current_job_index"] = max(0, index - 1)

        # Show next job or end
        return await self._show_job(update, context)

    async def handle_end(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle conversation end"""
        query = update.callback_query
        await query.answer()

        language = context.user_data.get("language", "en")

        if query.data == "search_again":
            return await self.start(update, context)
        else:
            text = self._get_text("goodbye", language)
            await query.edit_message_text(text)
            return -1  # End conversation

    # ========== HELPER METHODS ==========

    def _get_text(self, key: str, language: str) -> str:
        """Get translated text"""
        return TRANSLATIONS.get(language, TRANSLATIONS["en"]).get(key, "")

    def _format_criteria(self, user_data: Dict) -> str:
        """Format user criteria for display"""
        return f"""
• Job: {user_data.get('job_type', 'Any')}
• Min Salary: {user_data.get('min_salary', 'Any')} PLN
• Type: {user_data.get('contract_type', 'Any')}
• Location: {user_data.get('geography', 'trojmiasto')}
"""

    def _get_mock_jobs(self) -> list:
        """Get mock jobs for MVP"""
        return [
            {
                "title": "Python Backend Developer",
                "company": "TechCorp",
                "location": "Gdańsk",
                "salary_min": 8000,
                "salary_max": 12000,
                "contract_type": "Full-time",
                "work_location": "On-site",
                "required_skills": "Python, FastAPI, PostgreSQL",
                "url": "https://example.com/job/1",
            },
            {
                "title": "Frontend Developer",
                "company": "WebStudio",
                "location": "Sopot",
                "salary_min": 6500,
                "salary_max": 9500,
                "contract_type": "Full-time",
                "work_location": "Hybrid",
                "required_skills": "React, TypeScript, CSS",
                "url": "https://example.com/job/2",
            },
            {
                "title": "Data Scientist",
                "company": "DataWorks",
                "location": "Gdynia",
                "salary_min": 9000,
                "salary_max": 15000,
                "contract_type": "Full-time",
                "work_location": "Hybrid",
                "required_skills": "Python, SQL, ML, TensorFlow",
                "url": "https://example.com/job/3",
            },
        ]

    async def setup(self):
        """Set up conversation handler"""
        # Define conversation handler
        conv_handler = ConversationHandler(
            entry_points=[CommandHandler("start", self.start)],
            states={
                BotState.LANGUAGE_SELECT: [
                    CallbackQueryHandler(self.select_language)
                ],
                BotState.GEOGRAPHY_CONFIRM: [
                    CallbackQueryHandler(self.confirm_geography)
                ],
                BotState.JOB_TYPE_INPUT: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.input_job_type)
                ],
                BotState.SALARY_INPUT: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.input_salary)
                ],
                BotState.CONTRACT_SELECT: [
                    CallbackQueryHandler(self.select_contract)
                ],
                BotState.CRITERIA_CONFIRM: [
                    CallbackQueryHandler(self.confirm_criteria)
                ],
                BotState.RESULTS_DISPLAY: [
                    CallbackQueryHandler(self.handle_feedback)
                ],
                BotState.END: [
                    CallbackQueryHandler(self.handle_end)
                ],
            },
            fallbacks=[CommandHandler("start", self.start)],
        )

        # Add handler to application
        self.application.add_handler(conv_handler)

    async def start_polling(self):
        """Start bot in polling mode"""
        self.application = Application.builder().token(self.token).build()
        await self.setup()
        await self.application.run_polling()

    async def start_webhook(self, url: str):
        """Start bot in webhook mode"""
        self.application = Application.builder().token(self.token).build()
        await self.setup()
        await self.application.run_webhook(url)


# ========== STANDALONE USAGE ==========
"""
import asyncio
from config import get_settings

async def main():
    settings = get_settings()
    bot = TelegramBotHandler(settings.telegram_bot_token)
    await bot.start_polling()

asyncio.run(main())
"""
