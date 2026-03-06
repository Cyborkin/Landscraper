"""Legistar OData API scraper for Denver and Colorado Springs planning matters.

Queries the Legistar Web API for recent legislation and ordinances
related to zoning, development, and land use. These are leading
indicators of upcoming construction activity.
"""

import logging
from typing import Any

import httpx

from .base import BaseScraper

logger = logging.getLogger(__name__)

LEGISTAR_CLIENTS = {
    "denver": {
        "body_ids": [233, 237],
        "city": "Denver",
        "county": "Denver",
    },
    "coloradosprings": {
        "body_ids": [185],
        "city": "Colorado Springs",
        "county": "El Paso",
    },
}

KEYWORDS = [
    "zoning", "rezone", "rezoning", "development", "subdivision",
    "annex", "annexation", "land use", "building", "construction",
    "permit", "housing", "residential", "commercial", "mixed-use",
    "planned unit", "PUD", "site plan",
]


class LegistarScraper(BaseScraper):
    source_type = "api"

    def __init__(self):
        self.source_name = "legistar_planning"
        self.base_url = "https://webapi.legistar.com/v1"

    def _matches_keywords(self, text: str) -> bool:
        """Check if text contains any development-related keywords."""
        if not text:
            return False
        lower = text.lower()
        return any(kw in lower for kw in KEYWORDS)

    async def scrape(self) -> list[dict[str, Any]]:
        records = []
        async with httpx.AsyncClient(timeout=30.0) as client:
            for client_name, config in LEGISTAR_CLIENTS.items():
                try:
                    url = f"{self.base_url}/{client_name}/Matters"
                    response = await client.get(url, params={
                        "$top": "100",
                        "$orderby": "MatterIntroDate desc",
                    })
                    response.raise_for_status()
                    matters = response.json()

                    for matter in matters:
                        title = matter.get("MatterTitle") or matter.get("MatterName") or ""
                        if not self._matches_keywords(title):
                            continue

                        matter_file = matter.get("MatterFile", "")
                        raw = {
                            "permit_number": matter_file,
                            "permit_type": matter.get("MatterTypeName", "Legislation"),
                            "permit_status": matter.get("MatterStatusName"),
                            "description": title,
                            "city": config["city"],
                            "county": config["county"],
                            "state": "CO",
                            "filing_date": matter.get("MatterIntroDate"),
                        }
                        unique_key = f"legistar_{client_name}_{matter.get('MatterId', matter_file)}"
                        records.append(self.make_record(raw, unique_key))

                except Exception as e:
                    logger.warning("Legistar scrape failed for %s: %s", client_name, e)

        return records
