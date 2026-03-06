"""Tests for the consensus layer: validators and confidence scoring."""

import pytest

from landscraper.consensus.confidence import compute_confidence
from landscraper.consensus.validators import (
    VOTE_ACCEPT,
    VOTE_FLAG,
    VOTE_REJECT,
    validate_development,
)


# --- Confidence scoring ---


def test_confidence_high_quality():
    """Well-sourced, complete development should score high."""
    dev = {
        "sources": ["census_bps", "colorado_soda_permits", "denver_permits"],
        "permit_number": "BLD-001",
        "address_street": "100 Main St",
        "address_city": "Denver",
        "county": "Denver",
        "property_type": "multifamily",
        "valuation_usd": 5000000,
        "unit_count": 50,
        "owner_name": "Test Corp",
        "filing_date": "2026-01-15",
        "permit_status": "approved",
        "jurisdiction": "City of Denver",
        "description": "50-unit apartment",
    }
    conf = compute_confidence(dev)
    assert conf >= 0.7


def test_confidence_low_quality():
    """Sparse, single-source development should score low."""
    dev = {
        "sources": ["unknown_source"],
        "county": "Denver",
    }
    conf = compute_confidence(dev)
    assert conf < 0.5


def test_confidence_no_sources():
    dev = {"sources": []}
    conf = compute_confidence(dev)
    assert conf < 0.3


def test_confidence_bounds():
    """Confidence should always be between 0 and 1."""
    dev_empty = {}
    assert 0.0 <= compute_confidence(dev_empty) <= 1.0

    dev_full = {
        "sources": ["a", "b", "c", "d", "e"],
        **{field: "value" for field in [
            "permit_number", "address_street", "address_city", "county",
            "property_type", "valuation_usd", "unit_count", "owner_name",
            "filing_date", "permit_status", "jurisdiction", "description",
        ]},
    }
    assert 0.0 <= compute_confidence(dev_full) <= 1.0


# --- Validators ---


def test_validate_good_development():
    dev = {
        "address_city": "Denver",
        "county": "Denver",
        "address_state": "CO",
        "valuation_usd": 3000000,
        "unit_count": 30,
        "permit_type": "new_construction",
        "source_count": 2,
    }
    result = validate_development(dev)
    assert result["consensus"] == VOTE_ACCEPT
    assert len(result["rejection_reasons"]) == 0


def test_validate_no_location_rejects():
    dev = {"valuation_usd": 1000000}
    result = validate_development(dev)
    assert result["consensus"] == VOTE_REJECT
    assert any("No location" in r for r in result["rejection_reasons"])


def test_validate_negative_valuation_rejects():
    dev = {
        "address_city": "Denver",
        "county": "Denver",
        "valuation_usd": -100,
    }
    result = validate_development(dev)
    assert result["consensus"] == VOTE_REJECT


def test_validate_high_valuation_flags():
    dev = {
        "address_city": "Denver",
        "county": "Denver",
        "valuation_usd": 600_000_000,
        "source_count": 1,
    }
    result = validate_development(dev)
    assert result["consensus"] == VOTE_FLAG
    assert any("high valuation" in r.lower() for r in result["flag_reasons"])


def test_validate_wrong_state_flags():
    dev = {
        "address_city": "Dallas",
        "county": "Dallas",
        "address_state": "TX",
        "source_count": 1,
    }
    result = validate_development(dev)
    assert result["consensus"] == VOTE_FLAG


def test_validate_unknown_permit_type_flags():
    dev = {
        "address_city": "Denver",
        "county": "Denver",
        "permit_type": "space_elevator",
        "source_count": 1,
    }
    result = validate_development(dev)
    assert result["consensus"] == VOTE_FLAG


# --- Consensus node integration ---


@pytest.mark.asyncio
async def test_consensus_node_validates():
    from landscraper.agents.nodes import consensus_node

    state = {
        "developments": [
            {
                "correlation_key": "permit:BLD-001",
                "permit_number": "BLD-001",
                "address_city": "Denver",
                "county": "Denver",
                "address_state": "CO",
                "valuation_usd": 3000000,
                "unit_count": 30,
                "property_type": "multifamily",
                "permit_type": "new_construction",
                "permit_status": "approved",
                "owner_name": "Test LLC",
                "owner_entity_type": "llc",
                "source_count": 2,
                "sources": ["census_bps", "denver_permits"],
                "filing_date": "2026-01-15",
                "jurisdiction": "City of Denver",
                "description": "30-unit apartment",
            },
        ],
        "current_phase": "consensus",
        "messages": [],
        "errors": [],
        "cycle_id": "test",
        "active_sources": [],
        "raw_data": [],
        "builders": [],
        "validated_leads": [],
        "cycle_metrics": {},
    }

    result = await consensus_node(state)
    assert result["current_phase"] == "improvement"
    assert len(result["validated_leads"]) == 1
    lead = result["validated_leads"][0]
    assert "confidence_score" in lead
    assert "lead_score" in lead
    assert lead["validation_status"] in (VOTE_ACCEPT, VOTE_FLAG)


@pytest.mark.asyncio
async def test_consensus_node_rejects_bad():
    from landscraper.agents.nodes import consensus_node

    state = {
        "developments": [
            {
                "correlation_key": "bad:no-location",
                "valuation_usd": -500,
                "source_count": 0,
                "sources": [],
            },
        ],
        "current_phase": "consensus",
        "messages": [],
        "errors": [],
        "cycle_id": "test",
        "active_sources": [],
        "raw_data": [],
        "builders": [],
        "validated_leads": [],
        "cycle_metrics": {},
    }

    result = await consensus_node(state)
    assert len(result["validated_leads"]) == 0


@pytest.mark.asyncio
async def test_consensus_node_empty():
    from landscraper.agents.nodes import consensus_node

    state = {
        "developments": [],
        "current_phase": "consensus",
        "messages": [],
        "errors": [],
        "cycle_id": "test",
        "active_sources": [],
        "raw_data": [],
        "builders": [],
        "validated_leads": [],
        "cycle_metrics": {},
    }

    result = await consensus_node(state)
    assert result["validated_leads"] == []
