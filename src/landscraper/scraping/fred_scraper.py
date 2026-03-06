"""FRED building permits time series scraper.

Downloads monthly building permit counts from FRED CSV endpoint.
No authentication required.
"""

import csv
import io
from datetime import datetime, timezone
from typing import Any

import httpx

from .base import BaseScraper

# FRED series for Colorado Front Range MSAs
FRED_SERIES = {
    "DENV708BPPRIV": {"area": "Denver-Aurora-Lakewood MSA", "county": "Denver", "metric": "total_permits"},
    "DENV708BP1FH": {"area": "Denver-Aurora-Lakewood MSA", "county": "Denver", "metric": "single_family_permits"},
    "COBPPRIV": {"area": "Colorado", "county": None, "metric": "total_permits"},
    "COLO808BPPRIV": {"area": "Colorado Springs MSA", "county": "El Paso", "metric": "total_permits"},
    "GREE508BPPRIV": {"area": "Greeley MSA", "county": "Weld", "metric": "total_permits"},
}


class FREDScraper(BaseScraper):
    source_type = "csv"

    def __init__(self):
        self.source_name = "fred_building_permits"
        self.base_url = "https://fred.stlouisfed.org/graph/fredgraph.csv"

    async def scrape(self) -> list[dict[str, Any]]:
        # Fetch last 12 months of data for all series
        series_ids = ",".join(FRED_SERIES.keys())
        now = datetime.now(tz=timezone.utc)
        # Get data from 13 months ago to capture full trailing year
        start_year = now.year - 1
        start_month = now.month
        cosd = f"{start_year}-{start_month:02d}-01"
        coed = f"{now.year}-{now.month:02d}-28"

        params = {"id": series_ids, "cosd": cosd, "coed": coed}

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(self.base_url, params=params)
            response.raise_for_status()

        records = []
        reader = csv.DictReader(io.StringIO(response.text))
        for row in reader:
            date_str = row.get("DATE", "")
            for series_id, meta in FRED_SERIES.items():
                value = row.get(series_id, "").strip()
                if not value or value == ".":
                    continue
                try:
                    permit_count = int(float(value))
                except (ValueError, TypeError):
                    continue

                raw = {
                    "permit_number": f"FRED-{series_id}-{date_str}",
                    "permit_type": f"FRED {meta['metric']}",
                    "description": f"{meta['area']}: {permit_count} {meta['metric'].replace('_', ' ')} for {date_str}",
                    "county": meta["county"],
                    "state": "CO",
                    "filing_date": date_str,
                    "unit_count": permit_count,
                    "permit_status": "reported",
                }
                unique_key = f"fred_{series_id}_{date_str}"
                records.append(self.make_record(raw, unique_key))

        return records
