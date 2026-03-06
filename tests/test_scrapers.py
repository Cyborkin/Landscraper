"""Tests for collection specialist scrapers.

Uses respx to mock httpx calls so no real HTTP requests are made.
"""

import pytest
import respx
from httpx import Response

from landscraper.scraping import (
    CensusBPSScraper,
    HttpxScraper,
    RSSFeedScraper,
    SECEdgarScraper,
    SodaScraper,
)
from landscraper.scraping.base import BaseScraper


# --- BaseScraper ---


def test_hash_content_deterministic():
    h1 = BaseScraper.hash_content("test")
    h2 = BaseScraper.hash_content("test")
    assert h1 == h2
    assert len(h1) == 64  # SHA-256 hex


def test_hash_content_varies():
    assert BaseScraper.hash_content("a") != BaseScraper.hash_content("b")


# --- CensusBPSScraper ---

CENSUS_CSV = """\
08,001,3,8,Adams County,100,100,25000,5,10,1500,0,10,50,3000,0,115,160,29500
08,035,3,8,Douglas County,80,80,20000,3,6,900,0,5,25,1500,0,88,111,22400
08,999,3,8,Other County,10,10,2000,1,2,200,0,0,0,0,0,11,12,2200
"""


@respx.mock
@pytest.mark.asyncio
async def test_census_bps_scraper():
    respx.get("https://www2.census.gov/econ/bps/County/co2025a.txt").mock(
        return_value=Response(200, text=CENSUS_CSV)
    )

    scraper = CensusBPSScraper(year=2025)
    records = await scraper.scrape()

    # Should include Adams (001) and Douglas (035) but not Other (999)
    assert len(records) == 2
    counties = {r["raw_data"]["county"] for r in records}
    assert counties == {"Adams", "Douglas"}

    adams = next(r for r in records if r["raw_data"]["county"] == "Adams")
    assert adams["raw_data"]["single_family_buildings"] == 100
    assert adams["raw_data"]["total_units"] == 160
    assert adams["source_name"] == "census_bps"
    assert "content_hash" in adams


# --- SodaScraper ---

SODA_JSON = [
    {"county": "Adams", "year": "2025", "month": "01", "permits": "50", "units": "60", "valuation": "15000000"},
    {"county": "Adams", "year": "2025", "month": "02", "permits": "45", "units": "55", "valuation": "14000000"},
    {"county": "Pueblo", "year": "2025", "month": "01", "permits": "10", "units": "10", "valuation": "2000000"},
]


@respx.mock
@pytest.mark.asyncio
async def test_soda_scraper():
    respx.get("https://data.colorado.gov/resource/v4as-sthd.json").mock(
        return_value=Response(200, json=SODA_JSON)
    )

    scraper = SodaScraper(limit=100)
    records = await scraper.scrape()

    # Should include Adams (2 records) but not Pueblo
    assert len(records) == 2
    assert all(r["raw_data"]["county"] == "Adams" for r in records)
    assert records[0]["raw_data"]["permit_count"] == 50
    assert records[0]["source_name"] == "colorado_soda_permits"


# --- RSSFeedScraper ---

RSS_XML = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>Test Feed</title>
    <item>
      <title>New development permit approved</title>
      <link>https://example.com/article1</link>
      <description>A major residential development has been permitted.</description>
      <pubDate>Mon, 01 Jan 2025 00:00:00 GMT</pubDate>
    </item>
    <item>
      <title>City council meeting notes</title>
      <link>https://example.com/article2</link>
      <description>Discussion about traffic patterns.</description>
      <pubDate>Tue, 02 Jan 2025 00:00:00 GMT</pubDate>
    </item>
  </channel>
