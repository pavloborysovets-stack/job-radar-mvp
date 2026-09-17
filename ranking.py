"""
Job Radar MVP - Job Ranking Algorithm
Matches jobs against user search criteria with 8 scoring factors
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Tuple

logger = logging.getLogger(__name__)


class JobMatcher:
    """
    Ranks jobs based on how well they match user criteria

    Uses 8 scoring factors:
    1. Criteria Match (must-have requirements) - 25%
    2. Salary Match (salary range) - 20%
    3. Location Match (geography preferences) - 15%
    4. Contract Match (employment type) - 15%
    5. Skills Match (required skills match) - 10%
    6. Language Match (job language requirements) - 5%
    7. Recency Score (how recent is the job) - 5%
    8. Exclusion Penalty (penalties for excluded keywords) - (-10% max)

    Final score: 0-100 (higher is better)
    """

    def __init__(self):
        """Initialize matcher with default weights"""
        self.weights = {
            "criteria": 0.25,      # Must-have criteria
            "salary": 0.20,        # Salary range match
            "location": 0.15,      # Geography
            "contract": 0.15,      # Contract type
            "skills": 0.10,        # Technical skills
            "language": 0.05,      # Language requirements
            "recency": 0.05,       # How recent
            "exclusion": -0.10,    # Penalty for exclusions
        }

    def match_job(
        self,
        job: Dict,
        search_profile: Dict,
        user_language: str = "en"
    ) -> Dict:
        """
        Calculate match score for a job against user criteria

        Args:
            job: Job card data
            search_profile: User's search preferences
            user_language: User's language (for translations)

        Returns:
            Dict with match_score and component scores
        """
        scores = {
            "criteria_match": self._score_criteria_match(job, search_profile),
            "salary_match": self._score_salary_match(job, search_profile),
            "location_match": self._score_location_match(job, search_profile),
            "contract_match": self._score_contract_match(job, search_profile),
            "skills_match": self._score_skills_match(job, search_profile),
            "language_match": self._score_language_match(job, user_language),
            "recency_score": self._score_recency(job),
            "exclusion_score": self._score_exclusions(job, search_profile),
        }

        # Calculate weighted final score
        match_score = (
            scores["criteria_match"] * self.weights["criteria"] +
            scores["salary_match"] * self.weights["salary"] +
            scores["location_match"] * self.weights["location"] +
            scores["contract_match"] * self.weights["contract"] +
            scores["skills_match"] * self.weights["skills"] +
            scores["language_match"] * self.weights["language"] +
            scores["recency_score"] * self.weights["recency"] +
            scores["exclusion_score"] * self.weights["exclusion"]
        )

        # Ensure score is between 0-100
        match_score = max(0, min(100, int(match_score)))

        return {
            "match_score": match_score,
            **scores
        }

    def _score_criteria_match(self, job: Dict, profile: Dict) -> int:
        """
        Score 1: How well job matches must-have criteria

        Must-have criteria are the job title/role
        """
        job_title = (job.get("title") or "").lower()
        criteria_title = (profile.get("job_title") or "").lower()

        if not criteria_title:
            return 50  # Neutral score if no criteria specified

        # Exact match
        if criteria_title in job_title:
            return 100

        # Partial match (keywords)
        keywords = criteria_title.split()
        matched = sum(1 for kw in keywords if kw in job_title)

        if len(keywords) > 0:
            match_percent = (matched / len(keywords)) * 100
            return int(match_percent)

        return 0

    def _score_salary_match(self, job: Dict, profile: Dict) -> int:
        """
        Score 2: How well salary matches expectations

        Ideal: job's salary range >= user's min salary
        """
        job_min = job.get("salary_min")
        job_max = job.get("salary_max")
        user_min = profile.get("min_salary")
        user_max = profile.get("max_salary")

        # No salary info
        if not job_min or not job_max:
            return 60  # Neutral (missing data)

        # No user expectations
        if not user_min:
            return 70  # Neutral (no filter specified)

        # Calculate overlap
        if job_min >= user_min:
            # Job meets minimum
            if user_max and job_min <= user_max:
                # Job is within user's range
                return 100
            elif not user_max:
                # User has no max
                return 90
            else:
                # Job exceeds max (still good)
                return 75
        else:
            # Job doesn't meet minimum
            shortage_percent = (job_min / user_min) * 100
            return max(0, int(shortage_percent))

    def _score_location_match(self, job: Dict, profile: Dict) -> int:
        """
        Score 3: How well location matches preferences

        Prefer: on-site/hybrid in target geography, or remote
        """
        job_location = (job.get("location") or "").lower()
        job_work_location = (job.get("work_location") or "").lower()
        user_geography = (profile.get("geography") or "trojmiasto").lower()

        # Remote is always good
        if "remote" in job_work_location:
            return 95

        # On-site or hybrid - check geography
        trojmiasto_cities = ["gdańsk", "gdynia", "sopot", "trojmiasto", "gdansk"]
        job_in_trojmiasto = any(city in job_location for city in trojmiasto_cities)

        if user_geography == "trojmiasto" and job_in_trojmiasto:
            if "on-site" in job_work_location or "hybrid" in job_work_location:
                return 100
            else:
                return 80

        # Other location - partially match
        if user_geography in job_location:
            return 80

        # Different location
        if "on-site" in job_work_location:
            return 30  # Requires relocation
        else:
            return 60  # Maybe hybrid or other arrangement

    def _score_contract_match(self, job: Dict, profile: Dict) -> int:
        """
        Score 4: How well contract type matches preferences
        """
        job_contract = (job.get("contract_type") or "").lower()
        user_contracts = (profile.get("contract_types") or "").lower()

        # No preference specified
        if not user_contracts:
            return 70

        # Check for match
        contract_list = [c.strip() for c in user_contracts.split(",")]

        for contract in contract_list:
            if contract in job_contract:
                return 100

        # Partial match
        if "full-time" in user_contracts and ("full" in job_contract or "contract" not in job_contract):
            return 70

        return 30  # No match

    def _score_skills_match(self, job: Dict, profile: Dict) -> int:
        """
        Score 5: How well required skills match
        """
        job_skills = (job.get("required_skills") or "").lower()
        user_skills = (profile.get("required_skills") or "").lower()

        if not user_skills:
            return 70  # No preference

        # Split into individual skills
        user_skill_list = [s.strip() for s in user_skills.split(",")]

        # Count matches
        matched = 0
        for skill in user_skill_list:
            if skill in job_skills:
                matched += 1

        # Calculate percentage
        match_percent = (matched / len(user_skill_list)) * 100 if user_skill_list else 70
        return int(match_percent)

    def _score_language_match(self, job: Dict, user_language: str) -> int:
        """
        Score 6: Language requirement match
        """
        job_description = (job.get("description") or "").lower()
        job_requirements = (job.get("requirements") or "").lower()

        # Simplified: check if English/Polish is mentioned
        # In real system, would do proper language detection

        if user_language == "en":
            if "english" in job_description or "english" in job_requirements:
                return 100
            return 70

        elif user_language == "pl":
            if "polish" in job_description or "polski" in job_description:
                return 100
            return 70

        elif user_language == "ru":
            if "russian" in job_description or "русский" in job_description:
                return 100
            return 60  # Russian speakers can often work in English

        return 70  # Default

    def _score_recency(self, job: Dict) -> int:
        """
        Score 7: How recent is the job posting

        Prefer: posted in last 7 days
        Acceptable: posted in last 30 days
        """
        published = job.get("published_date")

        if not published:
            return 60  # Unknown date

        try:
            # Parse date if it's a string
            if isinstance(published, str):
                published = datetime.fromisoformat(published.replace("Z", "+00:00"))

            days_old = (datetime.utcnow() - published).days

            if days_old <= 7:
                return 100  # Very recent
            elif days_old <= 14:
                return 90   # Recent
            elif days_old <= 30:
                return 70   # Acceptable
            elif days_old <= 60:
                return 40   # Getting old
            else:
                return 20   # Stale

        except Exception as e:
            logger.warning(f"Error parsing job date: {e}")
            return 60

    def _score_exclusions(self, job: Dict, profile: Dict) -> int:
        """
        Score 8: Penalty for excluded keywords

        Returns negative score (penalty) if excluded keywords found
        """
        excluded = (profile.get("excluded_keywords") or "").lower()

        if not excluded:
            return 0  # No exclusions

        job_text = (
            (job.get("title") or "") + " " +
            (job.get("description") or "") + " " +
            (job.get("requirements") or "")
        ).lower()

        # Check for excluded keywords
        excluded_list = [e.strip() for e in excluded.split(",")]

        found_exclusions = 0
        for keyword in excluded_list:
            if keyword in job_text:
                found_exclusions += 1

        # Penalty: -10% per excluded keyword found
        penalty = min(100, found_exclusions * 10)
        return -penalty

    def rank_jobs(
        self,
        jobs: List[Dict],
        search_profile: Dict,
        user_language: str = "en",
        min_score: int = 0,
        limit: int = None
    ) -> List[Dict]:
        """
        Rank multiple jobs against criteria

        Args:
            jobs: List of job cards
            search_profile: User's search preferences
            user_language: User's language
            min_score: Minimum score to include (0-100)
            limit: Maximum jobs to return

        Returns:
            Sorted list of jobs with scores
        """
        results = []

        for job in jobs:
            score_data = self.match_job(job, search_profile, user_language)

            if score_data["match_score"] >= min_score:
                results.append({
                    **job,
                    **score_data
                })

        # Sort by score (highest first)
        results.sort(key=lambda x: x["match_score"], reverse=True)

        # Limit results
        if limit:
            results = results[:limit]

        return results


# ========== USAGE EXAMPLE ==========
"""
from ranking import JobMatcher

