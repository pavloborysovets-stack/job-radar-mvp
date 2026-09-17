"""
Job Radar MVP - Job Sources
Adapter pattern for different job sources (websites, APIs, etc.)

IMPORTANT (2026-09-17): Earlier versions of this file returned hardcoded
FAKE job listings from every source ("mock data for MVP"). That was removed.
A source now either:
  (a) performs a real fetch against a real, legal data provider, or
  (b) is not implemented yet and returns an EMPTY list with a clear log
      message - it never invents data.

Currently real: CBOPSource (Poland's official government job-offer
database, "Centralna Baza Ofert Pracy" / ePraca, CC BY 4.0 license,
https://dane.gov.pl/pl/dataset/538,oferty-pracy-psz). It requires a
"Partner" access code issued by the Ministry (Ministerstwo Rodziny,
Pracy i Polityki Spolecznej) - set it via the CBOP_PARTNER_CODE
environment variable. Until that code is configured, CBOPSource also
returns an empty list rather than failing.

Everything else (pracuj.pl, OLX, LinkedIn, Indeed, Telegram channels)
is a placeholder adapter matching ARCHITECTURE.md's target source list,
waiting on real (legal, ToS-compliant) integration work.
"""

import asyncio
import io
import json
import logging
import os
import re
import zipfile
from datetime import datetime
from typing import Dict, List, Optional
from urllib.parse import quote

import aiohttp

logger = logging.getLogger(__name__)


class JobSource:
    """Base class for job sources"""

    def __init__(self, name: str, url: str, source_type: str):
        self.name = name
        self.url = url
        self.source_type = source_type  # "website", "api", "telegram", "government"

    async def fetch_jobs(self, criteria: Dict = None) -> List[Dict]:
        """Fetch jobs from source - override in subclass"""
        raise NotImplementedError


# ========== REAL SOURCE: CBOP / ePraca (Polish government job database) ==========

# GUS/TERYT voivodeship codes - Trojmiasto (Gdansk/Gdynia/Sopot) is in Pomorskie
VOIVODESHIP_CODES = {
    "pomorskie": "22",       # Gdansk, Gdynia, Sopot (Trojmiasto)
    "mazowieckie": "14",     # Warsaw
    "malopolskie": "12",     # Krakow
    "dolnoslaskie": "02",    # Wroclaw
    "wielkopolskie": "30",   # Poznan
}


