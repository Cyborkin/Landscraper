"""Generic httpx-based scraper for static HTML permit portals.

Used for moderate-complexity portals like PPRBD, Douglas County, Weld County.
Parses HTML responses with basic extraction patterns.
"""

import re
from typing import Any

import httpx

from .base import BaseScraper


class HttpxScraper(BaseScraper):
    """Configurable httpx scraper for static/semi-static HTML sources."""

    source_type = "permit_portal"

    def __init__(
        self,
        source_name: str,
        url: str,
        method: str = "GET",
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        extract_fn: Any = None,
    ):
        self.source_name = source_name
        self.url = url
        self.method = method
        self.params = params or {}
        self.headers = headers or {}
        self.extract_fn = extract_fn

    async def scrape(self) -> list[dict[str, Any]]:
        async with httpx.AsyncClient(
            timeout=30.0,
            follow_redirects=True,
            headers={"User-Agent": "Mozilla/5.0 (compatible; Landscraper/0.1)"},
        ) as client:
            if self.method == "POST":
                response = await client.post(
                    self.url, data=self.params, headers=self.headers
                )
            else:
                response = await client.get(
                    self.url, params=self.params, headers=self.headers
                )
            response.raise_for_status()

        if self.extract_fn:
            raw_items = self.extract_fn(response.text)
        else:
            raw_items = [{"html": response.text[:10000], "url": self.url}]

        records = []
        for item in raw_items:
            unique_key = item.get("permit_number", item.get("url", self.url))
            records.append(self.make_record(item, unique_key))

        return records
