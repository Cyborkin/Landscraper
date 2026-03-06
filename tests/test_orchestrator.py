import uuid

import pytest
import respx
from httpx import Response

from landscraper.agents.orchestrator import build_graph, compile_graph
from landscraper.agents.state import LandscraperState


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


def test_graph_builds():
    graph = build_graph()
    assert graph is not None


def test_graph_compiles():
    app = compile_graph()
    assert app is not None


@pytest.mark.asyncio
async def test_graph_runs_empty_cycle():
    """A cycle with no active sources should complete without errors."""
    app = compile_graph()
    state = _initial_state()
    result = await app.ainvoke(state)

    assert result["current_phase"] == "complete"
    assert len(result["errors"]) == 0


@respx.mock
@pytest.mark.asyncio
async def test_graph_runs_with_sources():
    """A cycle with active sources should spawn collection specialists."""
    # Mock the SODA and EDGAR APIs so the real scrapers succeed
    respx.get("https://data.colorado.gov/resource/v4as-sthd.json").mock(
        return_value=Response(200, json=[
            {"county": "Adams", "year": "2025", "month": "01", "permits": "10", "units": "10", "valuation": "1000"},
        ])
    )
    respx.get("https://efts.sec.gov/LATEST/search-index").mock(
        return_value=Response(200, json={"hits": {"hits": []}})
    )

    app = compile_graph()
    state = _initial_state(
        active_sources=[
            {"id": "src_1", "name": "colorado_soda_permits", "access_method": "api"},
            {"id": "src_2", "name": "sec_edgar", "access_method": "api"},
        ]
    )
    result = await app.ainvoke(state)

    assert result["current_phase"] == "complete"
    assert len(result["errors"]) == 0
    assert len(result["raw_data"]) >= 1


def test_graph_has_expected_nodes():
    graph = build_graph()
    node_names = set(graph.nodes.keys())
    expected = {
        "source_discovery",
        "collection_specialist",
        "pipeline",
        "consensus",
        "self_improvement",
        "delivery",
    }
    assert expected.issubset(node_names)
