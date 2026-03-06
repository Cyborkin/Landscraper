"""Node functions for each phase of the Landscraper agent graph.

Each node receives the current state and returns a partial state update.
LLM calls use the least expensive capable model per task (see llm.py).
"""

import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage

from .state import CollectionTaskState, LandscraperState

logger = logging.getLogger(__name__)


def _build_scraper(source: dict[str, Any]):
    """Instantiate the right scraper based on source config."""
    from landscraper.scraping import (
        ArcGISScraper,
        CensusBPSScraper,
        DOLAScraper,
        FREDScraper,
        HttpxScraper,
        RSSFeedScraper,
        SECEdgarScraper,
        SodaScraper,
    )
    from landscraper.scraping.arcgis_scraper import ARCGIS_SOURCES

    access_method = source.get("access_method", "")
    source_name = source.get("name", "unknown")

    if source_name == "census_bps":
        return CensusBPSScraper()
    elif source_name == "colorado_soda_permits":
        return SodaScraper()
    elif source_name == "sec_edgar":
        return SECEdgarScraper()
    elif source_name == "dola_demography":
        return DOLAScraper()
    elif source_name == "fred_building_permits":
        return FREDScraper()
    elif source_name in ARCGIS_SOURCES:
        return ArcGISScraper(source_name)
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

    Uses Haiku to evaluate and prioritize active sources based on
    historical yield and relevance to Colorado Front Range developments.
    """
    from .llm import get_llm

    sources = state.get("active_sources", [])
    if not sources:
        return {
            "current_phase": "collection",
            "messages": ["Source discovery: no sources configured"],
            "errors": [],
        }

    llm = get_llm("source_discovery")
    sources_summary = json.dumps(
        [{"name": s.get("name"), "type": s.get("access_method"), "url": s.get("url", "")[:100]}
         for s in sources],
        indent=2,
    )

    response = await llm.ainvoke([
        SystemMessage(content=(
            "You are a data source evaluator for a real estate development intelligence platform "
            "focused on Colorado's Front Range. Evaluate the provided sources and return a JSON "
            "array of source names ordered by expected yield (highest first). Include a brief "
            "reason for each. Format: [{\"name\": \"...\", \"priority\": 1, \"reason\": \"...\"}]"
        )),
        HumanMessage(content=f"Evaluate these data sources:\n{sources_summary}"),
    ])

    try:
        priorities = json.loads(response.content)
        priority_names = [p["name"] for p in priorities]
        prioritized = sorted(sources, key=lambda s: (
            priority_names.index(s.get("name")) if s.get("name") in priority_names else 999
        ))
        logger.info("Source discovery: prioritized %d sources via LLM", len(prioritized))
    except (json.JSONDecodeError, KeyError):
        prioritized = sources
        logger.warning("Source discovery: LLM response not parseable, using original order")

    return {
        "active_sources": prioritized,
        "current_phase": "collection",
        "messages": [f"Source discovery: {len(prioritized)} sources prioritized"],
        "errors": [],
    }


async def collection_specialist_node(state: CollectionTaskState) -> dict[str, Any]:
    """Scrape a single data source.

    Called via Send() — receives a single source config, not the full state.
    No LLM needed — pure HTTP/parsing work.
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
    """Correlate, deduplicate, enrich, and score raw data into developments.

    Uses Haiku to enhance enrichment — extracts structured fields from
    unstructured descriptions and classifies property types.
    """
    from landscraper.pipeline import (
        correlate_records,
        deduplicate,
        enrich_development,
        score_development,
    )

    raw_data = state.get("raw_data", [])
    if not raw_data:
        return {
            "current_phase": "consensus",
            "developments": [],
            "builders": [],
            "messages": ["Pipeline: no raw data to process"],
            "errors": [],
        }

    # Step 1: Deduplicate
    unique = deduplicate(raw_data)

    # Step 2: Correlate into groups
    groups = correlate_records(unique)

    # Step 3: Enrich each group into a development record
    developments = []
    for key, records in groups.items():
        dev = enrich_development(key, records)
        dev = score_development(dev)
        developments.append(dev)

    # Step 4: LLM-enhanced enrichment for developments with descriptions
    developments = await _llm_enrich_developments(developments)

    logger.info(
        "Pipeline: %d raw → %d unique → %d groups → %d developments",
        len(raw_data), len(unique), len(groups), len(developments),
    )

    return {
        "current_phase": "consensus",
        "developments": developments,
        "builders": [],
        "messages": [f"Pipeline produced {len(developments)} developments from {len(raw_data)} raw records"],
        "errors": [],
    }


