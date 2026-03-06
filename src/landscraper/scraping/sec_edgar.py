"""SEC EDGAR scraper for publicly traded homebuilder filings.

Queries the EDGAR full-text search API for Colorado-related filings.
Low complexity — public REST API.
"""

from typing import Any

import httpx

from .base import BaseScraper

EDGAR_SEARCH_URL = "https://efts.sec.gov/LATEST/search-index"
EDGAR_FULLTEXT_URL = "https://efts.sec.gov/LATEST/search-index"

# Major publicly traded homebuilders active in Colorado
HOMEBUILDERS = {
    "0000920760": "Lennar Corporation",
    "0000045012": "D.R. Horton",
    "0000795266": "KB Home",
    "0001514991": "Taylor Morrison",
    "0001502554": "Meritage Homes",
    "0000799292": "MDC Holdings (Richmond American)",
}

# EDGAR full-text search API
EDGAR_API = "https://efts.sec.gov/LATEST/search-index"


class SECEdgarScraper(BaseScraper):
    source_name = "sec_edgar"
    source_type = "api"

    def __init__(self, query: str = '"Colorado" AND ("new homes" OR "residential" OR "permits")'):
        self.query = query

    async def scrape(self) -> list[dict[str, Any]]:
        """Search EDGAR for Colorado-related homebuilder filings."""
        url = "https://efts.sec.gov/LATEST/search-index"
        params = {
            "q": self.query,
            "dateRange": "custom",
            "startdt": "2025-01-01",
            "enddt": "2026-12-31",
            "forms": "10-K,10-Q,8-K",
        }
        headers = {"User-Agent": "Landscraper/0.1 (research@landscraper.io)"}

        records = []
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url, params=params, headers=headers)
            if response.status_code != 200:
                return records

            data = response.json()
            hits = data.get("hits", {}).get("hits", [])

            for hit in hits[:50]:  # Limit to 50 results
                source_data = hit.get("_source", {})
                raw = {
                    "company_name": source_data.get("display_names", [""])[0],
                    "cik": source_data.get("entity_id"),
                    "form_type": source_data.get("form_type"),
                    "filing_date": source_data.get("file_date"),
                    "description": source_data.get("display_date_filed"),
                    "filing_url": f"https://www.sec.gov/Archives/edgar/data/{source_data.get('entity_id', '')}/{source_data.get('file_num', '')}",
                }

                unique_key = f"sec_{raw['cik']}_{raw['form_type']}_{raw['filing_date']}"
                records.append(self.make_record(raw, unique_key))

        return records
