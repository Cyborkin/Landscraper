"""End-to-end integration test: full cycle from discovery to delivery.

Runs the complete LangGraph orchestrator against mocked data sources
and verifies leads flow through all pipeline stages.
"""

import uuid

import pytest
import respx
from httpx import Response

from landscraper.agents.orchestrator import compile_graph
from landscraper.agents.state import LandscraperState


# Mock data for two sources
SODA_RESPONSE = [
    {
        "county": "Adams",
        "year": "2025",
        "month": "01",
        "permits": "42",
        "units": "50",
        "valuation": "12000000",
    },
    {
        "county": "Denver",
        "year": "2025",
        "month": "01",
        "permits": "85",
        "units": "120",
        "valuation": "35000000",
    },
    {
        "county": "Boulder",
        "year": "2025",
        "month": "01",
        "permits": "30",
        "units": "35",
        "valuation": "9000000",
    },
    {
        "county": "Pueblo",
        "year": "2025",
        "month": "01",
        "permits": "5",
        "units": "5",
        "valuation": "1000000",
    },
]

CENSUS_CSV = """\
08,001,3,8,Adams County,120,120,30000,8,16,2400,0,15,60,5000,0,143,196,37400
08,031,3,8,Denver County,200,200,55000,12,24,3600,0,25,100,8000,0,237,324,66600
08,013,3,8,Boulder County,80,80,22000,5,10,1500,0,8,35,2800,0,93,125,26300
"""

EDGAR_RESPONSE = {
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
        ]
    }
}


def _initial_state(**overrides) -> LandscraperState:
    defaults: LandscraperState = {
        "messages": [],
        "current_phase": "discovery",
        "cycle_id": str(uuid.uuid4()),
        "active_sources": [],
        "raw_data": [],
        "developments": [],
        "builders": [],
        "validated_leads": [],
        "cycle_metrics": {},
        "errors": [],
    }
    defaults.update(overrides)
    return defaults


@respx.mock
@pytest.mark.asyncio
async def test_full_cycle_three_sources():
    """Complete end-to-end cycle with 3 data sources."""
    # Mock all external APIs
    respx.get("https://data.colorado.gov/resource/v4as-sthd.json").mock(
        return_value=Response(200, json=SODA_RESPONSE)
    )
    respx.get("https://www2.census.gov/econ/bps/County/co2025a.txt").mock(
        return_value=Response(200, text=CENSUS_CSV)
    )
    respx.get("https://efts.sec.gov/LATEST/search-index").mock(
        return_value=Response(200, json=EDGAR_RESPONSE)
    )

    app = compile_graph()
    state = _initial_state(
        active_sources=[
            {"name": "colorado_soda_permits", "access_method": "api"},
            {"name": "census_bps", "access_method": "api"},
            {"name": "sec_edgar", "access_method": "api"},
        ]
    )

    result = await app.ainvoke(state)

    # Phase completion
    assert result["current_phase"] == "complete"

    # Collection should have gathered data
    assert len(result["raw_data"]) > 0, "Should collect raw data from sources"

    # Pipeline should produce developments
    assert len(result["developments"]) > 0, "Should produce developments"

    # Consensus should validate some leads
    assert len(result["validated_leads"]) > 0, "Should produce validated leads"

    # All validated leads should have scores and tiers
    for lead in result["validated_leads"]:
        assert "lead_score" in lead
        assert "tier" in lead
        assert lead["tier"] in ("hot", "warm", "monitor", "cold")
        assert "confidence_score" in lead
        assert 0.0 <= lead["confidence_score"] <= 1.0

    # Self-improvement should compute metrics
    metrics = result["cycle_metrics"]
    assert "total_raw_records" in metrics
    assert "yield_rate" in metrics
    assert "recommendations" in metrics

    # No errors
    assert len(result["errors"]) == 0, f"Unexpected errors: {result['errors']}"

    # Messages should track progress
    assert len(result["messages"]) > 0


@respx.mock
@pytest.mark.asyncio
async def test_full_cycle_single_source():
    """Minimal cycle with just one source."""
    respx.get("https://data.colorado.gov/resource/v4as-sthd.json").mock(
        return_value=Response(200, json=SODA_RESPONSE)
    )

    app = compile_graph()
    state = _initial_state(
        active_sources=[
            {"name": "colorado_soda_permits", "access_method": "api"},
        ]
    )

    result = await app.ainvoke(state)

    assert result["current_phase"] == "complete"
    assert len(result["raw_data"]) == 3  # Adams, Denver, Boulder (not Pueblo)
    assert len(result["errors"]) == 0


@respx.mock
@pytest.mark.asyncio
async def test_full_cycle_with_source_failure():
    """Cycle should complete even if one source fails."""
    respx.get("https://data.colorado.gov/resource/v4as-sthd.json").mock(
        return_value=Response(200, json=SODA_RESPONSE)
    )
    respx.get("https://efts.sec.gov/LATEST/search-index").mock(
        return_value=Response(500)
    )

    app = compile_graph()
    state = _initial_state(
        active_sources=[
            {"name": "colorado_soda_permits", "access_method": "api"},
            {"name": "sec_edgar", "access_method": "api"},
        ]
    )

    result = await app.ainvoke(state)

    # Should complete despite SEC failure
    assert result["current_phase"] == "complete"
    # SODA data should still come through
    assert len(result["raw_data"]) >= 3
    # Should have validated leads from SODA
    assert len(result["validated_leads"]) > 0


@respx.mock
@pytest.mark.asyncio
async def test_full_cycle_empty_sources():
    """Cycle with no active sources should complete cleanly."""
    app = compile_graph()
    state = _initial_state(active_sources=[])

    result = await app.ainvoke(state)

    assert result["current_phase"] == "complete"
    assert result["raw_data"] == []
    assert result["validated_leads"] == []
    assert len(result["errors"]) == 0
