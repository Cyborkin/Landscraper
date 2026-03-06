"""Base scraper interface — all collection specialists implement this."""

import hashlib
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any


class BaseScraper(ABC):
    """Abstract base class for all scrapers."""

    source_name: str
    source_type: str  # permit_portal, rss, api, news

    @abstractmethod
    async def scrape(self) -> list[dict[str, Any]]:
        """Execute the scrape and return raw data records.

        Each record is a dict with at minimum:
            - source_name: str
            - collected_at: datetime (UTC)
            - content_hash: str (SHA-256 of unique content)
            - raw_data: dict (the actual scraped content)
        """
        ...

    @staticmethod
    def hash_content(content: str) -> str:
        """Generate SHA-256 hash for deduplication."""
        return hashlib.sha256(content.encode()).hexdigest()

    @staticmethod
    def now_utc() -> datetime:
        return datetime.now(timezone.utc)

    def make_record(self, raw_data: dict[str, Any], unique_key: str) -> dict[str, Any]:
        """Create a standardized raw collection record."""
        return {
            "source_name": self.source_name,
            "collected_at": self.now_utc().isoformat(),
            "content_hash": self.hash_content(unique_key),
            "raw_data": raw_data,
        }
