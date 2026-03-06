"""Deduplicate raw collection records by content hash."""

from typing import Any


def deduplicate(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Remove duplicate raw records based on content_hash.

    Keeps the first occurrence of each unique content hash.
    """
    seen: set[str] = set()
    unique: list[dict[str, Any]] = []

    for record in records:
        content_hash = record.get("content_hash", "")
        if content_hash and content_hash in seen:
            continue
        if content_hash:
            seen.add(content_hash)
        unique.append(record)

    return unique
