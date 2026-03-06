"""Tests for the FastAPI REST API."""

import uuid
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from landscraper.api.main import app
from landscraper.api.tenant_registry import register_default_tenant


POC_TENANT_ID = uuid.uuid4()


def _make_dev(**overrides):
    """Build a fake Development object with sensible defaults."""
    defaults = dict(
        id=uuid.uuid4(),
        permit_number=None,
        permit_type=None,
        permit_status=None,
        jurisdiction=None,
        address_street=None,
        address_city=None,
        address_state="CO",
        address_zip=None,
        county=None,
        latitude=None,
        longitude=None,
        property_type=None,
        project_name=None,
        description=None,
        valuation_usd=None,
        unit_count=None,
        total_sqft=None,
        owner_name=None,
        confidence_score=0.0,
        source_count=1,
        sources=[],
        filing_date=None,
        discovered_at=datetime.now(tz=timezone.utc),
        updated_at=None,
        tags=[],
        score_breakdown={},
        validation_status=None,
        lead_score=0,
        tier="cold",
    )
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


def _make_lead(dev, **overrides):
    """Build a fake Lead object linked to a development."""
    defaults = dict(
        id=uuid.uuid4(),
        tenant_id=POC_TENANT_ID,
        development_id=dev.id,
        lead_type="development",
        lead_score=dev.lead_score,
        tier=dev.tier,
        status="new",
    )
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


def _mock_session():
    """Create mock async session context manager."""
    mock_factory = AsyncMock()
    mock_session = AsyncMock()
    mock_factory.return_value.__aenter__ = AsyncMock(return_value=mock_session)
    mock_factory.return_value.__aexit__ = AsyncMock(return_value=False)
    return mock_factory


@pytest.fixture(autouse=True)
def setup_api():
    """Register default tenant."""
    register_default_tenant()
    yield


client = TestClient(app)

AUTH_HEADER = {"Authorization": "Bearer landscraper-poc-key"}


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["version"] == "0.1.0"


def test_list_leads_unauthorized():
    response = client.get("/api/v1/leads")
    assert response.status_code == 401  # no auth header


def test_list_leads_bad_key():
    response = client.get("/api/v1/leads", headers={"Authorization": "Bearer wrong-key"})
    assert response.status_code == 401


@patch("landscraper.api.main.db_list_leads", new_callable=AsyncMock)
@patch("landscraper.api.main.ensure_poc_tenant", new_callable=AsyncMock, return_value=POC_TENANT_ID)
@patch("landscraper.api.main.async_session")
def test_list_leads_empty(mock_session_factory, mock_tenant, mock_list):
    mock_session_factory.return_value.__aenter__ = AsyncMock(return_value=AsyncMock())
    mock_session_factory.return_value.__aexit__ = AsyncMock(return_value=False)
    mock_list.return_value = ([], 0)

    response = client.get("/api/v1/leads", headers=AUTH_HEADER)
    assert response.status_code == 200
    data = response.json()
    assert data["meta"]["total_count"] == 0
    assert data["leads"] == []


@patch("landscraper.api.main.db_list_leads", new_callable=AsyncMock)
@patch("landscraper.api.main.ensure_poc_tenant", new_callable=AsyncMock, return_value=POC_TENANT_ID)
@patch("landscraper.api.main.async_session")
def test_list_leads_with_data(mock_session_factory, mock_tenant, mock_list):
    mock_session_factory.return_value.__aenter__ = AsyncMock(return_value=AsyncMock())
    mock_session_factory.return_value.__aexit__ = AsyncMock(return_value=False)

    dev1 = _make_dev(permit_number="BLD-001", address_city="Denver", county="Denver",
                     lead_score=75, tier="warm", property_type="multifamily",
                     confidence_score=0.8, source_count=2, sources=["src_a", "src_b"])
    dev2 = _make_dev(permit_number="BLD-002", address_city="Boulder", county="Boulder",
                     lead_score=45, tier="monitor", property_type="single_family",
                     confidence_score=0.5, source_count=1, sources=["src_a"])
    lead1 = _make_lead(dev1)
    lead2 = _make_lead(dev2)
    mock_list.return_value = ([(dev1, lead1), (dev2, lead2)], 2)

    response = client.get("/api/v1/leads", headers=AUTH_HEADER)
    assert response.status_code == 200
    data = response.json()
    assert data["meta"]["total_count"] == 2
    assert len(data["leads"]) == 2


