import uuid
from datetime import datetime, timezone

import pytest
from sqlalchemy import select

from landscraper.models import (
    AgentRun,
    Builder,
    DataSource,
    Development,
    Lead,
    NotificationPreference,
    RawCollection,
    Tenant,
)


@pytest.mark.asyncio
async def test_create_tenant(session):
    tenant = Tenant(
        name="Test Firm",
        api_key_hash="abc123hash",
        is_active=True,
        contact_email="test@firm.com",
    )
    session.add(tenant)
    await session.flush()

    result = await session.execute(select(Tenant).where(Tenant.name == "Test Firm"))
    loaded = result.scalar_one()
    assert loaded.name == "Test Firm"
    assert loaded.api_key_hash == "abc123hash"
    assert loaded.is_active is True


@pytest.mark.asyncio
async def test_create_data_source(session):
    source = DataSource(
        name="PPRBD El Paso",
        url="https://www.pprbd.org/",
        source_type="permit_portal",
        access_method="public_web",
        scrape_complexity="js_rendered",
        geographic_coverage=["El Paso County", "Colorado Springs"],
        reliability_score=0.9,
        tier="tier_1",
        scrape_frequency_hours=6,
    )
    session.add(source)
    await session.flush()

    result = await session.execute(
        select(DataSource).where(DataSource.name == "PPRBD El Paso")
    )
    loaded = result.scalar_one()
    assert loaded.source_type == "permit_portal"
    assert loaded.reliability_score == 0.9
    assert "El Paso County" in loaded.geographic_coverage


@pytest.mark.asyncio
async def test_create_development(session):
    dev = Development(
        permit_type="new_construction",
        permit_status="applied",
        jurisdiction="City of Thornton, CO",
        address_city="Thornton",
        address_state="CO",
        county="Adams",
        property_type="multifamily",
        project_name="Harvest Ridge",
        valuation_usd=18_500_000.00,
        unit_count=120,
        confidence_score=0.87,
        source_count=3,
        sources=["adams_permits", "planning_agenda", "bizwest"],
        discovered_at=datetime.now(timezone.utc),
    )
    session.add(dev)
    await session.flush()

    result = await session.execute(
        select(Development).where(Development.project_name == "Harvest Ridge")
    )
    loaded = result.scalar_one()
    assert loaded.valuation_usd == 18_500_000.00
    assert loaded.source_count == 3
    assert loaded.county == "Adams"


@pytest.mark.asyncio
async def test_create_lead_with_relationships(session):
    tenant = Tenant(name="Acme Realty", api_key_hash="xyz789hash")
    dev = Development(
        permit_type="new_construction",
        permit_status="issued",
        jurisdiction="Denver",
        address_city="Denver",
        county="Denver",
        property_type="single_family",
        confidence_score=0.95,
        source_count=2,
        sources=["denver_permits", "census_bps"],
        discovered_at=datetime.now(timezone.utc),
    )
    session.add_all([tenant, dev])
    await session.flush()

    lead = Lead(
        tenant_id=tenant.id,
        development_id=dev.id,
        lead_type="development",
        lead_score=85,
        tier="hot",
        status="new",
    )
    session.add(lead)
    await session.flush()

    result = await session.execute(select(Lead).where(Lead.tier == "hot"))
    loaded = result.scalar_one()
    assert loaded.lead_score == 85
    assert loaded.tenant_id == tenant.id
    assert loaded.development_id == dev.id


@pytest.mark.asyncio
async def test_create_agent_run(session):
    run = AgentRun(
        agent_type="collection",
        agent_name="pprbd_scraper",
        task_description="Scrape PPRBD permits for El Paso County",
        status="completed",
        duration_seconds=12.5,
        records_processed=47,
        llm_model_used="mistral",
        llm_tokens_used=1200,
    )
    session.add(run)
    await session.flush()

    result = await session.execute(
        select(AgentRun).where(AgentRun.agent_name == "pprbd_scraper")
    )
    loaded = result.scalar_one()
    assert loaded.records_processed == 47
    assert loaded.status == "completed"


@pytest.mark.asyncio
async def test_create_builder(session):
    builder = Builder(
        company_name="Oakwood Homes LLC",
        entity_type="llc",
        headquarters_city="Denver",
        headquarters_state="CO",
        geographic_regions=["Front Range", "Northern Colorado"],
        active_project_count=12,
        pipeline_value_usd=85_000_000.00,
        confidence_score=0.72,
        source_count=2,
        sources=["colorado_sos", "sec_edgar"],
        discovered_at=datetime.now(timezone.utc),
    )
    session.add(builder)
    await session.flush()

    result = await session.execute(
        select(Builder).where(Builder.company_name == "Oakwood Homes LLC")
    )
    loaded = result.scalar_one()
    assert loaded.pipeline_value_usd == 85_000_000.00
    assert "Front Range" in loaded.geographic_regions
