"""Notification dispatcher — routes leads to configured channels."""

import logging
from typing import Any

from .channels import EmailChannel, NotificationChannel, SlackChannel, WebhookChannel

logger = logging.getLogger(__name__)

CHANNEL_REGISTRY: dict[str, type[NotificationChannel]] = {
    "slack": SlackChannel,
    "webhook": WebhookChannel,
    "email": EmailChannel,
}


def _filter_leads(
    leads: list[dict[str, Any]],
    filters: dict[str, Any] | None,
) -> list[dict[str, Any]]:
    """Apply notification preference filters to leads."""
    if not filters:
        return leads

    filtered = leads

    tier_filter = filters.get("tiers")
    if tier_filter:
        filtered = [l for l in filtered if l.get("tier") in tier_filter]

    county_filter = filters.get("counties")
    if county_filter:
        filtered = [l for l in filtered if l.get("county") in county_filter]

    min_score = filters.get("min_score")
    if min_score is not None:
        filtered = [l for l in filtered if l.get("lead_score", 0) >= min_score]

    return filtered


async def dispatch_notifications(
    leads: list[dict[str, Any]],
    preferences: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Dispatch leads to all configured notification channels.

    Args:
        leads: validated leads to deliver
        preferences: list of notification preference dicts, each with:
            - channel: "slack", "webhook", or "email"
            - config: channel-specific config (webhook_url, email, etc.)
            - filters: optional lead filters (tiers, counties, min_score)
            - is_enabled: bool

    Returns:
        List of delivery result dicts.
    """
    results: list[dict[str, Any]] = []

    for pref in preferences:
        if not pref.get("is_enabled", True):
            continue

        channel_type = pref.get("channel", "")
        channel_cls = CHANNEL_REGISTRY.get(channel_type)
        if channel_cls is None:
            logger.warning("Unknown notification channel: %s", channel_type)
            continue

        # Apply per-preference filters
        filtered = _filter_leads(leads, pref.get("filters"))
        if not filtered:
            continue

        channel = channel_cls()
        try:
            success = await channel.send(filtered, pref.get("config", {}))
            results.append({
                "channel": channel_type,
                "leads_sent": len(filtered),
                "success": success,
            })
        except Exception as e:
            logger.error("Notification failed for %s: %s", channel_type, e)
            results.append({
                "channel": channel_type,
                "leads_sent": 0,
                "success": False,
                "error": str(e),
            })

    return results
