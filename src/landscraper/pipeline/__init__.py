"""Data pipeline: dedup, correlate, aggregate, enrich, and score raw records."""

from .correlator import correlate_records
from .dedup import deduplicate
from .enricher import enrich_development
from .scorer import score_development

__all__ = [
    "correlate_records",
    "deduplicate",
    "enrich_development",
    "score_development",
]