class CBOPSource(JobSource):
    """
    Centralna Baza Ofert Pracy (CBOP) / ePraca - official Polish government
    job offer database, maintained by the Ministry of Family, Labor and
    Social Policy. Free to reuse under CC BY 4.0.

    Access requires a "Partner" code issued by the Ministry after
    registration (see the terms document linked from the dataset page).
    Set CBOP_PARTNER_CODE in the environment once you have one.

    NOTE ON FIELD MAPPING: the exact JSON schema returned inside the
    service's zip payload has NOT been verified yet against a live
    response (that requires an approved Partner code to test with).
    _parse_offer() below maps the field names documented in
    "Instrukcja pobierania danych z CBOP" as best as they could be
    confirmed from public documentation. The first real response should
    be logged and this mapping double-checked/adjusted - see the
    logger.debug("CBOP raw offer keys...") line below.
    """

    ENDPOINT = "https://oferty.praca.gov.pl/integration/services/oferta"
    NAMESPACE = "http://oferty.praca.gov.pl/v2/oferta"

    def __init__(self):
        super().__init__(
            name="CBOP (ePraca)",
            url="https://oferty.praca.gov.pl/portal/index.cbop",
            source_type="government",
        )
        self.partner_code = os.getenv("CBOP_PARTNER_CODE", "").strip()
        self.voivodeship = os.getenv("CBOP_VOIVODESHIP_CODE", VOIVODESHIP_CODES["pomorskie"])

    async def fetch_jobs(self, criteria: Dict = None) -> List[Dict]:
        if not self.partner_code:
            logger.warning(
                "⚠ CBOP_PARTNER_CODE not set - skipping CBOP source "
                "(register at https://dane.gov.pl/pl/dataset/538,oferty-pracy-psz "
                "to get a Partner code). Returning no jobs, not fake ones."
            )
            return []

        soap_body = self._build_soap_request(criteria or {})

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.ENDPOINT,
                    data=soap_body,
                    headers={
                        "Content-Type": "text/xml; charset=utf-8",
                        "SOAPAction": "",
                    },
                    timeout=aiohttp.ClientTimeout(total=30),
                ) as resp:
                    raw = await resp.read()
                    if resp.status != 200:
                        logger.error(f"✗ CBOP request failed: HTTP {resp.status}")
                        return []

            offers = self._extract_offers(raw)
            jobs = [self._parse_offer(o) for o in offers]
            jobs = [j for j in jobs if j]  # drop any that failed to parse
            logger.info(f"✓ Fetched {len(jobs)} jobs from CBOP")
            return jobs

        except Exception as e:
            logger.error(f"✗ Error fetching from CBOP: {str(e)}")
            return []

    def _build_soap_request(self, criteria: Dict) -> str:
        """Build the SOAP <Dane> request envelope per CBOP's WSDL"""
        # Prefer a specific voivodeship (fast, scoped to Trojmiasto);
        # criteria can override with an explicit "wszystkie" flag if a
        # nationwide search is ever needed.
        if criteria.get("wszystkie"):
            kryterium = "<Wszystkie>true</Wszystkie>"
        else:
            kryterium = f"<Kryterium><Wojewodztwo>{self.voivodeship}</Wojewodztwo></Kryterium>"

        return f"""<?xml version="1.0" encoding="UTF-8"?>
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/"
 xmlns:ofer="{self.NAMESPACE}">
 <soapenv:Body>
  <ofer:Dane>
   <pytanie>
    <Partner>{self.partner_code}</Partner>
    <Jezyk>pl</Jezyk>
    {kryterium}
   </pytanie>
  </ofer:Dane>
 </soapenv:Body>
</soapenv:Envelope>"""

    def _extract_offers(self, raw_response: bytes) -> List[Dict]:
        """
        The service returns job offers as one or more zipped JSON files
        (up to 1000 offers per file), referenced/embedded in the SOAP
        response. Handle both a directly-embedded zip and a plain XML
        response defensively, logging what we actually got so the
        format can be confirmed on first real use.
        """
        offers: List[Dict] = []

        # Case 1: response body itself is a zip (starts with PK magic bytes)
        if raw_response[:2] == b"PK":
            offers.extend(self._offers_from_zip(raw_response))
            return offers

        # Case 2: SOAP/XML envelope containing base64-encoded zip content,
        # or a direct URL to download the result file. Parse loosely.
        try:
            text = raw_response.decode("utf-8", errors="ignore")
        except Exception:
            text = ""

        import base64
        import re

        # Try to find a base64 blob inside the XML response
        b64_match = re.search(r"<[\w:]*(?:Zawartosc|Plik|Dane)[^>]*>([A-Za-z0-9+/=\s]{100,})</", text)
        if b64_match:
            try:
                decoded = base64.b64decode(b64_match.group(1))
                if decoded[:2] == b"PK":
                    offers.extend(self._offers_from_zip(decoded))
                    return offers
            except Exception as e:
                logger.warning(f"CBOP response looked base64 but failed to decode: {e}")

        # Try to find a download URL for the result file
        url_match = re.search(r"<[\w:]*(?:Url|Link|Adres)[^>]*>(https?://[^<]+)</", text)
        if url_match:
            logger.info(f"CBOP response points to a result file: {url_match.group(1)} "
                        f"(not yet auto-downloaded - add a follow-up GET here once verified)")
            return offers

        logger.warning(
            "CBOP response format not recognized (no zip, no base64 zip, no result URL). "
            f"First 300 bytes for debugging: {raw_response[:300]!r}"
        )
        return offers

    def _offers_from_zip(self, zip_bytes: bytes) -> List[Dict]:
        offers = []
        try:
            with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
                for name in zf.namelist():
                    if not name.lower().endswith(".json"):
                        continue
                    with zf.open(name) as f:
                        data = json.load(f)
                        if isinstance(data, list):
                            offers.extend(data)
                        elif isinstance(data, dict):
                            # Some exports wrap the list under a key
                            for key in ("oferty", "offers", "items", "dane"):
                                if key in data and isinstance(data[key], list):
                                    offers.extend(data[key])
                                    break
                            else:
                                offers.append(data)
        except Exception as e:
            logger.error(f"✗ Failed to unzip/parse CBOP payload: {e}")
        return offers

    def _parse_offer(self, offer: Dict) -> Optional[Dict]:
        """Normalize one raw CBOP offer record into our common job schema"""
        if not offer:
            return None

        logger.debug(f"CBOP raw offer keys (verify mapping): {list(offer.keys())}")

        def g(*keys, default=None):
            for k in keys:
                if k in offer and offer[k] not in (None, ""):
                    return offer[k]
            return default

        try:
            return {
                "title": g("nazwaStanowiska", "stanowisko", "nazwa_stanowiska", "title", default="Untitled"),
                "company": g("nazwaPracodawcy", "pracodawca", "nazwa_pracodawcy", "employer", default="N/A"),
                "location": g("miejsceWykonywaniaPracy", "miejscowosc", "miejsce_pracy", "location", default="Trojmiasto"),
                "salary_min": g("wynagrodzenieOd", "wynagrodzenie_od", "salary_min"),
                "salary_max": g("wynagrodzenieDo", "wynagrodzenie_do", "salary_max"),
                "currency": g("waluta", "currency", default="PLN"),
                "contract_type": g("rodzajZatrudnienia", "rodzaj_zatrudnienia", "contract_type", default="full-time"),
                "work_location": g("systemPracy", "system_pracy", "work_location", default="on-site"),
                "required_skills": g("wymagania", "required_skills", default=""),
                "requirements": g("wymagania", "requirements", default=""),
                "benefits": g("benefity", "benefits", default="[]"),
                "description": g("opisStanowiska", "opis", "description", default=""),
                "url": g("url", "link", default=self.url),
                "published_date": g("dataDodania", "data_dodania", "published_date",
                                     default=datetime.utcnow().isoformat()),
            }
        except Exception as e:
            logger.warning(f"Skipping unparseable CBOP offer: {e}")
            return None


