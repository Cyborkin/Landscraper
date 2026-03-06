"""Census Bureau Building Permits Survey scraper.

Downloads annual CSV data from census.gov for Colorado counties.
Low complexity — static file download and parse.
"""

import csv
import io
from typing import Any

import httpx

from .base import BaseScraper

# Census BPS annual data URL pattern
BPS_URL = "https://www2.census.gov/econ/bps/County/co{year}a.txt"

# Front Range county FIPS codes (state FIPS 08 = Colorado)
FRONT_RANGE_COUNTIES = {
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


class CensusBPSScraper(BaseScraper):
    source_name = "census_bps"
    source_type = "api"

    def __init__(self, year: int | None = None):
        self.year = year

    async def scrape(self) -> list[dict[str, Any]]:
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Try current year down to 2020 until we find published data
            years_to_try = [self.year] if self.year else list(range(2025, 2019, -1))
            response = None
            for yr in years_to_try:
                url = BPS_URL.format(year=yr)
                resp = await client.get(url)
                if resp.status_code == 200:
                    response = resp
                    self.year = yr
                    break
            if response is None:
                return []

        records = []
        reader = csv.reader(io.StringIO(response.text))

        for row in reader:
            if len(row) < 9:
                continue

            # Current format: year, state_fips, county_fips, region, division, name,
            # 1-unit_bldgs, 1-unit_units, 1-unit_value, 2-unit_bldgs, ...
            # Skip header rows and blank lines
            state_fips = row[1].strip()
            county_fips = row[2].strip()

            if state_fips != "08":  # Colorado
                continue
            if county_fips not in FRONT_RANGE_COUNTIES:
                continue

            county_name = FRONT_RANGE_COUNTIES[county_fips]
            raw = {
                "county": county_name,
                "county_fips": f"08{county_fips}",
                "year": _safe_int(row[0].strip()),
                "name": row[5].strip() if len(row) > 5 else county_name,
                "single_family_buildings": _safe_int(row[6]) if len(row) > 6 else None,
                "single_family_units": _safe_int(row[7]) if len(row) > 7 else None,
                "single_family_value_thousands": _safe_int(row[8]) if len(row) > 8 else None,
                "two_family_buildings": _safe_int(row[9]) if len(row) > 9 else None,
                "multi_family_buildings": _safe_int(row[15]) if len(row) > 15 else None,
                "multi_family_units": _safe_int(row[16]) if len(row) > 16 else None,
                "total_units": _safe_int(row[7]) if len(row) > 7 else None,  # Approximate with SF units
            }

            unique_key = f"census_bps_{self.year}_{county_fips}"
            records.append(self.make_record(raw, unique_key))

        return records


def _safe_int(val: str) -> int | None:
    try:
        return int(val.strip().replace(",", ""))
    except (ValueError, AttributeError):
        return None
