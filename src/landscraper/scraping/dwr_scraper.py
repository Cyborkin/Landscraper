"""Colorado DWR well permits scraper.

Queries the Division of Water Resources REST API for residential
well permits in Front Range counties. Well permits for domestic use
are a leading indicator for rural/exurban residential development.
"""

import logging
from datetime import UTC, datetime
from typing import Any

import httpx

from .base import BaseScraper

logger = logging.getLogger(__name__)

# Front Range counties where well permits signal development
DWR_COUNTIES = [
    "ADAMS", "ARAPAHOE", "BOULDER", "BROOMFIELD", "DENVER",
    "DOUGLAS", "ELPASO", "JEFFERSON", "LARIMER", "WELD",
]

# Map DWR county names to standard names
COUNTY_MAP = {
    "ADAMS": "Adams",
    "ARAPAHOE": "Arapahoe",
    "BOULDER": "Boulder",
    "BROOMFIELD": "Broomfield",
    "DENVER": "Denver",
    "DOUGLAS": "Douglas",
    "ELPASO": "El Paso",
    "JEFFERSON": "Jefferson",
    "LARIMER": "Larimer",
    "WELD": "Weld",
}


class DWRScraper(BaseScraper):
    """Scrapes Colorado Division of Water Resources well permit data."""

    source_name = "dwr_well_permits"
    source_type = "api"

    def __init__(self) -> None:
        self.base_url = (
            "https://dwr.state.co.us/Rest/GET/api/v2/wellpermits/wellpermit/"
        )

    async def scrape(self) -> list[dict[str, Any]]:
        """Fetch residential/domestic well permits for Front Range counties."""
        # Get permits modified in the last 6 months
        now = datetime.now(tz=UTC)
        if now.month > 6:
            six_months_ago = now.replace(month=now.month - 6)
        else:
            six_months_ago = now.replace(
                year=now.year - 1, month=now.month + 6
            )
        modified_date = six_months_ago.strftime("%m/%d/%Y")

        records: list[dict[str, Any]] = []
        async with httpx.AsyncClient(timeout=30.0) as client:
            for county in DWR_COUNTIES:
                try:
                    response = await client.get(
                        self.base_url,
                        params={
                            "format": "json",
                            "county": county,
                            "modified": modified_date,
                            "pageSize": 100,
                        },
                    )
                    response.raise_for_status()
                    data = response.json()

                    for well in data.get("ResultList", []):
                        uses = (well.get("associatedUses") or "").lower()
                        category = (
                            well.get("permitCategoryDescr") or ""
                        ).lower()
                        # Only include residential/domestic well permits
                        if (
                            "domestic" not in uses
                            and "residential" not in category
                        ):
                            continue

                        raw = {
                            "permit_number": well.get("permit", ""),
                            "permit_type": "Well Permit",
                            "permit_status": well.get(
                                "permitCurrentStatusDescr"
                            ),
                            "description": (
                                f"Well permit ({well.get('associatedUses', '')})"
                                f" - {well.get('permitCategoryDescr', '')}"
                            ),
                            "address_street": well.get("physicalAddress"),
                            "city": well.get("physicalCity"),
                            "county": COUNTY_MAP.get(county, county),
                            "state": "CO",
                            "latitude": well.get("latitude"),
                            "longitude": well.get("longitude"),
                            "filing_date": (
                                well.get("datePermitIssued")
                                or well.get("dateApplicationReceived")
                            ),
                            "owner_name": well.get("contactName"),
                        }
                        unique_key = f"dwr_{well.get('permit', '')}"
                        records.append(self.make_record(raw, unique_key))

                except Exception as e:
                    logger.warning(
                        "DWR scrape failed for %s: %s", county, e
                    )

        return records
