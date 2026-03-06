"""Tests for the data pipeline: dedup, correlate, enrich, score."""

from datetime import datetime, timedelta, timezone

import pytest

from landscraper.pipeline.correlator import correlate_records, _normalize_address
from landscraper.pipeline.dedup import deduplicate
from landscraper.pipeline.enricher import enrich_development
from landscraper.pipeline.scorer import score_development


# --- Dedup ---


def test_dedup_removes_duplicates():
    records = [
        {"content_hash": "abc123", "raw_data": {"a": 1}},
        {"content_hash": "abc123", "raw_data": {"a": 2}},
        {"content_hash": "def456", "raw_data": {"b": 3}},
    ]
    result = deduplicate(records)
    assert len(result) == 2
    assert result[0]["raw_data"]["a"] == 1  # keeps first


def test_dedup_keeps_unique():
    records = [
        {"content_hash": "a", "raw_data": {}},
        {"content_hash": "b", "raw_data": {}},
        {"content_hash": "c", "raw_data": {}},
    ]
    assert len(deduplicate(records)) == 3


def test_dedup_handles_missing_hash():
    records = [
        {"raw_data": {"no_hash": True}},
        {"raw_data": {"no_hash_either": True}},
    ]
    assert len(deduplicate(records)) == 2


# --- Correlator ---


def test_normalize_address():
    assert _normalize_address("123 Main Street") == "123 main st"
    assert _normalize_address("456 Oak Avenue, #200") == "456 oak ave 200"


def test_correlate_by_permit_number():
    records = [
        {"raw_data": {"permit_number": "BLD-001", "source": "a"}},
        {"raw_data": {"permit_number": "BLD-001", "source": "b"}},
        {"raw_data": {"permit_number": "BLD-002", "source": "c"}},
    ]
    groups = correlate_records(records)
    assert len(groups) == 2
    assert len(groups["permit:BLD-001"]) == 2
    assert len(groups["permit:BLD-002"]) == 1


def test_correlate_by_address():
    records = [
        {"raw_data": {"address_street": "100 Main St", "address_city": "Denver"}},
        {"raw_data": {"address_street": "100 Main Street", "address_city": "Denver"}},
    ]
    groups = correlate_records(records)
    # Both should normalize to the same address key
    assert len(groups) == 1
    key = list(groups.keys())[0]
    assert len(groups[key]) == 2


def test_correlate_by_county():
    records = [
        {"raw_data": {"county": "Adams", "year": "2025", "month": "01"}},
        {"raw_data": {"county": "Adams", "year": "2025", "month": "01"}},
        {"raw_data": {"county": "Adams", "year": "2025", "month": "02"}},
    ]
    groups = correlate_records(records)
    assert len(groups) == 2
    assert len(groups["county:Adams:2025:01"]) == 2


def test_correlate_uncorrelated():
    records = [
        {"raw_data": {"title": "random article"}},
    ]
    groups = correlate_records(records)
    assert len(groups) == 1
    key = list(groups.keys())[0]
    assert key.startswith("_uncorrelated:")


# --- Enricher ---


def test_enrich_merges_fields():
    records = [
        {
            "source_name": "source_a",
            "raw_data": {
                "permit_number": "BLD-001",
                "address_city": "Denver",
                "valuation_usd": "5000000",
            },
        },
        {
            "source_name": "source_b",
            "raw_data": {
                "permit_number": "BLD-001",
                "owner_name": "Acme Dev LLC",
                "unit_count": "50",
            },
        },
    ]
    dev = enrich_development("permit:BLD-001", records)

    assert dev["permit_number"] == "BLD-001"
    assert dev["address_city"] == "Denver"
    assert dev["owner_name"] == "Acme Dev LLC"
    assert dev["valuation_usd"] == 5000000.0
    assert dev["unit_count"] == 50
    assert dev["source_count"] == 2
    assert set(dev["sources"]) == {"source_a", "source_b"}


def test_enrich_handles_empty_group():
    dev = enrich_development("test:empty", [])
    assert dev["source_count"] == 0
    assert dev["permit_number"] is None


# --- Scorer ---