</rss>"""


@respx.mock
@pytest.mark.asyncio
async def test_rss_scraper_no_filter():
    respx.get("https://example.com/feed.xml").mock(
        return_value=Response(200, text=RSS_XML)
    )

    scraper = RSSFeedScraper(source_name="test_feed", feed_url="https://example.com/feed.xml")
    records = await scraper.scrape()

    assert len(records) == 2
    assert records[0]["raw_data"]["title"] == "New development permit approved"
    assert records[0]["source_name"] == "test_feed"


@respx.mock
@pytest.mark.asyncio
async def test_rss_scraper_with_keywords():
    respx.get("https://example.com/feed.xml").mock(
        return_value=Response(200, text=RSS_XML)
    )

    scraper = RSSFeedScraper(
        source_name="test_feed",
        feed_url="https://example.com/feed.xml",
        keywords=["development", "permit"],
    )
    records = await scraper.scrape()

    # Only the first article matches keywords
    assert len(records) == 1
    assert "development" in records[0]["raw_data"]["title"].lower()


# --- SECEdgarScraper ---

EDGAR_JSON = {
    "hits": {
        "hits": [
            {
                "_source": {
                    "display_names": ["Lennar Corporation"],
                    "entity_id": "0000920760",
                    "form_type": "10-K",
                    "file_date": "2025-02-15",
                    "display_date_filed": "2025-02-15",
                    "file_num": "001-11749",
                }
            },
            {
                "_source": {
                    "display_names": ["D.R. Horton"],
                    "entity_id": "0000045012",
                    "form_type": "10-Q",
                    "file_date": "2025-01-30",
                    "display_date_filed": "2025-01-30",
                    "file_num": "001-14122",
                }
            },
        ]
    }
}


@respx.mock
@pytest.mark.asyncio
async def test_sec_edgar_scraper():
    respx.get("https://efts.sec.gov/LATEST/search-index").mock(
        return_value=Response(200, json=EDGAR_JSON)
    )

    scraper = SECEdgarScraper()
    records = await scraper.scrape()

    assert len(records) == 2
    assert records[0]["raw_data"]["company_name"] == "Lennar Corporation"
    assert records[0]["raw_data"]["form_type"] == "10-K"
    assert records[0]["source_name"] == "sec_edgar"


@respx.mock
@pytest.mark.asyncio
async def test_sec_edgar_handles_non_200():
    respx.get("https://efts.sec.gov/LATEST/search-index").mock(
        return_value=Response(503)
    )

    scraper = SECEdgarScraper()
    records = await scraper.scrape()
    assert records == []


# --- HttpxScraper ---


@respx.mock
@pytest.mark.asyncio
async def test_httpx_scraper_get():
    respx.get("https://example.com/permits").mock(
        return_value=Response(200, text="<html><body>Permit data</body></html>")
    )

    scraper = HttpxScraper(source_name="test_portal", url="https://example.com/permits")
    records = await scraper.scrape()

    assert len(records) == 1
    assert "Permit data" in records[0]["raw_data"]["html"]
    assert records[0]["source_name"] == "test_portal"


@respx.mock
@pytest.mark.asyncio
async def test_httpx_scraper_with_extract_fn():
    respx.get("https://example.com/permits").mock(
        return_value=Response(200, text="PERMIT-001|residential\nPERMIT-002|commercial")
    )

    def extract(text):
        items = []
        for line in text.strip().split("\n"):
            num, ptype = line.split("|")
            items.append({"permit_number": num, "type": ptype})
        return items

    scraper = HttpxScraper(
        source_name="test_portal",
        url="https://example.com/permits",
        extract_fn=extract,
    )
    records = await scraper.scrape()

    assert len(records) == 2
    assert records[0]["raw_data"]["permit_number"] == "PERMIT-001"
    assert records[1]["raw_data"]["type"] == "commercial"


@respx.mock
@pytest.mark.asyncio
async def test_httpx_scraper_post():
    respx.post("https://example.com/search").mock(
        return_value=Response(200, text="<html>results</html>")
    )

    scraper = HttpxScraper(
        source_name="test_portal",
        url="https://example.com/search",
        method="POST",
        params={"query": "residential"},
    )
    records = await scraper.scrape()
    assert len(records) == 1


# --- collection_specialist_node wiring ---


@pytest.mark.asyncio
async def test_collection_node_unknown_source():
    from landscraper.agents.nodes import collection_specialist_node

    result = await collection_specialist_node({
        "source": {"name": "unknown_source", "access_method": "magic"},
        "cycle_id": "test-cycle",
    })

    assert result["raw_data"] == []
    assert any("No scraper" in e for e in result["errors"])


@respx.mock
@pytest.mark.asyncio
async def test_collection_node_dispatches_soda():
    respx.get("https://data.colorado.gov/resource/v4as-sthd.json").mock(
        return_value=Response(200, json=SODA_JSON)
    )

    from landscraper.agents.nodes import collection_specialist_node

    result = await collection_specialist_node({
        "source": {"name": "colorado_soda_permits", "access_method": "api"},
        "cycle_id": "test-cycle",
    })

    assert len(result["raw_data"]) == 2
    assert result["errors"] == []


@respx.mock
@pytest.mark.asyncio
async def test_collection_node_handles_scrape_error():
    respx.get("https://data.colorado.gov/resource/v4as-sthd.json").mock(
        return_value=Response(500)
    )

    from landscraper.agents.nodes import collection_specialist_node

    result = await collection_specialist_node({
        "source": {"name": "colorado_soda_permits", "access_method": "api"},
        "cycle_id": "test-cycle",
    })

    assert result["raw_data"] == []
    assert any("Scrape failed" in e for e in result["errors"])
