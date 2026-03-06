"""Node functions for each phase of the Landscraper agent graph.

Each node receives the current state and returns a partial state update.
Stub implementations — will be filled in during subsequent phases.
"""

import logging
import uuid
from datetime import datetime, timezone
from typing import Any

from .state import CollectionTaskState, LandscraperState

logger = logging.getLogger(__name__)


def _build_scraper(source: dict[str, Any]):
    """Instantiate the right scraper based on source config."""
    from landscraper.scraping import (
        CensusBPSScraper,
        HttpxScraper,
        RSSFeedScraper,
        SECEdgarScraper,
        SodaScraper,
    )

    access_method = source.get("access_method", "")
    source_name = source.get("name", "unknown")

    if source_name == "census_bps":
        return CensusBPSScraper()
    elif source_name == "colorado_soda_permits":
        return SodaScraper()
    elif source_name == "sec_edgar":
        return SECEdgarScraper()
    elif access_method == "rss":
        return RSSFeedScraper(
            source_name=source_name,
            feed_url=source.get("url", ""),
            keywords=source.get("keywords"),
        )
    elif access_method in ("httpx", "html"):
        return HttpxScraper(
            source_name=source_name,
            url=source.get("url", ""),
            method=source.get("method", "GET"),
            params=source.get("params"),
            headers=source.get("headers"),
            extract_fn=source.get("extract_fn"),
        )
    else:
        return None


async def source_discovery_node(state: LandscraperState) -> dict[str, Any]:
    """Phase 1: Discover and validate data sources.

    Queries the data_sources table for active sources, evaluates their
    current status, and returns the list of sources to scrape this cycle.
    """
    # TODO Phase 4+: Implement OSINT source discovery with LLM evaluation
    # For now, return whatever active_sources are already in state
    return {
        "current_phase": "collection",
        "messages": [],
        "errors": [],
    }


async def collection_specialist_node(state: CollectionTaskState) -> dict[str, Any]:
    """Scrape a single data source.

    Called via Send() — receives a single source config, not the full state.
    Returns raw scraped data to be merged into the main state.
    """
    source = state["source"]
    source_name = source.get("name", "unknown")

    scraper = _build_scraper(source)
    if scraper is None:
        return {
            "raw_data": [],
            "errors": [f"No scraper available for source: {source_name}"],
            "messages": [],
        }

    try:
        records = await scraper.scrape()
        logger.info("Collected %d records from %s", len(records), source_name)
        return {
            "raw_data": records,
            "errors": [],
            "messages": [f"Collected {len(records)} records from {source_name}"],
        }
    except Exception as e:
        logger.error("Scrape failed for %s: %s", source_name, e)
        return {
            "raw_data": [],
            "errors": [f"Scrape failed for {source_name}: {e}"],
            "messages": [],
        }


async def pipeline_node(state: LandscraperState) -> dict[str, Any]:
    """Phase 3: Correlate, aggregate, deduplicate, enrich, and score.

    Takes raw_data from collection and produces normalized developments/builders.
    """
    # TODO Phase 4: Implement correlation, aggregation, dedup, enrichment, scoring
    return {
        "current_phase": "consensus",
        "developments": [],
        "builders": [],
        "messages": [],
        "errors": [],
    }


async def consensus_node(state: LandscraperState) -> dict[str, Any]:
    """Phase 4: Cross-validate findings and produce scored leads.

    Multiple agents independently evaluate developments before they become leads.
    Confidence scoring based on source count, reliability, and data freshness.
    """
    # TODO Phase 5: Implement multi-agent consensus voting
    return {
        "current_phase": "improvement",
        "validated_leads": [],
        "messages": [],
        "errors": [],
    }


async def self_improvement_node(state: LandscraperState) -> dict[str, Any]:
    """Phase 5: Evaluate cycle performance and adjust strategies.

    Tracks yield rate, false positive rate, source freshness, scrape success rate.
    Suggests strategy modifications for next cycle.
    """
    # TODO Phase 6: Implement metric tracking and strategy evaluation
    return {
        "current_phase": "delivery",
        "cycle_metrics": {},
        "messages": [],
        "errors": [],
    }


async def delivery_node(state: LandscraperState) -> dict[str, Any]:
    """Phase 6: Store leads and push to tenants via configured channels.

    Creates Lead records in the database and triggers notifications.
    """
    # TODO Phase 8: Implement notification delivery
    return {
        "current_phase": "complete",
        "messages": [],
        "errors": [],
    }
