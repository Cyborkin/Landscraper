"""SEC EDGAR scraper for publicly traded homebuilder filings.

Queries the EDGAR company submissions API for 10-K/10-Q filings
from major homebuilders active in Colorado.
Low complexity — public REST API.
"""

from typing import Any

import httpx

from .base import BaseScraper

# EDGAR company submissions API (no auth required, just User-Agent)
EDGAR_SUBMISSIONS_URL = "https://data.sec.gov/submissions/CIK{cik}.json"

# Major publicly traded homebuilders active in Colorado
HOMEBUILDERS = {
    "0000920760": "Lennar Corporation",
    "0000882184": "D.R. Horton",
    "0000795266": "KB Home",
    "0001514991": "Taylor Morrison",
    "0001502554": "Meritage Homes",
    "0000799292": "MDC Holdings (Richmond American)",
}

# Filing types we care about
TARGET_FORMS = {"10-K", "10-Q", "8-K"}


class SECEdgarScraper(BaseScraper):
    source_name = "sec_edgar"
    source_type = "api"

    def __init__(self, max_filings_per_company: int = 5):
        self.max_filings = max_filings_per_company

    async def scrape(self) -> list[dict[str, Any]]:
        """Fetch recent filings from EDGAR for each homebuilder."""
        headers = {
            "User-Agent": "Landscraper/0.1 (research@landscraper.io)",
            "Accept": "application/json",
        }
        records = []

        async with httpx.AsyncClient(timeout=30.0, headers=headers) as client:
            for cik, company_name in HOMEBUILDERS.items():
                try:
                    url = EDGAR_SUBMISSIONS_URL.format(cik=cik)
                    response = await client.get(url)
                    if response.status_code != 200:
                        continue

                    data = response.json()
                    filings = data.get("filings", {}).get("recent", {})
                    forms = filings.get("form", [])
                    dates = filings.get("filingDate", [])
                    accessions = filings.get("accessionNumber", [])
                    descriptions = filings.get("primaryDocDescription", [])
                    primary_docs = filings.get("primaryDocument", [])

                    count = 0
                    for i in range(len(forms)):
                        if forms[i] not in TARGET_FORMS:
                            continue
                        if count >= self.max_filings:
                            break

                        accession_no_dash = accessions[i].replace("-", "")
                        filing_url = (
                            f"https://www.sec.gov/Archives/edgar/data/"
                            f"{cik.lstrip('0')}/{accession_no_dash}/"
                            f"{primary_docs[i] if i < len(primary_docs) else ''}"
                        )

                        raw = {
                            "company_name": company_name,
                            "cik": cik,
                            "form_type": forms[i],
                            "filing_date": dates[i] if i < len(dates) else None,
                            "description": (
                                descriptions[i] if i < len(descriptions) else forms[i]
                            ),
                            "filing_url": filing_url,
                        }

                        unique_key = f"sec_{cik}_{forms[i]}_{dates[i]}"
                        records.append(self.make_record(raw, unique_key))
                        count += 1

                except Exception:
                    continue  # Skip failed companies, continue with others

        return records
