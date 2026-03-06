import uuid

import pytest

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


@pytest.mark.asyncio
async def test_graph_runs_with_sources():
    """A cycle with active sources should spawn collection specialists."""
    app = compile_graph()
    state = _initial_state(
        active_sources=[
            {"id": "src_1", "name": "PPRBD", "url": "https://pprbd.org"},
            {"id": "src_2", "name": "Census BPS", "url": "https://census.gov/bps"},
        ]
    )
    result = await app.ainvoke(state)

    assert result["current_phase"] == "complete"
    assert len(result["errors"]) == 0


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
