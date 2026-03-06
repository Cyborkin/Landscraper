"""RSS/Atom feed scraper for planning agendas and news sources.

Handles Legistar iCal feeds, BizWest RSS, and other feed-based sources.
Low complexity — standard feed parsing.
"""

from typing import Any

import feedparser
import httpx

from .base import BaseScraper


class RSSFeedScraper(BaseScraper):
    source_type = "rss"

    def __init__(self, source_name: str, feed_url: str, keywords: list[str] | None = None):
        self.source_name = source_name
        self.feed_url = feed_url
        self.keywords = [k.lower() for k in keywords] if keywords else None

    async def scrape(self) -> list[dict[str, Any]]:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(self.feed_url)
            response.raise_for_status()

        feed = feedparser.parse(response.text)
        records = []

        for entry in feed.entries:
            title = getattr(entry, "title", "")
            summary = getattr(entry, "summary", "")
            link = getattr(entry, "link", "")
            published = getattr(entry, "published", "")

            # Keyword filtering if configured
            if self.keywords:
                text = f"{title} {summary}".lower()
                if not any(kw in text for kw in self.keywords):
                    continue

            raw = {
                "title": title,
                "summary": summary,
                "link": link,
                "published": published,
                "source_feed": self.feed_url,
            }

            unique_key = link or f"{self.source_name}_{title}"
            records.append(self.make_record(raw, unique_key))

        return records


# Pre-configured scrapers for known sources
def bizwest_scraper() -> RSSFeedScraper:
    return RSSFeedScraper(
        source_name="bizwest_real_estate",
        feed_url="https://bizwest.com/category/real-estate-construction/feed/",
        keywords=["development", "construction", "permit", "housing", "residential", "builder"],
    )


def denver_planning_scraper() -> RSSFeedScraper:
    return RSSFeedScraper(
        source_name="denver_planning",
        feed_url="https://denver.legistar.com/Feed.ashx?M=Calendar&ID=24361589&GUID=8ef864d3-dba5-4126-9e5f-94efb64fd926&Mode=2024-2027",
        keywords=["planning", "zoning", "development", "land use", "rezoning"],
    )
