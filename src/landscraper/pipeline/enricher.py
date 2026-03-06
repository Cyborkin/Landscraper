"""Enrich development records with derived and merged fields.

Takes a correlation group (multiple raw records about the same development)
and produces a single enriched development dict.
"""

from typing import Any


def _merge_field(records: list[dict[str, Any]], field: str) -> Any:
    """Extract the best value for a field across multiple records.

    Returns the first non-None, non-empty value found.
    """
    for record in records:
        raw = record.get("raw_data", {})
        val = raw.get(field)
        if val is not None and val != "":
            return val
    return None


def _collect_sources(records: list[dict[str, Any]]) -> list[str]:
    """Collect unique source names from a group of records."""
    sources: list[str] = []
    seen: set[str] = set()
    for record in records:
        src = record.get("source_name", "")
        if src and src not in seen:
            sources.append(src)
            seen.add(src)
    return sources


def enrich_development(
    correlation_key: str,
    records: list[dict[str, Any]],
) -> dict[str, Any]:
    """Merge a correlation group into a single enriched development record.

    Combines fields from multiple sources, preferring non-null values.
    Sets source_count and sources for consensus scoring.
    """
    sources = _collect_sources(records)

    development = {
        "correlation_key": correlation_key,
        "source_count": len(sources),
        "sources": sources,
        # Permit info
        "permit_number": _merge_field(records, "permit_number"),
        "permit_type": _merge_field(records, "permit_type") or "new_construction",
        "permit_status": _merge_field(records, "permit_status") or "applied",
        "jurisdiction": _merge_field(records, "jurisdiction"),
        # Location
        "address_street": _merge_field(records, "address_street") or _merge_field(records, "address"),
        "address_city": _merge_field(records, "address_city") or _merge_field(records, "city"),
        "address_state": _merge_field(records, "address_state") or "CO",
        "address_zip": _merge_field(records, "address_zip"),
        "county": _merge_field(records, "county"),
        "latitude": _merge_field(records, "latitude"),
        "longitude": _merge_field(records, "longitude"),
        # Zoning
        "zoning_current": _merge_field(records, "zoning_current"),
        "zoning_proposed": _merge_field(records, "zoning_proposed"),
        # Project details
        "property_type": _merge_field(records, "property_type") or "single_family",
        "project_name": _merge_field(records, "project_name"),
        "description": _merge_field(records, "description"),
        "valuation_usd": _safe_float(_merge_field(records, "valuation_usd") or _merge_field(records, "valuation")),
        "unit_count": _safe_int(_merge_field(records, "unit_count") or _merge_field(records, "units")),
        "total_sqft": _safe_int(_merge_field(records, "total_sqft")),
        "lot_size_acres": _safe_float(_merge_field(records, "lot_size_acres")),
        "stories": _safe_int(_merge_field(records, "stories")),
        # Stakeholders
        "owner_name": _merge_field(records, "owner_name"),
        "owner_entity_type": _merge_field(records, "owner_entity_type") or "unknown",
        "owner_phone": _merge_field(records, "owner_phone"),
        "owner_email": _merge_field(records, "owner_email"),
        "applicant_name": _merge_field(records, "applicant_name"),
        "contractor_name": _merge_field(records, "contractor_name"),
        "architect_name": _merge_field(records, "architect_name"),
        # Dates
        "filing_date": _merge_field(records, "filing_date"),
        "approval_date": _merge_field(records, "approval_date"),
        "estimated_start_date": _merge_field(records, "estimated_start_date"),
        "estimated_completion_date": _merge_field(records, "estimated_completion_date"),
        # Tags
        "tags": _collect_tags(records),
    }

    return development


def _safe_int(val: Any) -> int | None:
    if val is None:
        return None
    try:
        return int(val)
    except (ValueError, TypeError):
        return None


def _safe_float(val: Any) -> float | None:
    if val is None:
        return None
    try:
        return float(val)
    except (ValueError, TypeError):
        return None


def _collect_tags(records: list[dict[str, Any]]) -> list[str]:
    """Collect unique tags from all records in a group."""
    tags: list[str] = []
    seen: set[str] = set()
    for record in records:
        raw = record.get("raw_data", {})
        for tag in raw.get("tags", []):
            if tag not in seen:
                tags.append(tag)
                seen.add(tag)
    return tags
