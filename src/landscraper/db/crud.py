"""CRUD operations for persistent lead/development storage."""

import hashlib
import uuid
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from landscraper.api.auth import hash_api_key
from landscraper.models import Development, Lead, Tenant


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _compute_content_hash(dev: dict) -> str:
    """SHA-256 of normalized permit_number|address_street|address_city|county|first_source."""
    parts = [
        (dev.get("permit_number") or "").strip().lower(),
        (dev.get("address_street") or "").strip().lower(),
        (dev.get("address_city") or "").strip().lower(),
        (dev.get("county") or "").strip().lower(),
        (dev.get("sources", [""])[0] if dev.get("sources") else "").strip().lower(),
    ]
    raw = "|".join(parts)
    return hashlib.sha256(raw.encode()).hexdigest()


def _parse_datetime(val) -> datetime | None:
    """Convert ISO string, epoch-ms int/float, or None to datetime."""
    if val is None:
        return None
    if isinstance(val, datetime):
        return val
    if isinstance(val, (int, float)):
        # Treat as epoch milliseconds
        return datetime.fromtimestamp(val / 1000, tz=timezone.utc)
    if isinstance(val, str):
        # Try ISO format
        cleaned = val.replace("Z", "+00:00")
        try:
            return datetime.fromisoformat(cleaned)
        except ValueError:
            return None
    return None


# ---------------------------------------------------------------------------
# POC tenant
# ---------------------------------------------------------------------------

POC_API_KEY = "landscraper-poc-key"


async def ensure_poc_tenant(session: AsyncSession) -> uuid.UUID:
    """Return the POC tenant UUID, creating the row if it does not exist."""
    key_hash = hash_api_key(POC_API_KEY)

    result = await session.execute(
        select(Tenant).where(Tenant.api_key_hash == key_hash)
    )
    tenant = result.scalar_one_or_none()

    if tenant is not None:
        return tenant.id

    tenant = Tenant(
        name="Landscraper POC",
        api_key_hash=key_hash,
        is_active=True,
    )
    session.add(tenant)
    await session.flush()
    return tenant.id


# ---------------------------------------------------------------------------
# Development upsert
# ---------------------------------------------------------------------------


async def upsert_development(session: AsyncSession, dev: dict) -> Development:
    """INSERT ... ON CONFLICT (content_hash) DO UPDATE for a development dict."""
    content_hash = dev.get("content_hash") or _compute_content_hash(dev)

    now = datetime.now(tz=timezone.utc)
    sources = dev.get("sources") or []

    values = dict(
        content_hash=content_hash,
        permit_number=dev.get("permit_number"),
        permit_type=dev.get("permit_type"),
        permit_status=dev.get("permit_status"),
        jurisdiction=dev.get("jurisdiction"),
        address_street=dev.get("address_street"),
        address_city=dev.get("address_city"),
        address_state=dev.get("address_state", "CO"),
        address_zip=dev.get("address_zip"),
        county=dev.get("county"),
        apn=dev.get("apn"),
        latitude=dev.get("latitude"),
        longitude=dev.get("longitude"),
        zoning_current=dev.get("zoning_current"),
        zoning_proposed=dev.get("zoning_proposed"),
        property_type=dev.get("property_type"),
        project_name=dev.get("project_name"),
        description=dev.get("description"),
        valuation_usd=dev.get("valuation_usd"),
        unit_count=dev.get("unit_count"),
        total_sqft=dev.get("total_sqft"),
        lot_size_acres=dev.get("lot_size_acres"),
        stories=dev.get("stories"),
        owner_name=dev.get("owner_name"),
        owner_entity_type=dev.get("owner_entity_type"),
        owner_phone=dev.get("owner_phone"),
        owner_email=dev.get("owner_email"),
        owner_mailing_address=dev.get("owner_mailing_address"),
        applicant_name=dev.get("applicant_name"),
        applicant_phone=dev.get("applicant_phone"),
        applicant_email=dev.get("applicant_email"),
        contractor_name=dev.get("contractor_name"),
        contractor_license=dev.get("contractor_license"),
        architect_name=dev.get("architect_name"),
        filing_date=_parse_datetime(dev.get("filing_date")),
        approval_date=_parse_datetime(dev.get("approval_date")),
        estimated_start_date=_parse_datetime(dev.get("estimated_start_date")),
        estimated_completion_date=_parse_datetime(dev.get("estimated_completion_date")),
        confidence_score=dev.get("confidence_score", 0.0),
        source_count=dev.get("source_count", len(sources) or 1),
        sources=sources,
        discovered_at=_parse_datetime(dev.get("discovered_at")) or now,
        tags=dev.get("tags"),
        score_breakdown=dev.get("score_breakdown"),
        validation_status=dev.get("validation_status"),
        lead_score=dev.get("lead_score"),
        tier=dev.get("tier"),
    )

    stmt = insert(Development).values(**values)
    stmt = stmt.on_conflict_do_update(
        index_elements=["content_hash"],
        set_={
            "permit_status": stmt.excluded.permit_status,
            "confidence_score": stmt.excluded.confidence_score,
            "source_count": stmt.excluded.source_count,
            "sources": stmt.excluded.sources,
            "lead_score": stmt.excluded.lead_score,
            "tier": stmt.excluded.tier,
            "score_breakdown": stmt.excluded.score_breakdown,
            "validation_status": stmt.excluded.validation_status,
            "updated_at": now,
        },
    ).returning(Development)

    result = await session.execute(stmt)
    return result.scalar_one()


