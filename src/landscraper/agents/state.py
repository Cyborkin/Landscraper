import operator
from typing import Annotated, Any

from langchain_core.messages import BaseMessage
from typing_extensions import TypedDict


class LandscraperState(TypedDict):
    """Shared state for the Landscraper multi-agent graph."""

    # LLM conversation history (append-only)
    messages: Annotated[list[BaseMessage], operator.add]

    # Workflow control
    current_phase: str  # discovery, collection, pipeline, consensus, improvement, delivery, complete
    cycle_id: str  # unique ID for this weekly cycle run

    # Source management
    active_sources: list[dict[str, Any]]  # sources to scrape this cycle

    # Collection results (append-only — multiple collection agents contribute)
    raw_data: Annotated[list[dict[str, Any]], operator.add]

    # Pipeline results (overwritten each phase)
    developments: list[dict[str, Any]]  # normalized development records
    builders: list[dict[str, Any]]  # normalized builder records

    # Consensus output
    validated_leads: list[dict[str, Any]]  # scored, validated leads

    # Self-improvement metrics
    cycle_metrics: dict[str, Any]

    # Error tracking (append-only)
    errors: Annotated[list[str], operator.add]


class CollectionTaskState(TypedDict):
    """State passed to individual collection specialist via Send()."""

    source: dict[str, Any]  # the source to scrape
    cycle_id: str