# Create matcher
matcher = JobMatcher()

# User's search profile
profile = {
    "job_title": "Python developer",
    "min_salary": 7000,
    "max_salary": 12000,
    "currency": "PLN",
    "contract_types": "full-time",
    "geography": "trojmiasto",
    "required_skills": "Python, FastAPI, PostgreSQL",
    "excluded_keywords": "Java, PHP",
}

# Sample jobs
jobs = [
    {
        "title": "Python Developer",
        "company": "TechCorp",
        "location": "Gdańsk",
        "salary_min": 7000,
        "salary_max": 11000,
        "contract_type": "full-time",
        "work_location": "on-site",
        "required_skills": "Python, FastAPI, PostgreSQL",
        "description": "We need a Python expert...",
        "requirements": "3+ years experience",
        "published_date": "2026-09-17T10:00:00",
    },
    {
        "title": "Java Developer",
        "company": "OtherCorp",
        "location": "Warsaw",
        "salary_min": 6000,
        "salary_max": 9000,
        "contract_type": "full-time",
        "work_location": "remote",
        "required_skills": "Java, Spring",
        "description": "Java backend developer needed...",
        "requirements": "2+ years",
        "published_date": "2026-09-16T10:00:00",
    },
]

# Rank jobs
ranked = matcher.rank_jobs(jobs, profile, user_language="en", min_score=30, limit=10)

# Results will be sorted by match_score (highest first)
for job in ranked:
    print(f"{job['title']}: {job['match_score']}/100")
"""
