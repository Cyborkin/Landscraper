"""Socrata Open Data (SODA) API scraper for data.colorado.gov.

Queries the Building Permit Counts dataset via REST API.
Low complexity — standard JSON API.
"""

from typing import Any

import httpx

from .base import BaseScraper

# Socrata dataset endpoint for Colorado Building Permit Counts
SODA_ENDPOINT = "https://data.colorado.gov/resource/v4as-sthd.json"

# Front Range counties to filter
FRONT_RANGE_COUNTIES = {
    "Adams", "Arapahoe", "Boulder", "Broomfield", "Denver",
    "Douglas", "El Paso", "Jefferson", "Larimer", "Weld",
}


class SodaScraper(BaseScraper):
    source_name = "colorado_soda_permits"
    source_type = "api"

    def __init__(self, limit: int = 1000):
        self.limit = limit

    async def scrape(self) -> list[dict[str, Any]]:
        params = {
            "$limit": self.limit,
            "$order": ":id",
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(SODA_ENDPOINT, params=params)
            response.raise_for_status()

        data = response.json()
        records = []

        for row in data:
            county = row.get("county", "")
            if county not in FRONT_RANGE_COUNTIES:
                continue

            raw = {
                "county": county,
                "year": row.get("year"),
                "month": row.get("month"),
                "permit_count": _safe_int(row.get("permits")),
                "units": _safe_int(row.get("units")),
                "valuation": _safe_int(row.get("valuation")),
            }

            unique_key = f"soda_{county}_{row.get('year')}_{row.get('month')}"
            records.append(self.make_record(raw, unique_key))

        return records


def _safe_int(val: Any) -> int | None:
    if val is None:
        return None
    try:
        return int(val)
    except (ValueError, TypeError):
        return None