# ========== PLACEHOLDER SOURCES (not yet implemented - no fake data) ==========

class _NotYetImplementedSource(JobSource):
    """
    Common behavior for target sources listed in ARCHITECTURE.md that
    don't have a real integration yet. Returns an empty list and logs
    why, instead of ever returning invented listings.
    """

    async def fetch_jobs(self, criteria: Dict = None) -> List[Dict]:
        logger.info(
            f"i {self.name}: real integration not implemented yet - "
            f"returning 0 jobs (no mock data)."
        )
        return []


class PracujPlSource(JobSource):
    """
    pracuj.pl - no official public API for third parties. This fetches
    the public search-results page (plain HTTP, no login/paywall
    bypass) and uses an LLM (via llm_service.py) to parse the visible
    text into structured job listings instead of hand-written
    HTML selectors.

    IMPORTANT: this is functionally scraping - using an LLM to parse
    the page instead of regex/BeautifulSoup selectors does not change
    its legal/ToS status. This was an explicit, informed decision by
    the product owner for the MVP-validation stage only (2026-09-17);
    revisit before any real launch or scale-up (see ARCHITECTURE.md's
    "only legal/permitted sources" constraint).
    """

    def __init__(self):
        super().__init__(name="pracuj.pl", url="https://www.pracuj.pl", source_type="website")

    async def fetch_jobs(self, criteria: Dict = None) -> List[Dict]:
        criteria = criteria or {}
        search_url = self._build_search_url(criteria)

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    search_url,
                    headers={
                        "User-Agent": (
                            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                            "AppleWebKit/537.36 (KHTML, like Gecko) "
                            "Chrome/120.0 Safari/537.36"
                        )
                    },
                    timeout=aiohttp.ClientTimeout(total=20),
                ) as resp:
                    if resp.status != 200:
                        logger.warning(f"⚠ pracuj.pl returned HTTP {resp.status} for {search_url}")
                        return []
                    html = await resp.text()
        except Exception as e:
            logger.error(f"✗ Error fetching pracuj.pl: {e}")
            return []

        page_text = self._html_to_text(html)
        if not page_text.strip():
            logger.warning("⚠ pracuj.pl page had no extractable text")
            return []

        try:
            from llm_service import get_llm_service
            llm = get_llm_service()
            raw_listings = await llm.extract_job_listings(page_text, "pracuj.pl")
        except Exception as e:
            logger.error(f"✗ LLM extraction failed for pracuj.pl: {e}")
            return []

        jobs = [self._normalize(item) for item in raw_listings]
        jobs = [j for j in jobs if j]
        logger.info(f"✓ Fetched {len(jobs)} jobs from pracuj.pl (LLM-parsed)")
        return jobs

    def _build_search_url(self, criteria: Dict) -> str:
        job_title = (criteria.get("job_title") or "").strip()
        geography = (criteria.get("geography") or "trojmiasto").lower()
        # pracuj.pl doesn't have a single "trojmiasto" location slug -
        # default to Gdansk, the largest of the three cities
        city = "gdansk" if geography in ("trojmiasto", "") else geography

        if job_title:
            return f"https://www.pracuj.pl/praca/{quote(job_title)};kw/{quote(city)};wp"
        return f"https://www.pracuj.pl/praca/{quote(city)};wp"

    def _html_to_text(self, html: str) -> str:
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html, "html.parser")
            for tag in soup(["script", "style", "nav", "footer"]):
                tag.decompose()
            return soup.get_text(separator="\n", strip=True)
        except ImportError:
            # bs4 not installed - crude fallback so this never hard-crashes
            text = re.sub(r"<script[\s\S]*?</script>", " ", html, flags=re.IGNORECASE)
            text = re.sub(r"<style[\s\S]*?</style>", " ", text, flags=re.IGNORECASE)
            text = re.sub(r"<[^>]+>", " ", text)
            return re.sub(r"\s+", " ", text).strip()

    def _normalize(self, item: Dict) -> Optional[Dict]:
        if not isinstance(item, dict) or not item.get("title"):
            return None
        return {
            "title": item.get("title"),
            "company": item.get("company") or "N/A",
            "location": item.get("location") or "Trojmiasto",
            "salary_min": item.get("salary_min"),
            "salary_max": item.get("salary_max"),
            "currency": item.get("currency") or "PLN",
            "contract_type": item.get("contract_type") or "full-time",
            "work_location": item.get("work_location") or "on-site",
            "required_skills": item.get("required_skills") or "",
            "requirements": item.get("required_skills") or "",
            "benefits": "[]",
            "description": "",
            "url": item.get("url") or self.url,
            "published_date": item.get("published_date") or datetime.utcnow().isoformat(),
        }


