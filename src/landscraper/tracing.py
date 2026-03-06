"""LangSmith tracing configuration.

Sets environment variables that LangChain/LangGraph auto-detect.
Call configure_tracing() at application startup.
"""

import os
from typing import Any

from landscraper.config import settings


def configure_tracing() -> bool:
    """Configure LangSmith tracing from Landscraper settings.

    Sets the LANGCHAIN_* env vars that LangChain/LangGraph auto-detect.
    Returns True if tracing was enabled, False otherwise.
    """
    if not settings.langsmith_tracing_enabled or not settings.langsmith_api_key:
        os.environ.pop("LANGCHAIN_TRACING_V2", None)
        return False

    os.environ["LANGCHAIN_TRACING_V2"] = "true"
    os.environ["LANGCHAIN_API_KEY"] = settings.langsmith_api_key
    os.environ["LANGCHAIN_PROJECT"] = settings.langsmith_project

    return True


def disable_tracing() -> None:
    """Explicitly disable tracing (used in tests)."""
    os.environ.pop("LANGCHAIN_TRACING_V2", None)
    os.environ.pop("LANGCHAIN_API_KEY", None)
    os.environ.pop("LANGCHAIN_PROJECT", None)


def tracing_is_enabled() -> bool:
    """Check if tracing is currently active."""
    return os.environ.get("LANGCHAIN_TRACING_V2", "").lower() == "true"


def cycle_run_metadata(cycle_id: str, sources: list[str] | None = None) -> dict[str, Any]:
    """Build metadata dict for a cycle run."""
    metadata: dict[str, Any] = {
        "cycle_id": cycle_id,
        "app": "landscraper",
    }
    if sources:
        metadata["sources"] = sources
        metadata["source_count"] = len(sources)

    return metadata


def cycle_run_config(cycle_id: str, sources: list[str] | None = None) -> dict[str, Any]:
    """Build LangGraph run config with LangSmith metadata and tags.

    Usage: await graph.ainvoke(state, config=cycle_run_config(cycle_id))
    """
    return {
        "metadata": cycle_run_metadata(cycle_id, sources),
        "tags": ["landscraper", "cycle"],
        "run_name": f"landscraper-cycle-{cycle_id[:8]}",
    }
