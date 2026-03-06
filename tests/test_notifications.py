"""Tests for notification channels and dispatcher."""

import pytest
import respx
from httpx import Response

from landscraper.notifications.channels import EmailChannel, SlackChannel, WebhookChannel
from landscraper.notifications.dispatcher import dispatch_notifications, _filter_leads

SAMPLE_LEADS = [
    {
        "lead_id": "lead-1",
        "tier": "hot",
        "lead_score": 85,
        "county": "Denver",
        "address_city": "Denver",
        "permit_number": "BLD-001",
        "project_name": "Test Project",
    },
    {
        "lead_id": "lead-2",
        "tier": "warm",
        "lead_score": 60,
        "county": "Boulder",
        "address_city": "Boulder",
        "permit_number": "BLD-002",
    },
    {
        "lead_id": "lead-3",
        "tier": "monitor",
        "lead_score": 35,
        "county": "Adams",
        "address_city": "Thornton",
    },
]


# --- Slack ---


@respx.mock
@pytest.mark.asyncio
async def test_slack_channel():
    respx.post("https://hooks.slack.com/test").mock(return_value=Response(200, text="ok"))

    channel = SlackChannel()
    result = await channel.send(SAMPLE_LEADS, {"webhook_url": "https://hooks.slack.com/test"})
    assert result is True


@respx.mock
@pytest.mark.asyncio
async def test_slack_channel_failure():
    respx.post("https://hooks.slack.com/test").mock(return_value=Response(500))

    channel = SlackChannel()
    result = await channel.send(SAMPLE_LEADS, {"webhook_url": "https://hooks.slack.com/test"})
    assert result is False


@pytest.mark.asyncio
async def test_slack_no_url():
    channel = SlackChannel()
    result = await channel.send(SAMPLE_LEADS, {})
    assert result is False


# --- Webhook ---


@respx.mock
@pytest.mark.asyncio
async def test_webhook_channel():
    respx.post("https://example.com/webhook").mock(return_value=Response(200))

    channel = WebhookChannel()
    result = await channel.send(
        SAMPLE_LEADS,
        {"webhook_url": "https://example.com/webhook", "secret": "mysecret"},
    )
    assert result is True

    # Verify HMAC signature was sent
    request = respx.calls[0].request
    assert "X-Landscraper-Signature" in request.headers
    assert len(request.headers["X-Landscraper-Signature"]) == 64  # SHA-256 hex


@respx.mock
@pytest.mark.asyncio
async def test_webhook_failure():
    respx.post("https://example.com/webhook").mock(return_value=Response(500))

    channel = WebhookChannel()
    result = await channel.send(SAMPLE_LEADS, {"webhook_url": "https://example.com/webhook"})
    assert result is False


# --- Email ---


@pytest.mark.asyncio
async def test_email_channel():
    channel = EmailChannel()
    result = await channel.send(SAMPLE_LEADS, {"email": "test@example.com"})
    assert result is True  # POC: always succeeds (logs only)


@pytest.mark.asyncio
async def test_email_no_recipient():
    channel = EmailChannel()
    result = await channel.send(SAMPLE_LEADS, {})
    assert result is False


# --- Filters ---


def test_filter_by_tier():
    filtered = _filter_leads(SAMPLE_LEADS, {"tiers": ["hot"]})
    assert len(filtered) == 1
    assert filtered[0]["tier"] == "hot"


def test_filter_by_county():
    filtered = _filter_leads(SAMPLE_LEADS, {"counties": ["Denver", "Boulder"]})
    assert len(filtered) == 2


def test_filter_by_min_score():
    filtered = _filter_leads(SAMPLE_LEADS, {"min_score": 50})
    assert len(filtered) == 2


def test_filter_no_filters():
    filtered = _filter_leads(SAMPLE_LEADS, None)
    assert len(filtered) == 3


def test_filter_combined():
    filtered = _filter_leads(SAMPLE_LEADS, {"tiers": ["hot", "warm"], "min_score": 70})
    assert len(filtered) == 1
    assert filtered[0]["lead_id"] == "lead-1"


# --- Dispatcher ---


@respx.mock
@pytest.mark.asyncio
async def test_dispatch_to_slack():
    respx.post("https://hooks.slack.com/test").mock(return_value=Response(200, text="ok"))

    prefs = [{
        "channel": "slack",
        "config": {"webhook_url": "https://hooks.slack.com/test"},
        "is_enabled": True,
    }]

    results = await dispatch_notifications(SAMPLE_LEADS, prefs)
    assert len(results) == 1
    assert results[0]["success"] is True
    assert results[0]["leads_sent"] == 3


@pytest.mark.asyncio
async def test_dispatch_disabled_channel():
    prefs = [{
        "channel": "email",
        "config": {"email": "test@example.com"},
        "is_enabled": False,
    }]

    results = await dispatch_notifications(SAMPLE_LEADS, prefs)
    assert len(results) == 0  # disabled channels skipped


@pytest.mark.asyncio
async def test_dispatch_with_filters():
    prefs = [{
        "channel": "email",
        "config": {"email": "test@example.com"},
        "filters": {"tiers": ["hot"]},
        "is_enabled": True,
    }]

    results = await dispatch_notifications(SAMPLE_LEADS, prefs)
    assert len(results) == 1
    assert results[0]["leads_sent"] == 1


@pytest.mark.asyncio
async def test_dispatch_unknown_channel():
    prefs = [{"channel": "carrier_pigeon", "config": {}, "is_enabled": True}]
    results = await dispatch_notifications(SAMPLE_LEADS, prefs)
    assert len(results) == 0
