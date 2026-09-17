"""
Job Radar MVP - Job Sources
Adapter pattern for different job sources (websites, APIs, etc.)
"""

import logging
from typing import List, Dict
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class JobSource:
    """Base class for job sources"""

    def __init__(self, name: str, url: str, source_type: str):
        self.name = name
        self.url = url
        self.source_type = source_type  # "website", "api", "telegram"

    async def fetch_jobs(self, criteria: Dict = None) -> List[Dict]:
        """Fetch jobs from source - override in subclass"""
        raise NotImplementedError


class PracujPlSource(JobSource):
    """pracuj.pl job source - Polish job portal"""

    def __init__(self):
        super().__init__(
            name="pracuj.pl",
            url="https://www.pracuj.pl",
            source_type="website"
        )

    async def fetch_jobs(self, criteria: Dict = None) -> List[Dict]:
        """
        Fetch jobs from pracuj.pl

        In production: Use their API or web scraping
        For MVP: Return mock data
        """
        # Mock data for MVP
        return [
            {
                "title": "Python Backend Developer",
                "company": "TechCorp Poland",
                "location": "Gdańsk",
                "salary_min": 8000,
                "salary_max": 12000,
                "currency": "PLN",
                "contract_type": "full-time",
                "work_location": "on-site",
                "required_skills": "Python, FastAPI, PostgreSQL, Docker",
                "requirements": "3+ years Python experience, BS in CS",
                "benefits": '["Health insurance", "Remote days 2x/week", "Training budget"]',
                "description": "We are looking for an experienced Python developer to join our backend team. You will work on scalable APIs and microservices for our platform.",
                "url": "https://www.pracuj.pl/job/python-backend-gdansk",
                "published_date": (datetime.utcnow() - timedelta(days=2)).isoformat(),
            },
            {
                "title": "Full Stack Developer",
                "company": "WebStudio",
                "location": "Sopot",
                "salary_min": 6500,
                "salary_max": 9500,
                "currency": "PLN",
                "contract_type": "full-time",
                "work_location": "hybrid",
                "required_skills": "React, Python, TypeScript, PostgreSQL",
                "requirements": "2+ years experience with React and backend",
                "benefits": '["Flexible hours", "Office gym", "Stock options"]',
                "description": "Join our dynamic team building web applications for startups. Work with modern tech stack.",
                "url": "https://www.pracuj.pl/job/full-stack-sopot",
                "published_date": (datetime.utcnow() - timedelta(days=1)).isoformat(),
            },
        ]


class OLXSource(JobSource):
    """OLX job source - Classified ads platform"""

    def __init__(self):
        super().__init__(
            name="OLX",
            url="https://www.olx.pl",
            source_type="website"
        )

    async def fetch_jobs(self, criteria: Dict = None) -> List[Dict]:
        """Fetch jobs from OLX - mock data for MVP"""
        return [
            {
                "title": "Senior Data Scientist",
                "company": "DataWorks Gdańsk",
                "location": "Gdynia",
                "salary_min": 9000,
                "salary_max": 15000,
                "currency": "PLN",
                "contract_type": "full-time",
                "work_location": "hybrid",
                "required_skills": "Python, SQL, Machine Learning, TensorFlow, Pandas",
                "requirements": "5+ years in ML/Data Science, Masters preferred",
                "benefits": '["Competitive salary", "Flexible schedule", "Home office"]',
                "description": "We need a senior data scientist to lead ML initiatives and build predictive models.",
                "url": "https://www.olx.pl/job/data-scientist-gdynia",
                "published_date": (datetime.utcnow() - timedelta(days=3)).isoformat(),
            },
            {
                "title": "DevOps Engineer",
                "company": "CloudSys",
                "location": "Gdańsk",
                "salary_min": 7500,
                "salary_max": 11000,
                "currency": "PLN",
                "contract_type": "full-time",
                "work_location": "remote",
                "required_skills": "Docker, Kubernetes, AWS, CI/CD, Terraform",
                "requirements": "3+ years DevOps/SRE experience",
                "benefits": '["Remote work", "Learning budget", "Gym membership"]',
                "description": "Looking for a DevOps engineer to maintain and improve our cloud infrastructure.",
                "url": "https://www.olx.pl/job/devops-gdansk",
                "published_date": (datetime.utcnow() - timedelta(days=4)).isoformat(),
            },
        ]


class LinkedInSource(JobSource):
    """LinkedIn job source - Professional network"""

    def __init__(self):
        super().__init__(
            name="LinkedIn",
            url="https://www.linkedin.com",
            source_type="api"
        )

    async def fetch_jobs(self, criteria: Dict = None) -> List[Dict]:
        """Fetch jobs from LinkedIn - mock data for MVP"""
        return [
            {
                "title": "Machine Learning Engineer",
                "company": "AI Innovations",
                "location": "Gdańsk",
                "salary_min": 10000,
                "salary_max": 16000,
                "currency": "PLN",
                "contract_type": "full-time",
                "work_location": "on-site",
                "required_skills": "Python, PyTorch, TensorFlow, Research",
                "requirements": "PhD or Masters in ML/CS, 2+ years production ML",
                "benefits": '["Cutting edge tech", "Research opportunities", "Relocation package"]',
                "description": "Join our AI team working on cutting-edge machine learning solutions for enterprise clients.",
                "url": "https://www.linkedin.com/job/ml-engineer-gdansk",
                "published_date": (datetime.utcnow() - timedelta(days=5)).isoformat(),
            },
        ]