def test_score_high_value_development():
    dev = {
        "valuation_usd": 10_000_000,
        "permit_status": "issued",
        "unit_count": 100,
        "property_type": "multifamily",
        "county": "Adams",
        "owner_entity_type": "corporation",
        "owner_name": "Big Corp",
        "owner_phone": "+13035551234",
        "owner_email": "info@bigcorp.com",
        "filing_date": (datetime.now(timezone.utc) - timedelta(days=3)).isoformat(),
        "confidence_score": 0.95,
        "source_count": 4,
    }
    scored = score_development(dev)

    assert scored["lead_score"] >= 80
    assert scored["tier"] == "hot"
    assert scored["score_breakdown"]["project_scale"] == 20
    assert scored["score_breakdown"]["permit_status"] == 15
    assert scored["score_breakdown"]["unit_count"] == 10


def test_score_low_value_development():
    dev = {
        "valuation_usd": 100_000,
        "permit_status": "pre_application",
        "unit_count": 1,
        "property_type": "manufactured",
        "county": "Unknown",
        "owner_entity_type": "individual",
        "filing_date": (datetime.now(timezone.utc) - timedelta(days=200)).isoformat(),
        "confidence_score": 0.3,
        "source_count": 1,
    }
    scored = score_development(dev)

    assert scored["lead_score"] < 30
    assert scored["tier"] in ("cold", "monitor")


def test_score_unknown_fields():
    """Development with mostly unknown fields should still score."""
    dev = {}
    scored = score_development(dev)

    assert "lead_score" in scored
    assert "tier" in scored
    assert scored["lead_score"] > 0  # defaults give some points


def test_score_tiers():
    """Verify tier boundaries."""
    assert score_development({"lead_score": 0})["tier"] in ("cold", "monitor")

    # Construct a warm-tier development
    warm = {
        "valuation_usd": 2_000_000,
        "permit_status": "under_review",
        "unit_count": 25,
        "property_type": "townhome",
        "county": "Boulder",
        "owner_entity_type": "llc",
        "owner_name": "Test LLC",
        "owner_phone": "+13035551234",
        "confidence_score": 0.75,
        "source_count": 2,
    }
    scored_warm = score_development(warm)
    assert scored_warm["tier"] in ("warm", "hot")


# --- Pipeline integration via node ---


@pytest.mark.asyncio
async def test_pipeline_node_processes_records():
    from landscraper.agents.nodes import pipeline_node

    state = {
        "raw_data": [
            {
                "source_name": "source_a",
                "content_hash": "hash1",
                "raw_data": {
                    "permit_number": "BLD-001",
                    "address_city": "Denver",
                    "county": "Denver",
                    "valuation_usd": "3000000",
                    "unit_count": "30",
                    "property_type": "multifamily",
                    "permit_status": "approved",
                },
            },
            {
                "source_name": "source_b",
                "content_hash": "hash2",
                "raw_data": {
                    "permit_number": "BLD-001",
                    "owner_name": "Denver Dev LLC",
                    "owner_entity_type": "llc",
                },
            },
        ],
        "current_phase": "pipeline",
        "messages": [],
        "errors": [],
        "cycle_id": "test",
        "active_sources": [],
        "developments": [],
        "builders": [],
        "validated_leads": [],
        "cycle_metrics": {},
    }

    result = await pipeline_node(state)

    assert result["current_phase"] == "consensus"
    assert len(result["developments"]) == 1
    dev = result["developments"][0]
    assert dev["permit_number"] == "BLD-001"
    assert dev["source_count"] == 2
    assert "lead_score" in dev
    assert "tier" in dev


@pytest.mark.asyncio
async def test_pipeline_node_empty_data():
    from landscraper.agents.nodes import pipeline_node

    state = {
        "raw_data": [],
        "current_phase": "pipeline",
        "messages": [],
        "errors": [],
        "cycle_id": "test",
        "active_sources": [],
        "developments": [],
        "builders": [],
        "validated_leads": [],
        "cycle_metrics": {},
    }

    result = await pipeline_node(state)
    assert result["developments"] == []
    assert any("no raw data" in m for m in result["messages"])
