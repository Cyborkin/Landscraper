"""Confidence scoring for development leads.

Computes a 0.0-1.0 confidence score based on data quality signals:
- Source count and diversity
- Field completeness
- Data consistency across sources
- Source reliability tiers
"""

from typing import Any

# Source reliability weights (higher = more trustworthy)
SOURCE_RELIABILITY = {
    "census_bps": 0.95,
    "colorado_soda_permits": 0.90,
    "sec_edgar": 0.85,
    "jefferson_county_permits": 0.85,
    "adams_county_permits": 0.85,
    "denver_permits": 0.85,
    "douglas_county_permits": 0.85,
    "el_paso_permits": 0.85,
    "boulder_permits": 0.85,
    "larimer_county_permits": 0.85,
    "weld_county_permits": 0.80,
    "bizwest_real_estate": 0.60,
    "denver_planning": 0.70,
}

# Fields that contribute to completeness score
COMPLETENESS_FIELDS = [
    "permit_number",
    "address_street",
    "address_city",
    "county",
    "property_type",
    "valuation_usd",
    "unit_count",
    "owner_name",
    "filing_date",
    "permit_status",
    "jurisdiction",
    "description",
]


def compute_confidence(dev: dict[str, Any]) -> float:
    """Compute a confidence score (0.0-1.0) for a development record.

    Weighted formula:
    - 40% source corroboration (count + reliability)
    - 40% field completeness
    - 20% data consistency
    """
    source_score = _source_corroboration_score(dev)
    completeness_score = _field_completeness_score(dev)
    consistency_score = _consistency_score(dev)

    confidence = (
        0.40 * source_score
        + 0.40 * completeness_score
        + 0.20 * consistency_score
    )

    return round(min(max(confidence, 0.0), 1.0), 3)


def _source_corroboration_score(dev: dict[str, Any]) -> float:
    """Score based on number and reliability of sources."""
    sources = dev.get("sources", [])
    if not sources:
        return 0.0

    # Base score from count (diminishing returns)
    count = len(sources)
    count_score = min(count / 3.0, 1.0)  # 3+ sources = max count score

    # Weighted average reliability of contributing sources
    reliabilities = [
        SOURCE_RELIABILITY.get(src, 0.50)
        for src in sources
    ]
    avg_reliability = sum(reliabilities) / len(reliabilities) if reliabilities else 0.5

    return 0.6 * count_score + 0.4 * avg_reliability


def _field_completeness_score(dev: dict[str, Any]) -> float:
    """Score based on how many key fields are populated."""
    filled = sum(
        1 for field in COMPLETENESS_FIELDS
        if dev.get(field) is not None and dev.get(field) != ""
    )
    return filled / len(COMPLETENESS_FIELDS)


def _consistency_score(dev: dict[str, Any]) -> float:
    """Score based on internal data consistency.

    Checks for logical consistency between fields.
    """
    score = 1.0
    penalties = 0

    # Valuation should be positive if present
    val = dev.get("valuation_usd")
    if val is not None:
        try:
            if float(val) <= 0:
                penalties += 1
        except (ValueError, TypeError):
            pass

    # Unit count should be positive if present
    units = dev.get("unit_count")
    if units is not None:
        try:
            if int(units) <= 0:
                penalties += 1
        except (ValueError, TypeError):
            pass

    # City and county should both be present or both absent
    has_city = bool(dev.get("address_city"))
    has_county = bool(dev.get("county"))
    if has_city != has_county:
        penalties += 0.5

    # Permit status should be a known value
    valid_statuses = {
        "pre_application", "applied", "under_review", "approved",
        "issued", "in_progress", "final", "expired", "denied",
    }
    status = dev.get("permit_status", "")
    if status and status.lower() not in valid_statuses:
        penalties += 0.5

    return max(score - (penalties * 0.2), 0.0)
