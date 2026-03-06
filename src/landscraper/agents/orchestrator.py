"""Landscraper orchestrator — the main LangGraph agent graph.

Manages the weekly aggregation cycle:
  source_discovery -> collection (parallel) -> pipeline -> consensus -> improvement -> delivery
"""

from typing import Any

from langgraph.types import Send
from langgraph.graph import END, START, StateGraph

from .nodes import (
    collection_specialist_node,
    consensus_node,
    delivery_node,
    pipeline_node,
    self_improvement_node,
    source_discovery_node,
)
from .state import LandscraperState


def route_after_discovery(state: LandscraperState) -> list[Send] | str:
    """After source discovery, delegate collection to specialist agents.

    Uses Send() to spawn one collection_specialist per active source.
    If no sources, skip to pipeline (which will produce empty results).
    """
    sources = state.get("active_sources", [])
    if not sources:
        return "pipeline"

    return [
        Send("collection_specialist", {"source": source, "cycle_id": state["cycle_id"]})
        for source in sources
    ]


def route_after_phase(state: LandscraperState) -> str:
    """Generic phase router based on current_phase."""
    phase = state.get("current_phase", "complete")
    phase_map = {
        "collection": "source_discovery",  # shouldn't happen, but safe fallback
        "pipeline": "pipeline",
        "consensus": "consensus",
        "improvement": "self_improvement",
        "delivery": "delivery",
        "complete": END,
    }
    return phase_map.get(phase, END)


def build_graph() -> StateGraph:
    """Construct the Landscraper orchestrator graph."""
    graph = StateGraph(LandscraperState)

    # Add nodes
    graph.add_node("source_discovery", source_discovery_node)
    graph.add_node("collection_specialist", collection_specialist_node)
    graph.add_node("pipeline", pipeline_node)
    graph.add_node("consensus", consensus_node)
    graph.add_node("self_improvement", self_improvement_node)
    graph.add_node("delivery", delivery_node)

    # Wire edges
    graph.add_edge(START, "source_discovery")

    # After discovery, dynamically spawn collection agents via Send()
    graph.add_conditional_edges(
        "source_discovery",
        route_after_discovery,
        ["collection_specialist", "pipeline"],
    )

    # All collection specialists feed into pipeline
    graph.add_edge("collection_specialist", "pipeline")

    # Sequential phases after pipeline
    graph.add_edge("pipeline", "consensus")
    graph.add_edge("consensus", "self_improvement")
    graph.add_edge("self_improvement", "delivery")
    graph.add_edge("delivery", END)

    return graph


def compile_graph(**kwargs: Any):
    """Build and compile the graph, optionally with a checkpointer."""
    graph = build_graph()
    return graph.compile(**kwargs)
