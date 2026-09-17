"""
Job Radar MVP - LLM Integration
Support for Anthropic (Claude) and OpenAI (GPT) APIs
"""

import logging
from typing import Dict, Optional
from config import get_settings

logger = logging.getLogger(__name__)


class BaseLLMService:
    """Base class for LLM services"""

    def __init__(self):
        self.settings = get_settings()

    async def detect_language(self, text: str) -> str:
        """Detect language of text"""
        raise NotImplementedError

    async def extract_search_criteria(self, text: str) -> Dict:
        """Extract job search criteria from natural language"""
        raise NotImplementedError

    async def generate_explanation(self, job: Dict, user_language: str) -> str:
        """Generate explanation for match score"""
        raise NotImplementedError

    async def extract_job_listings(self, page_text: str, source_name: str) -> list:
        """
        LLM-assisted parsing: given the visible text of a job-search
        results page, extract structured job listings as a list of dicts.

        NOTE: this is functionally equivalent to scraping - the LLM is
        doing the parsing instead of regex/BeautifulSoup selectors, but
        the legal/ToS status of fetching+extracting a site's listings is
        unchanged either way. This was an explicit, informed decision for
        the MVP-validation stage (see sources.py) - revisit before any
        real launch/scale-up.
        """
        raise NotImplementedError


class AnthropicLLMService(BaseLLMService):
    """Anthropic/Claude LLM service"""

    def __init__(self):
        super().__init__()
        try:
            from anthropic import Anthropic
            self.client = Anthropic(api_key=self.settings.anthropic_api_key)
            self.available = True
            logger.info("✓ Anthropic/Claude API initialized")
        except ImportError:
            self.available = False
            logger.warning("⚠ Anthropic library not installed")
        except Exception as e:
            self.available = False
            logger.warning(f"⚠ Anthropic API error: {e}")

    async def detect_language(self, text: str) -> str:
        """
        Detect language using Claude

        Returns: 'ru', 'en', 'pl', 'uk'
        """
        if not self.available:
            # Fallback: simple heuristic
            return self._detect_language_fallback(text)

        try:
            prompt = f"""Detect the language of this text and respond with ONLY the language code:
- 'ru' for Russian
- 'en' for English
- 'pl' for Polish
- 'uk' for Ukrainian

Text: {text}

Response (only the language code):"""

            message = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=10,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )

            lang = message.content[0].text.strip().lower()

            # Validate
            if lang not in ['ru', 'en', 'pl', 'uk']:
                return self._detect_language_fallback(text)

            return lang

        except Exception as e:
            logger.warning(f"Claude language detection failed: {e}")
            return self._detect_language_fallback(text)

    async def extract_search_criteria(self, text: str) -> Dict:
        """
        Extract job search criteria from natural language using Claude

        Returns: Dict with job_title, min_salary, max_salary, location, etc.
        """
        if not self.available:
            return self._extract_criteria_fallback(text)

        try:
            prompt = f"""Extract job search criteria from this text and respond with JSON.
Return ONLY valid JSON, no other text.

Example response format:
{{"job_title": "Python Developer", "min_salary": 7000, "max_salary": 12000, "location": "Gdańsk", "contract_types": "full-time", "required_skills": "Python, FastAPI, PostgreSQL"}}

Text: {text}

JSON response:"""

            message = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=500,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )

            response_text = message.content[0].text.strip()

            # Parse JSON
            import json
            criteria = json.loads(response_text)

            # Validate and normalize
            return self._normalize_criteria(criteria)

        except Exception as e:
            logger.warning(f"Claude criteria extraction failed: {e}")
            return self._extract_criteria_fallback(text)

    async def generate_explanation(self, job: Dict, user_language: str) -> str:
        """
        Generate explanation for why this job matches using Claude
        """
        if not self.available:
            return "Good match for your criteria"

        try:
            lang_map = {
                'ru': 'Russian',
                'en': 'English',
                'pl': 'Polish',
                'uk': 'Ukrainian'
            }
            lang_name = lang_map.get(user_language, 'English')

            prompt = f"""Explain in 1-2 sentences why this job might be good for someone looking for {job.get('title', 'a job')}.
Write in {lang_name}.
Keep it concise and encouraging.

Job: {job.get('title')} at {job.get('company')}
Salary: {job.get('salary_min', 'N/A')}-{job.get('salary_max', 'N/A')} PLN
Location: {job.get('location')}

Explanation:"""

            message = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=150,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )

            return message.content[0].text.strip()

        except Exception as e:
            logger.warning(f"Claude explanation generation failed: {e}")
            return "Interesting opportunity matching your criteria"

    async def extract_job_listings(self, page_text: str, source_name: str) -> list:
        """Extract structured job listings from raw page text using Claude"""
        if not self.available:
            logger.warning(f"⚠ Claude unavailable - cannot LLM-parse {source_name}, returning no jobs")
            return []

        # Keep the prompt bounded - search result pages can be long
        truncated = page_text[:12000]

        prompt = f"""Below is the visible text of a job search results page from {source_name}.
Extract every distinct job listing you can find and return ONLY a valid JSON array,
no other text. Each item must have exactly these keys (use null when not present):
title, company, location, salary_min, salary_max, currency, contract_type,
work_location, required_skills, url, published_date

salary_min/salary_max must be integers or null (strip currency symbols/text).
url should be the full listing URL if present in the text, else null.
If you find no listings, return an empty array: []

PAGE TEXT:
{truncated}

JSON array:"""

        try:
            message = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=4000,
                messages=[{"role": "user", "content": prompt}],
            )
            raw = message.content[0].text.strip()
            # Strip markdown code fences if the model added them anyway
            if raw.startswith("```"):
                raw = raw.strip("`")
                if raw.startswith("json"):
                    raw = raw[4:]
            import json
            listings = json.loads(raw)
            if not isinstance(listings, list):
                logger.warning(f"Claude job extraction for {source_name} did not return a list")
                return []
            return listings
        except Exception as e:
            logger.warning(f"Claude job-listing extraction failed for {source_name}: {e}")
            return []

    def _detect_language_fallback(self, text: str) -> str:
        """Fallback language detection using simple heuristics"""
        # Cyrillic for Russian/Ukrainian
        if any('Ѐ' <= char <= 'ӿ' for char in text):
            # Cyrillic detected
            if 'ь' in text.lower() or 'й' in text.lower():
                return 'ru'  # Russian
            return 'uk'  # Ukrainian

        # Polish characters
        if any(char in 'ąćęłńóśźż' for char in text.lower()):
            return 'pl'

        # Default to English
        return 'en'

    def _extract_criteria_fallback(self, text: str) -> Dict:
        """Fallback criteria extraction"""
        return {
            "job_title": text[:50] if text else "Job search",
            "min_salary": None,
            "max_salary": None,
            "location": "trojmiasto",
            "contract_types": "full-time",
        }

    def _normalize_criteria(self, criteria: Dict) -> Dict:
        """Normalize extracted criteria"""
        return {
            "job_title": criteria.get("job_title", "").strip(),
            "min_salary": self._parse_salary(criteria.get("min_salary")),
            "max_salary": self._parse_salary(criteria.get("max_salary")),
            "location": (criteria.get("location") or "trojmiasto").lower(),
            "contract_types": (criteria.get("contract_types") or "full-time").lower(),
            "required_skills": criteria.get("required_skills", ""),
            "excluded_keywords": criteria.get("excluded_keywords", ""),
        }

    @staticmethod
    def _parse_salary(salary) -> Optional[int]:
        """Parse salary from various formats"""
        if not salary:
            return None

        if isinstance(salary, int):
            return salary

        if isinstance(salary, str):
            # Extract digits
            import re
            match = re.search(r'\d+', salary)
            return int(match.group()) if match else None

        return None


