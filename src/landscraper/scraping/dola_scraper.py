"""DOLA State Demography Office scraper.

Fetches county-level building permits and demographics from
the Colorado DOLA REST API. No authentication required.
"""

from typing import Any

import httpx

from .base import BaseScraper

DOLA_URL = "https://gis.dola.colorado.gov/lookups/profile"

# Front Range county FIPS codes (without state prefix)
FRONT_RANGE_COUNTIES = {
    1: "Adams",
    5: "Arapahoe",
    13: "Boulder",
    14: "Broomfield",
    31: "Denver",
    35: "Douglas",
    41: "El Paso",
    59: "Jefferson",
    69: "Larimer",
    123: "Weld",
}


class DOLAScraper(BaseScraper):
    source_name = "dola_demography"
    source_type = "api"

    def __init__(self, year: int = 2024):
        self.year = year

    async def scrape(self) -> list[dict[str, Any]]:
        records = []
        async with httpx.AsyncClient(timeout=30.0) as client:
            for fips, county_name in FRONT_RANGE_COUNTIES.items():
                try:
                    resp = await client.get(
                        DOLA_URL, params={"county": fips, "year": self.year}
                    )
                    resp.raise_for_status()
                    data = resp.json()
                except (httpx.HTTPError, Exception):
                    continue

                if not data:
                    continue

                # API returns a list; take the first (and usually only) entry
                row = data[0] if isinstance(data, list) else data

                raw = {
                    "county": county_name,
                    "county_fips": f"08{fips:03d}",
                    "year": self.year,
                    "permit_count": _safe_int(row.get("censusbuildingpermits")),
                    "total_population": _safe_int(row.get("totalpopulation")),
                    "total_housing_units": _safe_int(row.get("totalhousingunits")),
                    "vacant_housing_units": _safe_int(row.get("vacanthousingunits")),
                    "vacancy_rate": _safe_float(row.get("vacancyrate")),
                    "households": _safe_int(row.get("households")),
                    "net_migration": _safe_int(row.get("netmigration")),
                }

                unique_key = f"dola_{self.year}_{fips}"
                records.append(self.make_record(raw, unique_key))

        return records


def _safe_int(val: Any) -> int | None:
    if val is None:
        return None
    try:
        return int(val)
    except (ValueError, TypeError):
        return None


def _safe_float(val: Any) -> float | None:
    if val is None:
        return None
    try:
        return float(val)
    except (ValueError, TypeError):
        return None
