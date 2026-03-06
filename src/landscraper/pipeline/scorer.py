"""Lead scoring model — 100-point composite score.

Implements the 10-factor scoring model from docs/research/lead_format.md.
"""

from datetime import datetime, timezone
from typing import Any

# High-growth corridors along the Front Range
HIGH_GROWTH_COUNTIES = {"Adams", "Broomfield", "Weld", "Douglas", "Larimer"}
MODERATE_GROWTH_COUNTIES = {"Arapahoe", "Jefferson", "El Paso", "Denver", "Boulder"}


def score_development(dev: dict[str, Any]) -> dict[str, Any]:
    """Apply the 100-point scoring model to a development record.

    Returns the development dict with lead_score, tier, and score_breakdown added.
    """
    breakdown: dict[str, int] = {}

    # 1. Project Scale (20 pts) — based on valuation_usd
    val = dev.get("valuation_usd")
    if val is not None:
        if val >= 5_000_000:
            breakdown["project_scale"] = 20
        elif val >= 1_000_000:
            breakdown["project_scale"] = 14
        elif val >= 500_000:
            breakdown["project_scale"] = 8
        else:
            breakdown["project_scale"] = 3
    else:
        breakdown["project_scale"] = 5  # unknown

    # 2. Permit Status / Timeline (15 pts)
    status = dev.get("permit_status", "").lower()
    status_scores = {
        "issued": 15, "in_progress": 15,
        "approved": 12, "final": 12,
        "under_review": 9,
        "applied": 6,
        "pre_application": 3,
    }
    breakdown["permit_status"] = status_scores.get(status, 3)

    # 3. Unit Count (10 pts)
    units = dev.get("unit_count")
    if units is not None:
        if units >= 50:
            breakdown["unit_count"] = 10
        elif units >= 20:
            breakdown["unit_count"] = 7
        elif units >= 5:
            breakdown["unit_count"] = 4
        else:
            breakdown["unit_count"] = 2
    else:
        breakdown["unit_count"] = 3  # unknown

    # 4. Property Type Fit (10 pts)
    ptype = dev.get("property_type", "").lower()
    ptype_scores = {
        "multifamily": 10, "mixed_use": 10,
        "townhome": 7,
        "single_family": 5,
        "active_adult": 5,
        "manufactured": 3,
    }
    breakdown["property_type_fit"] = ptype_scores.get(ptype, 3)

    # 5. Location Demand (10 pts) — based on county
    county = dev.get("county", "")
    if county in HIGH_GROWTH_COUNTIES:
        breakdown["location_demand"] = 10
    elif county in MODERATE_GROWTH_COUNTIES:
        breakdown["location_demand"] = 6
    else:
        breakdown["location_demand"] = 3

    # 6. Owner Entity Type (8 pts)
    entity = dev.get("owner_entity_type", "unknown").lower()
    entity_scores = {
        "reit": 8, "corporation": 8,
        "llc": 6,
        "trust": 4,
        "individual": 2,
        "unknown": 1,
    }
    breakdown["owner_entity_type"] = entity_scores.get(entity, 1)

    # 7. Contact Completeness (10 pts)
    contact_fields = [
        dev.get("owner_name"),
        dev.get("owner_phone"),
        dev.get("owner_email"),
    ]
    filled = sum(1 for f in contact_fields if f)
    contact_scores = {3: 10, 2: 7, 1: 3, 0: 0}
    breakdown["contact_completeness"] = contact_scores[filled]

    # 8. Recency (7 pts) — based on filing_date
    filing = dev.get("filing_date")
    breakdown["recency"] = _score_recency(filing)

    # 9. Confidence Score (5 pts)
    conf = dev.get("confidence_score", 0.0)
    if conf >= 0.9:
        breakdown["confidence"] = 5
    elif conf >= 0.7:
        breakdown["confidence"] = 4
    elif conf >= 0.5:
        breakdown["confidence"] = 2
    else:
        breakdown["confidence"] = 0

    # 10. Source Corroboration (5 pts)
    src_count = dev.get("source_count", 1)
    if src_count >= 3:
        breakdown["source_corroboration"] = 5
    elif src_count >= 2:
        breakdown["source_corroboration"] = 3
    else:
        breakdown["source_corroboration"] = 1

    total = sum(breakdown.values())

    # Assign tier
    if total >= 80:
        tier = "hot"
    elif total >= 50:
        tier = "warm"
    elif total >= 20:
        tier = "monitor"
    else:
        tier = "cold"

    dev["lead_score"] = total
    dev["tier"] = tier
    dev["score_breakdown"] = breakdown
    return dev


def _score_recency(filing_date: str | None) -> int:
    """Score based on how recently the filing was made."""
    if not filing_date:
        return 1

    try:
        if isinstance(filing_date, str):
            # Handle both date and datetime strings
            if "T" in filing_date:
                filed = datetime.fromisoformat(filing_date.replace("Z", "+00:00"))
            else:
                filed = datetime.fromisoformat(filing_date).replace(tzinfo=timezone.utc)
        else:
            return 1

        now = datetime.now(timezone.utc)
        days = (now - filed).days

        if days <= 7:
            return 7
        elif days <= 30:
            return 5
        elif days <= 90:
            return 3
        else:
            return 1
    except (ValueError, TypeError):
        return 1
