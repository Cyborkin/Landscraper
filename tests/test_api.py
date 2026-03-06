"""Tests for the FastAPI REST API."""

import pytest
from fastapi.testclient import TestClient

from landscraper.api.main import app, _leads_store, store_leads
from landscraper.api.tenant_registry import register_default_tenant


@pytest.fixture(autouse=True)
def setup_api():
    """Register default tenant and clear leads store before each test."""
    register_default_tenant()
    _leads_store.clear()
    yield
    _leads_store.clear()


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


def test_list_leads_empty():
    response = client.get("/api/v1/leads", headers=AUTH_HEADER)
    assert response.status_code == 200
    data = response.json()
    assert data["meta"]["total_count"] == 0
    assert data["leads"] == []


def test_list_leads_with_data():
    store_leads([
        {
            "lead_id": "test-lead-1",
            "permit_number": "BLD-001",
            "address_city": "Denver",
            "county": "Denver",
            "lead_score": 75,
            "tier": "warm",
            "property_type": "multifamily",
            "confidence_score": 0.8,
            "source_count": 2,
            "sources": ["src_a", "src_b"],
        },
        {
            "lead_id": "test-lead-2",
            "permit_number": "BLD-002",
            "address_city": "Boulder",
            "county": "Boulder",
            "lead_score": 45,
            "tier": "monitor",
            "property_type": "single_family",
            "confidence_score": 0.5,
            "source_count": 1,
            "sources": ["src_a"],
        },
    ])

    response = client.get("/api/v1/leads", headers=AUTH_HEADER)
    assert response.status_code == 200
    data = response.json()
    assert data["meta"]["total_count"] == 2
    assert len(data["leads"]) == 2


def test_list_leads_filter_tier():
    store_leads([
        {"lead_id": "hot-1", "tier": "hot", "lead_score": 85},
        {"lead_id": "warm-1", "tier": "warm", "lead_score": 60},
    ])

    response = client.get("/api/v1/leads?tier=hot", headers=AUTH_HEADER)
    data = response.json()
    assert data["meta"]["total_count"] == 1
    assert data["leads"][0]["tier"] == "hot"


def test_list_leads_filter_county():
    store_leads([
        {"lead_id": "d1", "county": "Denver", "tier": "warm"},
        {"lead_id": "b1", "county": "Boulder", "tier": "warm"},
    ])

    response = client.get("/api/v1/leads?county=Denver", headers=AUTH_HEADER)
    data = response.json()
    assert data["meta"]["total_count"] == 1


def test_list_leads_min_score():
    store_leads([
        {"lead_id": "high", "lead_score": 80, "tier": "hot"},
        {"lead_id": "low", "lead_score": 30, "tier": "monitor"},
    ])

    response = client.get("/api/v1/leads?min_score=50", headers=AUTH_HEADER)
    data = response.json()
    assert data["meta"]["total_count"] == 1
    assert data["leads"][0]["lead_id"] == "high"


def test_list_leads_pagination():
    store_leads([{"lead_id": f"lead-{i}", "tier": "warm"} for i in range(5)])

    response = client.get("/api/v1/leads?page=1&page_size=2", headers=AUTH_HEADER)
    data = response.json()
    assert data["meta"]["total_count"] == 5
    assert len(data["leads"]) == 2
    assert data["meta"]["next_page_url"] is not None


def test_get_lead():
    store_leads([{"lead_id": "find-me", "tier": "hot", "permit_number": "BLD-X"}])

    response = client.get("/api/v1/leads/find-me", headers=AUTH_HEADER)
    assert response.status_code == 200
    data = response.json()
    assert data["lead_id"] == "find-me"
    assert data["permit_number"] == "BLD-X"


def test_get_lead_not_found():
    response = client.get("/api/v1/leads/nonexistent", headers=AUTH_HEADER)
    assert response.status_code == 404


def test_cycle_status():
    response = client.get("/api/v1/cycle/status", headers=AUTH_HEADER)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ("idle", "triggered", "complete")


def test_trigger_cycle():
    response = client.post(
        "/api/v1/cycle/trigger",
        headers=AUTH_HEADER,
        json={"sources": None},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "triggered"
    assert data["cycle_id"] is not None


def test_lead_response_structure():
    """Verify the lead response includes nested address and coordinates."""
    store_leads([{
        "lead_id": "struct-test",
        "address_street": "100 Main St",
        "address_city": "Denver",
        "address_state": "CO",
        "address_zip": "80202",
        "county": "Denver",
        "latitude": 39.7392,
        "longitude": -104.9903,
        "tier": "hot",
    }])

    response = client.get("/api/v1/leads/struct-test", headers=AUTH_HEADER)
    data = response.json()

    assert data["address"]["street"] == "100 Main St"
    assert data["address"]["city"] == "Denver"
    assert data["address"]["county"] == "Denver"
    assert data["coordinates"]["latitude"] == 39.7392