async def _llm_enrich_developments(developments: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Use Haiku to extract structured fields from development descriptions."""
    from .llm import get_llm

    devs_needing_enrichment = [
        d for d in developments
        if d.get("description") and not d.get("property_type")
    ]

    if not devs_needing_enrichment:
        return developments

    llm = get_llm("enrichment")

    for dev in devs_needing_enrichment:
        try:
            response = await llm.ainvoke([
                SystemMessage(content=(
                    "Extract structured data from this development record description. "
                    "Return JSON with these fields (use null if unknown): "
                    "{\"property_type\": \"residential|commercial|mixed-use|industrial\", "
                    "\"unit_count\": int|null, \"total_sqft\": int|null, "
                    "\"project_name\": str|null, \"owner_name\": str|null}"
                )),
                HumanMessage(content=(
                    f"Description: {dev.get('description', '')}\n"
                    f"Address: {dev.get('address_street', '')} {dev.get('address_city', '')}\n"
                    f"Permit type: {dev.get('permit_type', '')}\n"
                    f"Valuation: {dev.get('valuation_usd', '')}"
                )),
            ])
            extracted = json.loads(response.content)
            for field in ("property_type", "unit_count", "total_sqft", "project_name", "owner_name"):
                if extracted.get(field) is not None and not dev.get(field):
                    dev[field] = extracted[field]
        except (json.JSONDecodeError, Exception) as e:
            logger.debug("LLM enrichment failed for %s: %s", dev.get("correlation_key"), e)

    return developments


async def consensus_node(state: LandscraperState) -> dict[str, Any]:
    """Cross-validate developments and produce scored, validated leads.

    Runs rule-based validators and confidence scoring, then uses Haiku
    for LLM-based quality assessment on borderline cases.
    """
    from landscraper.consensus import compute_confidence, validate_development

    from .llm import get_llm

    developments = state.get("developments", [])
    if not developments:
        return {
            "current_phase": "improvement",
            "validated_leads": [],
            "messages": ["Consensus: no developments to validate"],
            "errors": [],
        }

    validated = []
    rejected_count = 0
    llm = get_llm("consensus")

    for dev in developments:
        # Compute confidence score
        dev["confidence_score"] = compute_confidence(dev)

        # Re-score with updated confidence (affects scoring factor #9)
        from landscraper.pipeline.scorer import score_development
        dev = score_development(dev)

        # Run rule-based validators
        result = validate_development(dev)

        if result["consensus"] == "reject":
            rejected_count += 1
            logger.info("Rejected development %s: %s", dev.get("correlation_key"), result["rejection_reasons"])
            continue

        # LLM quality check on flagged developments
        if result["consensus"] == "flag" and dev.get("description"):
            try:
                response = await llm.ainvoke([
                    SystemMessage(content=(
                        "You assess real estate development leads for a construction intelligence "
                        "platform in Colorado. Given a flagged development, decide: accept or reject. "
                        "Return JSON: {\"decision\": \"accept\"|\"reject\", \"reason\": \"...\"}"
                    )),
                    HumanMessage(content=(
                        f"Flagged for: {result.get('flag_reasons', [])}\n"
                        f"Description: {dev.get('description', '')}\n"
                        f"Score: {dev.get('lead_score', 0)}, Confidence: {dev.get('confidence_score', 0)}\n"
                        f"Location: {dev.get('address_city', '')} {dev.get('county', '')}\n"
                        f"Valuation: ${dev.get('valuation_usd', 0):,.0f}" if dev.get('valuation_usd') else ""
                    )),
                ])
                llm_result = json.loads(response.content)
                if llm_result.get("decision") == "reject":
                    rejected_count += 1
                    logger.info("LLM rejected flagged dev %s: %s", dev.get("correlation_key"), llm_result.get("reason"))
                    continue
            except (json.JSONDecodeError, Exception) as e:
                logger.debug("LLM consensus check failed: %s", e)

        dev["validation_status"] = result["consensus"]
        dev["flag_reasons"] = result.get("flag_reasons", [])
        validated.append(dev)

    logger.info(
        "Consensus: %d developments → %d validated, %d rejected",
        len(developments), len(validated), rejected_count,
    )

    return {
        "current_phase": "improvement",
        "validated_leads": validated,
        "messages": [f"Consensus validated {len(validated)} leads, rejected {rejected_count}"],
        "errors": [],
    }


async def self_improvement_node(state: LandscraperState) -> dict[str, Any]:
    """Evaluate cycle performance and generate strategy recommendations.

    Uses Sonnet for deeper analytical reasoning about patterns and
    strategy adjustments.
    """
    from landscraper.improvement import compute_cycle_metrics, evaluate_strategy

    from .llm import get_llm

    metrics = compute_cycle_metrics(
        raw_data=state.get("raw_data", []),
        developments=state.get("developments", []),
        validated_leads=state.get("validated_leads", []),
        errors=state.get("errors", []),
    )

    # Rule-based recommendations
    recommendations = evaluate_strategy(metrics)

    # LLM-enhanced strategy analysis
    llm = get_llm("strategy")
    try:
        response = await llm.ainvoke([
            SystemMessage(content=(
                "You are a strategy analyst for a real estate development intelligence platform "
                "in Colorado's Front Range. Analyze cycle metrics and provide 2-3 actionable "
                "recommendations to improve data quality, coverage, or efficiency. "
                "Return JSON array: [{\"recommendation\": \"...\", \"priority\": \"high|medium|low\", "
                "\"expected_impact\": \"...\"}]"
            )),
            HumanMessage(content=(
                f"Cycle metrics:\n"
                f"- Raw records collected: {metrics.get('raw_count', 0)}\n"
                f"- Unique after dedup: {metrics.get('unique_count', 0)}\n"
                f"- Developments created: {metrics.get('development_count', 0)}\n"
                f"- Leads validated: {metrics.get('validated_count', 0)}\n"
                f"- Errors: {metrics.get('error_count', 0)}\n"
                f"- Yield rate: {metrics.get('yield_rate', 0):.1%}\n"
                f"- Quality score avg: {metrics.get('avg_quality_score', 0):.1f}\n"
                f"- Rule-based recommendations: {json.dumps(recommendations)}"
            )),
        ])
        llm_recs = json.loads(response.content)
        for rec in llm_recs:
            rec["source"] = "llm"
        recommendations.extend(llm_recs)
    except (json.JSONDecodeError, Exception) as e:
        logger.debug("LLM strategy analysis failed: %s", e)

    metrics["recommendations"] = recommendations

    rec_summary = "; ".join(r["recommendation"][:60] for r in recommendations)
    logger.info("Self-improvement: %s", rec_summary)

    return {
        "current_phase": "delivery",
        "cycle_metrics": metrics,
        "messages": [f"Self-improvement: {len(recommendations)} recommendations"],
        "errors": [],
    }


async def delivery_node(state: LandscraperState) -> dict[str, Any]:
    """Store validated leads and update cycle status.

    Uses Haiku to generate concise lead summaries for notifications.
    """
    from landscraper.api.main import update_cycle_status
    from landscraper.db import async_session
    from landscraper.db.crud import ensure_poc_tenant, store_validated_leads

    from .llm import get_llm

    validated = state.get("validated_leads", [])
    cycle_id = state.get("cycle_id", "unknown")

    # Generate LLM summaries for hot/warm leads
    if validated:
        llm = get_llm("summary")
        hot_warm = [l for l in validated if l.get("tier") in ("hot", "warm")]

        for lead in hot_warm[:10]:  # cap at 10 to control costs
            try:
                response = await llm.ainvoke([
                    SystemMessage(content=(
                        "Write a 1-2 sentence executive summary for this development lead. "
                        "Focus on what makes it actionable for a construction services company."
                    )),
                    HumanMessage(content=(
                        f"Project: {lead.get('project_name', 'Unknown')}\n"
                        f"Type: {lead.get('property_type', 'Unknown')}\n"
                        f"Location: {lead.get('address_city', '')} {lead.get('county', '')}\n"
                        f"Valuation: ${lead.get('valuation_usd', 0):,.0f}\n"
                        f"Score: {lead.get('lead_score', 0)}/100\n"
                        f"Description: {lead.get('description', 'N/A')[:200]}"
                    )),
                ])
                lead["summary"] = response.content.strip()
            except Exception as e:
                logger.debug("Lead summary generation failed: %s", e)

        # Persist to database
        async with async_session() as session:
            tenant_id = await ensure_poc_tenant(session)
            count = await store_validated_leads(session, validated, tenant_id)
            logger.info("Persisted %d leads to DB for cycle %s", count, cycle_id)

        logger.info("Delivered %d leads for cycle %s", len(validated), cycle_id)

    update_cycle_status(
        cycle_id=cycle_id,
        status="complete",
        metrics=state.get("cycle_metrics", {}),
    )

    return {
        "current_phase": "complete",
        "messages": [f"Delivered {len(validated)} leads"],
        "errors": [],
    }
