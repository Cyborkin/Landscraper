"""Socrata Open Data (SODA) API scraper for data.colorado.gov.

Queries the Building Permit Counts dataset via REST API.
Low complexity — standard JSON API.
"""

from typing import Any

import httpx

from .base import BaseScraper

# Socrata dataset endpoint for Colorado Building Permit Counts
SODA_ENDPOINT = "https://data.colorado.gov/resource/v4as-sthd.json"

# Front Range county FIPS codes (Colorado state FIPS = 08)
FRONT_RANGE_FIPS = {
    "001": "Adams",
    "005": "Arapahoe",
    "013": "Boulder",
    "014": "Broomfield",
    "031": "Denver",
    "035": "Douglas",
    "041": "El Paso",
    "059": "Jefferson",
    "069": "Larimer",
    "123": "Weld",
}


class SodaScraper(BaseScraper):
    source_name = "colorado_soda_permits"
    source_type = "api"

    def __init__(self, limit: int = 1000):
        self.limit = limit

    async def scrape(self) -> list[dict[str, Any]]:
        # Filter for Front Range counties and most recent year available
        fips_list = ",".join(f"'{f}'" for f in FRONT_RANGE_FIPS)
        params = {
            "$limit": self.limit,
            "$where": f"countyfips in ({fips_list})",
            "$order": "year DESC",
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(SODA_ENDPOINT, params=params)
            response.raise_for_status()

        data = response.json()
        records = []

        for row in data:
            county_fips = row.get("countyfips", "")
            county_name = FRONT_RANGE_FIPS.get(county_fips, county_fips)
            area = row.get("area", "")

            raw = {
                "county": county_name,
                "county_fips": f"08{county_fips}",
                "area": area,
                "year": row.get("year"),
                "permit_count": _safe_int(row.get("cbbuildingpermit")),
                "sdo_permit_count": _safe_int(row.get("sdobuildingpermit")),
                "total_population": _safe_int(row.get("totalpopulation")),
                "total_housing_units": _safe_int(row.get("totalhousingunits")),
            }

            unique_key = f"soda_{county_fips}_{area}_{row.get('year')}"
            records.append(self.make_record(raw, unique_key))

        return records


def _safe_int(val: Any) -> int | None:
    if val is None:
        return None
    try:
        return int(val)
    except (ValueError, TypeError):
        return None