class OLXSource(_NotYetImplementedSource):
    """OLX Praca - no official job-search API found."""

    def __init__(self):
        super().__init__(name="OLX", url="https://www.olx.pl", source_type="website")


class LinkedInSource(_NotYetImplementedSource):
    """LinkedIn - scraping violates ToS; would require the official
    (paid, partner-gated) Talent/Jobs API."""

    def __init__(self):
        super().__init__(name="LinkedIn", url="https://www.linkedin.com", source_type="api")


class IndeedSource(_NotYetImplementedSource):
    """Indeed - Indeed's public XML feed is for employers publishing their
    own postings, not for third parties consuming aggregated listings."""

    def __init__(self):
        super().__init__(name="Indeed", url="https://www.indeed.com", source_type="website")


class TelegramSource(_NotYetImplementedSource):
    """Public Telegram job-posting channels - legal to read, but needs
    either the bot added to each channel or a user-account (MTProto)
    client; not wired up yet."""

    def __init__(self):
        super().__init__(name="Telegram Channels", url="https://telegram.org", source_type="telegram")


class JobSourceManager:
    """Manager for multiple job sources"""

    def __init__(self):
        """Initialize all sources"""
        self.sources = {
            "cbop": CBOPSource(),
            "pracuj": PracujPlSource(),
            "olx": OLXSource(),
            "linkedin": LinkedInSource(),
            "indeed": IndeedSource(),
            "telegram": TelegramSource(),
        }

    async def fetch_all_jobs(self, criteria: Dict = None) -> List[Dict]:
        """
        Fetch jobs from all sources concurrently

        Args:
            criteria: Search criteria (optional filtering)

        Returns:
            Combined list of jobs from all sources (real data only)
        """
        results = await asyncio.gather(
            *(self._fetch_and_tag(key, source, criteria) for key, source in self.sources.items()),
            return_exceptions=True,
        )

        all_jobs: List[Dict] = []
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"✗ Source fetch raised: {result}")
                continue
            all_jobs.extend(result)

        logger.info(f"Total jobs collected: {len(all_jobs)}")
        return all_jobs

    async def _fetch_and_tag(self, source_key: str, source: JobSource, criteria: Dict = None) -> List[Dict]:
        try:
            jobs = await source.fetch_jobs(criteria)
            for job in jobs:
                job["source"] = source.name
                job["source_key"] = source_key
            return jobs
        except Exception as e:
            logger.error(f"✗ Error fetching from {source.name}: {str(e)}")
            return []

    async def fetch_from_source(self, source_key: str, criteria: Dict = None) -> List[Dict]:
        """
        Fetch jobs from specific source

        Args:
            source_key: Source identifier (e.g., "cbop", "pracuj")
            criteria: Search criteria (optional)

        Returns:
            Jobs from that source
        """
        if source_key not in self.sources:
            logger.error(f"Unknown source: {source_key}")
            return []

        return await self._fetch_and_tag(source_key, self.sources[source_key], criteria)

    def get_available_sources(self) -> List[Dict]:
        """Get list of available sources"""
        return [
            {
                "key": key,
                "name": source.name,
                "url": source.url,
                "type": source.source_type,
                "implemented": isinstance(source, (CBOPSource, PracujPlSource)),
            }
            for key, source in self.sources.items()
        ]


# ========== USAGE EXAMPLE ==========
"""
import asyncio
from sources import JobSourceManager

async def main():
    manager = JobSourceManager()

    # Fetch from all sources (only CBOP will return real data until
    # CBOP_PARTNER_CODE is set and the other adapters are implemented)
    all_jobs = await manager.fetch_all_jobs()

    # Fetch from the government source specifically
    cbop_jobs = await manager.fetch_from_source("cbop")

    sources = manager.get_available_sources()
    print(sources)

asyncio.run(main())
"""
