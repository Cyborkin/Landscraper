"""Correlate raw records into grouped development clusters.

Groups records that likely describe the same development based on:
- Matching permit numbers
- Matching addresses (normalized)
- Matching source + county + approximate time window
"""

import re
from collections import defaultdict
from typing import Any


def _normalize_address(address: str) -> str:
    """Normalize address for fuzzy matching."""
    addr = address.lower().strip()
    # Common abbreviations
    replacements = {
        " street": " st",
        " avenue": " ave",
        " boulevard": " blvd",
        " drive": " dr",
        " road": " rd",
        " lane": " ln",
        " court": " ct",
        " circle": " cir",
        " place": " pl",
    }
    for full, abbr in replacements.items():
        addr = addr.replace(full, abbr)
    # Remove extra whitespace, punctuation
    addr = re.sub(r"[.,#]", "", addr)
    addr = re.sub(r"\s+", " ", addr)
    return addr


def _extract_correlation_key(record: dict[str, Any]) -> str | None:
    """Extract the best correlation key from a raw record.

    Priority: permit_number > normalized address > county+source composite.
    """
    raw = record.get("raw_data", {})

    # Permit number is the strongest correlator
    permit = raw.get("permit_number")
    if permit:
        return f"permit:{permit.strip().upper()}"

    # Address-based correlation
    address = raw.get("address_street") or raw.get("address") or ""
    city = raw.get("address_city") or raw.get("city") or ""
    if address and city:
        normalized = _normalize_address(f"{address} {city}")
        return f"addr:{normalized}"

    # County-level grouping for aggregate records (Census, SODA)
    county = raw.get("county")
    year = raw.get("year")
    month = raw.get("month")
    if county and year:
        key = f"county:{county}:{year}"
        if month:
            key += f":{month}"
        return key

    return None


def correlate_records(records: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    """Group raw records into correlation clusters.

    Returns a dict of {correlation_key: [records]} where each group
    likely represents the same development or data point.
    Records that can't be correlated get their own singleton group.
    """
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    uncorrelated_idx = 0

    for record in records:
        key = _extract_correlation_key(record)
        if key:
            groups[key].append(record)
        else:
            groups[f"_uncorrelated:{uncorrelated_idx}"].append(record)
            uncorrelated_idx += 1

    return dict(groups)