@patch("landscraper.api.main.db_list_leads", new_callable=AsyncMock)
@patch("landscraper.api.main.ensure_poc_tenant", new_callable=AsyncMock, return_value=POC_TENANT_ID)
@patch("landscraper.api.main.async_session")
def test_list_leads_filter_tier(mock_session_factory, mock_tenant, mock_list):
    mock_session_factory.return_value.__aenter__ = AsyncMock(return_value=AsyncMock())
    mock_session_factory.return_value.__aexit__ = AsyncMock(return_value=False)

    dev = _make_dev(tier="hot", lead_score=85)
    lead = _make_lead(dev)
    mock_list.return_value = ([(dev, lead)], 1)

    response = client.get("/api/v1/leads?tier=hot", headers=AUTH_HEADER)
    data = response.json()
    assert data["meta"]["total_count"] == 1
    assert data["leads"][0]["tier"] == "hot"


@patch("landscraper.api.main.db_list_leads", new_callable=AsyncMock)
@patch("landscraper.api.main.ensure_poc_tenant", new_callable=AsyncMock, return_value=POC_TENANT_ID)
@patch("landscraper.api.main.async_session")
def test_list_leads_filter_county(mock_session_factory, mock_tenant, mock_list):
    mock_session_factory.return_value.__aenter__ = AsyncMock(return_value=AsyncMock())
    mock_session_factory.return_value.__aexit__ = AsyncMock(return_value=False)

    dev = _make_dev(county="Denver", tier="warm")
    lead = _make_lead(dev)
    mock_list.return_value = ([(dev, lead)], 1)

    response = client.get("/api/v1/leads?county=Denver", headers=AUTH_HEADER)
    data = response.json()
    assert data["meta"]["total_count"] == 1


@patch("landscraper.api.main.db_list_leads", new_callable=AsyncMock)
@patch("landscraper.api.main.ensure_poc_tenant", new_callable=AsyncMock, return_value=POC_TENANT_ID)
@patch("landscraper.api.main.async_session")
def test_list_leads_min_score(mock_session_factory, mock_tenant, mock_list):
    mock_session_factory.return_value.__aenter__ = AsyncMock(return_value=AsyncMock())
    mock_session_factory.return_value.__aexit__ = AsyncMock(return_value=False)

    lead_id = uuid.uuid4()
    dev = _make_dev(lead_score=80, tier="hot")
    lead = _make_lead(dev, id=lead_id)
    mock_list.return_value = ([(dev, lead)], 1)

    response = client.get("/api/v1/leads?min_score=50", headers=AUTH_HEADER)
    data = response.json()
    assert data["meta"]["total_count"] == 1
    assert data["leads"][0]["lead_id"] == str(lead_id)


@patch("landscraper.api.main.db_list_leads", new_callable=AsyncMock)
@patch("landscraper.api.main.ensure_poc_tenant", new_callable=AsyncMock, return_value=POC_TENANT_ID)
@patch("landscraper.api.main.async_session")
def test_list_leads_pagination(mock_session_factory, mock_tenant, mock_list):
    mock_session_factory.return_value.__aenter__ = AsyncMock(return_value=AsyncMock())
    mock_session_factory.return_value.__aexit__ = AsyncMock(return_value=False)

    items = []
    for i in range(2):
        dev = _make_dev(tier="warm")
        lead = _make_lead(dev)
        items.append((dev, lead))
    mock_list.return_value = (items, 5)

    response = client.get("/api/v1/leads?page=1&page_size=2", headers=AUTH_HEADER)
    data = response.json()
    assert data["meta"]["total_count"] == 5
    assert len(data["leads"]) == 2
    assert data["meta"]["next_page_url"] is not None