class OpenAILLMService(BaseLLMService):
    """OpenAI/GPT LLM service"""

    def __init__(self):
        super().__init__()
        try:
            from openai import OpenAI
            self.client = OpenAI(api_key=self.settings.openai_api_key)
            self.available = True
            logger.info("✓ OpenAI/GPT API initialized")
        except ImportError:
            self.available = False
            logger.warning("⚠ OpenAI library not installed")
        except Exception as e:
            self.available = False
            logger.warning(f"⚠ OpenAI API error: {e}")

    async def detect_language(self, text: str) -> str:
        """Detect language using GPT"""
        if not self.available:
            return self._detect_language_fallback(text)

        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                max_tokens=10,
                messages=[
                    {
                        "role": "user",
                        "content": f"""Detect the language. Respond with ONLY: ru, en, pl, or uk
Text: {text}"""
                    }
                ]
            )

            lang = response.choices[0].message.content.strip().lower()
            return lang if lang in ['ru', 'en', 'pl', 'uk'] else 'en'

        except Exception as e:
            logger.warning(f"GPT language detection failed: {e}")
            return self._detect_language_fallback(text)

    async def extract_search_criteria(self, text: str) -> Dict:
        """Extract criteria using GPT"""
        if not self.available:
            return self._extract_criteria_fallback(text)

        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                max_tokens=500,
                messages=[
                    {
                        "role": "user",
                        "content": f"""Extract job criteria as JSON. Return ONLY JSON.
Text: {text}"""
                    }
                ]
            )

            import json
            criteria = json.loads(response.choices[0].message.content)
            return self._normalize_criteria(criteria)

        except Exception as e:
            logger.warning(f"GPT criteria extraction failed: {e}")
            return self._extract_criteria_fallback(text)

    async def generate_explanation(self, job: Dict, user_language: str) -> str:
        """Generate explanation using GPT"""
        if not self.available:
            return "Good match for your criteria"

        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                max_tokens=150,
                messages=[
                    {
                        "role": "user",
                        "content": f"""Explain in 1-2 sentences (in {user_language}) why this job is a good match:
Job: {job.get('title')} at {job.get('company')}"""
                    }
                ]
            )

            return response.choices[0].message.content.strip()

        except Exception as e:
            logger.warning(f"GPT explanation generation failed: {e}")
            return "Interesting opportunity"

    async def extract_job_listings(self, page_text: str, source_name: str) -> list:
        """Extract structured job listings from raw page text using GPT"""
        if not self.available:
            logger.warning(f"⚠ GPT unavailable - cannot LLM-parse {source_name}, returning no jobs")
            return []

        truncated = page_text[:12000]

        prompt = f"""Below is the visible text of a job search results page from {source_name}.
Extract every distinct job listing you can find and return ONLY a valid JSON array,
no other text. Each item must have exactly these keys (use null when not present):
title, company, location, salary_min, salary_max, currency, contract_type,
work_location, required_skills, url, published_date

salary_min/salary_max must be integers or null (strip currency symbols/text).
url should be the full listing URL if present in the text, else null.
If you find no listings, return an empty array: []

PAGE TEXT:
{truncated}

JSON array:"""

        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                max_tokens=4000,
                messages=[{"role": "user", "content": prompt}],
            )
            raw = response.choices[0].message.content.strip()
            if raw.startswith("```"):
                raw = raw.strip("`")
                if raw.startswith("json"):
                    raw = raw[4:]
            import json
            listings = json.loads(raw)
            if not isinstance(listings, list):
                logger.warning(f"GPT job extraction for {source_name} did not return a list")
                return []
            return listings
        except Exception as e:
            logger.warning(f"GPT job-listing extraction failed for {source_name}: {e}")
            return []

    def _detect_language_fallback(self, text: str) -> str:
        """Fallback detection"""
        if any('Ѐ' <= char <= 'ӿ' for char in text):
            return 'ru'
        if any(char in 'ąćęłńóśźż' for char in text.lower()):
            return 'pl'
        return 'en'

    def _extract_criteria_fallback(self, text: str) -> Dict:
        """Fallback extraction"""
        return {
            "job_title": text[:50] if text else "Job",
            "min_salary": None,
            "max_salary": None,
            "location": "trojmiasto",
        }

    def _normalize_criteria(self, criteria: Dict) -> Dict:
        """Normalize criteria"""
        return {
            "job_title": criteria.get("job_title", "").strip(),
            "min_salary": criteria.get("min_salary"),
            "max_salary": criteria.get("max_salary"),
            "location": (criteria.get("location") or "trojmiasto").lower(),
            "contract_types": (criteria.get("contract_types") or "full-time").lower(),
        }


