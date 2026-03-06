"""Cycle performance metrics computation.

Tracks key indicators that the self-improvement agent uses to
evaluate and adjust strategies between cycles.
"""

from typing import Any


def compute_cycle_metrics(
    raw_data: list[dict[str, Any]],
    developments: list[dict[str, Any]],
    validated_leads: list[dict[str, Any]],
    errors: list[str],
) -> dict[str, Any]:
    """Compute performance metrics for a completed cycle.

    Returns a dict of metrics for strategy evaluation.
    """
    total_raw = len(raw_data)
    total_developments = len(developments)
    total_validated = len(validated_leads)
    total_errors = len(errors)

    # Yield rate: what fraction of raw records became validated leads
    yield_rate = total_validated / total_raw if total_raw > 0 else 0.0

    # Conversion rate: developments that passed consensus
    conversion_rate = total_validated / total_developments if total_developments > 0 else 0.0

    # Error rate
    error_rate = total_errors / max(total_raw, 1)

    # Source diversity: number of unique sources in validated leads
    all_sources: set[str] = set()
    for lead in validated_leads:
        for src in lead.get("sources", []):
            all_sources.add(src)

    # Tier distribution
    tier_counts: dict[str, int] = {"hot": 0, "warm": 0, "monitor": 0, "cold": 0}
    for lead in validated_leads:
        tier = lead.get("tier", "cold")
        tier_counts[tier] = tier_counts.get(tier, 0) + 1

    # Average confidence and lead score
    confidences = [l.get("confidence_score", 0) for l in validated_leads]
    scores = [l.get("lead_score", 0) for l in validated_leads]
    avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
    avg_score = sum(scores) / len(scores) if scores else 0.0

    return {
        "total_raw_records": total_raw,
        "total_developments": total_developments,
        "total_validated_leads": total_validated,
        "total_errors": total_errors,
        "yield_rate": round(yield_rate, 4),
        "conversion_rate": round(conversion_rate, 4),
        "error_rate": round(error_rate, 4),
        "unique_source_count": len(all_sources),
        "tier_distribution": tier_counts,
        "avg_confidence": round(avg_confidence, 3),
        "avg_lead_score": round(avg_score, 1),
    }