class IndeedSource(JobSource):
    """Indeed job source - International job board"""

    def __init__(self):
        super().__init__(
            name="Indeed",
            url="https://www.indeed.com",
            source_type="website"
        )

    async def fetch_jobs(self, criteria: Dict = None) -> List[Dict]:
        """Fetch jobs from Indeed - mock data for MVP"""
        return [
            {
                "title": "QA Engineer",
                "company": "SoftwareHouse",
                "location": "Sopot",
                "salary_min": 5500,
                "salary_max": 8000,
                "currency": "PLN",
                "contract_type": "full-time",
                "work_location": "on-site",
                "required_skills": "Python, Selenium, TestNG, SQL",
                "requirements": "2+ years QA automation experience",
                "benefits": '["Career growth", "Nice office", "Team events"]',
                "description": "Automation QA engineer needed to build test frameworks and ensure software quality.",
                "url": "https://www.indeed.com/job/qa-sopot",
                "published_date": (datetime.utcnow() - timedelta(days=6)).isoformat(),
            },
        ]


class TelegramSource(JobSource):
    """Telegram channels - Community job announcements"""

    def __init__(self):
        super().__init__(
            name="Telegram Channels",
            url="https://telegram.org",
            source_type="telegram"
        )

    async def fetch_jobs(self, criteria: Dict = None) -> List[Dict]:
        """Fetch jobs from Telegram - mock data for MVP"""
        return [
            {
                "title": "Rust Developer",
                "company": "SystemsLab",
                "location": "Gdańsk",
                "salary_min": 9000,
                "salary_max": 13000,
                "currency": "PLN",
                "contract_type": "full-time",
                "work_location": "remote",
                "required_skills": "Rust, System Programming, Linux",
                "requirements": "2+ years Rust experience",
                "benefits": '["Remote", "Flexible", "Equity"]',
                "description": "Startup building systems infrastructure in Rust. Fast paced, innovative environment.",
                "url": "https://t.me/jobschannel/1234",
                "published_date": (datetime.utcnow() - timedelta(days=1)).isoformat(),
            },
        ]


class JobSourceManager:
    """Manager for multiple job sources"""

    def __init__(self):
        """Initialize all sources"""
        self.sources = {
            "pracuj": PracujPlSource(),
            "olx": OLXSource(),
            "linkedin": LinkedInSource(),
            "indeed": IndeedSource(),
            "telegram": TelegramSource(),
        }

    async def fetch_all_jobs(self, criteria: Dict = None) -> List[Dict]:
        """
        Fetch jobs from all sources

        Args:
            criteria: Search criteria (optional filtering)

        Returns:
            Combined list of jobs from all sources
        """
        all_jobs = []

        for source_key, source in self.sources.items():
            try:
                jobs = await source.fetch_jobs(criteria)

                # Add source_id to each job
                for job in jobs:
                    job["source"] = source.name
                    job["source_key"] = source_key

                all_jobs.extend(jobs)
                logger.info(f"✓ Fetched {len(jobs)} jobs from {source.name}")

            except Exception as e:
                logger.error(f"✗ Error fetching from {source.name}: {str(e)}")

        logger.info(f"Total jobs collected: {len(all_jobs)}")
        return all_jobs

    async def fetch_from_source(self, source_key: str, criteria: Dict = None) -> List[Dict]:
        """
        Fetch jobs from specific source

        Args:
            source_key: Source identifier (e.g., "pracuj", "olx")
            criteria: Search criteria (optional)

        Returns:
            Jobs from that source
        """
        if source_key not in self.sources:
            logger.error(f"Unknown source: {source_key}")
            return []

        source = self.sources[source_key]
        try:
            jobs = await source.fetch_jobs(criteria)
            logger.info(f"✓ Fetched {len(jobs)} jobs from {source.name}")
            return jobs
        except Exception as e:
            logger.error(f"✗ Error fetching from {source.name}: {str(e)}")
            return []

    def get_available_sources(self) -> List[Dict]:
        """Get list of available sources"""
        return [
            {
                "key": key,
                "name": source.name,
                "url": source.url,
                "type": source.source_type,
            }
            for key, source in self.sources.items()
        ]


# ========== USAGE EXAMPLE ==========
"""
import asyncio
from sources import JobSourceManager

async def main():
    # Create manager
    manager = JobSourceManager()

    # Fetch from all sources
    all_jobs = await manager.fetch_all_jobs()

    # Fetch from specific source
    pracuj_jobs = await manager.fetch_from_source("pracuj")

    # List available sources
    sources = manager.get_available_sources()
    print(sources)

asyncio.run(main())
"""