class LLMServiceFactory:
    """Factory to get appropriate LLM service"""

    _service_instance = None

    @classmethod
    def get_service(cls) -> BaseLLMService:
        """Get LLM service based on configuration"""
        if cls._service_instance is not None:
            return cls._service_instance

        settings = get_settings()

        if settings.llm_provider == "anthropic":
            cls._service_instance = AnthropicLLMService()
        elif settings.llm_provider == "openai":
            cls._service_instance = OpenAILLMService()
        else:
            logger.warning(f"Unknown LLM provider: {settings.llm_provider}")
            # Fallback: try Anthropic
            cls._service_instance = AnthropicLLMService()

        return cls._service_instance


def get_llm_service() -> BaseLLMService:
    """Get LLM service instance"""
    return LLMServiceFactory.get_service()


# ========== USAGE EXAMPLE ==========
"""
import asyncio
from llm_service import get_llm_service

async def main():
    service = get_llm_service()

    # Detect language
    lang = await service.detect_language("Я ищу работу Python разработчика")
    print(f"Language: {lang}")  # Output: ru

    # Extract criteria
    criteria = await service.extract_search_criteria(
        "Ищу Python developer работу в Gdańsku, full-time, не менее 7000 PLN"
    )
    print(f"Criteria: {criteria}")

    # Generate explanation
    job = {
        "title": "Python Developer",
        "company": "TechCorp",
        "salary_min": 8000,
        "salary_max": 12000
    }
    explanation = await service.generate_explanation(job, "en")
    print(f"Explanation: {explanation}")

asyncio.run(main())
"""