# ---------------------------------------------------------------------------
# Lead creation
# ---------------------------------------------------------------------------


async def create_lead_for_development(
    session: AsyncSession,
    development: Development,
    tenant_id: uuid.UUID,
) -> Lead:
    """Create or update a Lead row for (tenant_id, development_id)."""
    result = await session.execute(
        select(Lead).where(
            Lead.tenant_id == tenant_id,
            Lead.development_id == development.id,
        )
    )
    lead = result.scalar_one_or_none()

    if lead is not None:
        lead.lead_score = development.lead_score or 0
        lead.tier = development.tier or "cold"
        return lead

    lead = Lead(
        tenant_id=tenant_id,
        development_id=development.id,
        lead_type="development",
        lead_score=development.lead_score or 0,
        tier=development.tier or "cold",
        status="new",
    )
    session.add(lead)
    return lead


# ---------------------------------------------------------------------------
# Batch store
# ---------------------------------------------------------------------------


async def store_validated_leads(
    session: AsyncSession,
    leads: list[dict],
    tenant_id: uuid.UUID,
) -> int:
    """Upsert developments and create leads for each. Return count stored."""
    count = 0
    for dev_dict in leads:
        development = await upsert_development(session, dev_dict)
        await create_lead_for_development(session, development, tenant_id)
        count += 1
    await session.commit()
    return count


# ---------------------------------------------------------------------------
# Queries
# ---------------------------------------------------------------------------


async def list_leads(
    session: AsyncSession,
    tenant_id: uuid.UUID,
    *,
    tier: str | None = None,
    property_type: str | None = None,
    county: str | None = None,
    min_score: int = 0,
    page: int = 1,
    page_size: int = 50,
) -> tuple[list[Development], int]:
    """Query developments joined with leads, apply filters, paginate.

    Returns (page_items, total_count). Ordered by lead_score DESC.
    """
    base = (
        select(Development)
        .join(Lead, Lead.development_id == Development.id)
        .where(Lead.tenant_id == tenant_id)
    )

    if tier is not None:
        base = base.where(Development.tier == tier)
    if property_type is not None:
        base = base.where(Development.property_type == property_type)
    if county is not None:
        base = base.where(Development.county == county)
    if min_score > 0:
        base = base.where(Development.lead_score >= min_score)

    # Total count
    count_stmt = select(func.count()).select_from(base.subquery())
    total = (await session.execute(count_stmt)).scalar_one()

    # Page
    offset = (page - 1) * page_size
    page_stmt = (
        base.order_by(Development.lead_score.desc().nulls_last())
        .offset(offset)
        .limit(page_size)
    )
    rows = (await session.execute(page_stmt)).scalars().all()

    return list(rows), total


async def get_lead_by_id(
    session: AsyncSession,
    lead_id: uuid.UUID,
    tenant_id: uuid.UUID,
) -> Development | None:
    """Get a single development by its Lead UUID, scoped to tenant."""
    result = await session.execute(
        select(Development)
        .join(Lead, Lead.development_id == Development.id)
        .where(Lead.id == lead_id, Lead.tenant_id == tenant_id)
    )
    return result.scalar_one_or_none()
