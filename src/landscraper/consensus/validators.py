"""Development validators — rule-based checks that flag data quality issues.

Each validator returns a vote: ACCEPT, FLAG, or REJECT with a reason.
The consensus layer aggregates votes to produce a final validated_leads list.
"""

from typing import Any

VOTE_ACCEPT = "accept"
VOTE_FLAG = "flag"
VOTE_REJECT = "reject"


def _validate_location(dev: dict[str, Any]) -> tuple[str, str]:
    """Check that location data is present and plausible."""
    city = dev.get("address_city")
    county = dev.get("county")
    state = dev.get("address_state", "CO")

    if not city and not county:
        return VOTE_REJECT, "No location data (city or county)"

    if state and state.upper() != "CO":
        return VOTE_FLAG, f"State is {state}, expected CO"

    return VOTE_ACCEPT, "Location present"


def _validate_valuation(dev: dict[str, Any]) -> tuple[str, str]:
    """Check that valuation is reasonable for residential construction."""
    val = dev.get("valuation_usd")
    if val is None:
        return VOTE_ACCEPT, "No valuation to validate"

    if val < 0:
        return VOTE_REJECT, f"Negative valuation: ${val:,.0f}"

    if val > 500_000_000:
        return VOTE_FLAG, f"Unusually high valuation: ${val:,.0f}"

    units = dev.get("unit_count")
    if units and val > 0 and units > 0:
        per_unit = val / units
        if per_unit < 10_000:
            return VOTE_FLAG, f"Low per-unit valuation: ${per_unit:,.0f}"
        if per_unit > 2_000_000:
            return VOTE_FLAG, f"High per-unit valuation: ${per_unit:,.0f}"

    return VOTE_ACCEPT, "Valuation reasonable"


def _validate_permit(dev: dict[str, Any]) -> tuple[str, str]:
    """Check permit data quality."""
    permit_type = dev.get("permit_type", "")
    valid_types = {
        "new_construction", "addition", "demolition_rebuild",
        "change_of_use", "subdivision", "planned_unit_development", "rezoning",
    }
    if permit_type and permit_type not in valid_types:
        return VOTE_FLAG, f"Unknown permit type: {permit_type}"

    return VOTE_ACCEPT, "Permit data valid"


def _validate_source_quality(dev: dict[str, Any]) -> tuple[str, str]:
    """Check that the development has sufficient source backing."""
    source_count = dev.get("source_count", 0)
    if source_count == 0:
        return VOTE_REJECT, "No sources"
    if source_count == 1:
        return VOTE_ACCEPT, "Single source — limited corroboration"
    return VOTE_ACCEPT, f"Corroborated by {source_count} sources"


VALIDATORS = [
    ("location", _validate_location),
    ("valuation", _validate_valuation),
    ("permit", _validate_permit),
    ("source_quality", _validate_source_quality),
]


def validate_development(dev: dict[str, Any]) -> dict[str, Any]:
    """Run all validators against a development and produce a consensus result.

    Returns a dict with:
    - votes: list of (validator_name, vote, reason) tuples
    - consensus: "accept", "flag", or "reject"
    - rejection_reasons: list of rejection reasons (if any)
    """
    votes: list[tuple[str, str, str]] = []

    for name, validator in VALIDATORS:
        vote, reason = validator(dev)
        votes.append((name, vote, reason))

    rejections = [(n, r) for n, v, r in votes if v == VOTE_REJECT]
    flags = [(n, r) for n, v, r in votes if v == VOTE_FLAG]

    if rejections:
        consensus = VOTE_REJECT
    elif flags:
        consensus = VOTE_FLAG
    else:
        consensus = VOTE_ACCEPT

    return {
        "votes": votes,
        "consensus": consensus,
        "rejection_reasons": [r for _, r in rejections],
        "flag_reasons": [r for _, r in flags],
    }