@patch("landscraper.api.main.get_lead_by_id", new_callable=AsyncMock)
@patch("landscraper.api.main.ensure_poc_tenant", new_callable=AsyncMock, return_value=POC_TENANT_ID)
@patch("landscraper.api.main.async_session")
def test_get_lead(mock_session_factory, mock_tenant, mock_get):
    mock_session_factory.return_value.__aenter__ = AsyncMock(return_value=AsyncMock())
    mock_session_factory.return_value.__aexit__ = AsyncMock(return_value=False)

    lead_id = uuid.uuid4()
    dev = _make_dev(tier="hot", permit_number="BLD-X")
    lead = _make_lead(dev, id=lead_id)
    mock_get.return_value = (dev, lead)

    response = client.get(f"/api/v1/leads/{lead_id}", headers=AUTH_HEADER)
    assert response.status_code == 200
    data = response.json()
    assert data["lead_id"] == str(lead_id)
    assert data["permit_number"] == "BLD-X"


@patch("landscraper.api.main.get_lead_by_id", new_callable=AsyncMock)
@patch("landscraper.api.main.ensure_poc_tenant", new_callable=AsyncMock, return_value=POC_TENANT_ID)
@patch("landscraper.api.main.async_session")
def test_get_lead_not_found(mock_session_factory, mock_tenant, mock_get):
    mock_session_factory.return_value.__aenter__ = AsyncMock(return_value=AsyncMock())
    mock_session_factory.return_value.__aexit__ = AsyncMock(return_value=False)
    mock_get.return_value = None

    fake_id = uuid.uuid4()
    response = client.get(f"/api/v1/leads/{fake_id}", headers=AUTH_HEADER)
    assert response.status_code == 404


def test_cycle_status():
    response = client.get("/api/v1/cycle/status", headers=AUTH_HEADER)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ("idle", "triggered", "complete", "running")


def test_trigger_cycle():
    response = client.post(
        "/api/v1/cycle/trigger",
        headers=AUTH_HEADER,
        json={"sources": None},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "running"
    assert data["cycle_id"] is not None


@patch("landscraper.api.main.get_lead_by_id", new_callable=AsyncMock)
@patch("landscraper.api.main.ensure_poc_tenant", new_callable=AsyncMock, return_value=POC_TENANT_ID)
@patch("landscraper.api.main.async_session")
def test_lead_response_structure(mock_session_factory, mock_tenant, mock_get):
    """Verify the lead response includes nested address and coordinates."""
    mock_session_factory.return_value.__aenter__ = AsyncMock(return_value=AsyncMock())
    mock_session_factory.return_value.__aexit__ = AsyncMock(return_value=False)

    lead_id = uuid.uuid4()
    dev = _make_dev(
        address_street="100 Main St",
        address_city="Denver",
        address_state="CO",
        address_zip="80202",
        county="Denver",
        latitude=39.7392,
        longitude=-104.9903,
        tier="hot",
    )
    lead = _make_lead(dev, id=lead_id)
    mock_get.return_value = (dev, lead)

    response = client.get(f"/api/v1/leads/{lead_id}", headers=AUTH_HEADER)
    data = response.json()

    assert data["address"]["street"] == "100 Main St"
    assert data["address"]["city"] == "Denver"
    assert data["address"]["county"] == "Denver"
    assert data["coordinates"]["latitude"] == 39.7392


@patch("landscraper.api.main.get_lead_by_id", new_callable=AsyncMock)
@patch("landscraper.api.main.ensure_poc_tenant", new_callable=AsyncMock, return_value=POC_TENANT_ID)
@patch("landscraper.api.main.async_session")
def test_lead_includes_score_breakdown(mock_session_factory, mock_tenant, mock_get):
    mock_session_factory.return_value.__aenter__ = AsyncMock(return_value=AsyncMock())
    mock_session_factory.return_value.__aexit__ = AsyncMock(return_value=False)

    lead_id = uuid.uuid4()
    dev = _make_dev(
        tier="hot",
        lead_score=85,
        score_breakdown={"project_scale": 20, "permit_status": 15, "unit_count": 10},
    )
    lead = _make_lead(dev, id=lead_id)
    mock_get.return_value = (dev, lead)

    response = client.get(f"/api/v1/leads/{lead_id}", headers=AUTH_HEADER)
    data = response.json()
    assert data["score_breakdown"]["project_scale"] == 20
    assert data["score_breakdown"]["permit_status"] == 15


def test_tracing_status():
    response = client.get("/api/v1/tracing/status", headers=AUTH_HEADER)
    assert response.status_code == 200
    data = response.json()
    assert "enabled" in data
    assert isinstance(data["enabled"], bool)
