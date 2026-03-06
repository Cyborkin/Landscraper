# Persistent Storage + UI Audit + New Data Sources

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Move lead storage from in-memory list to PostgreSQL, audit all dashboard UI components, and integrate 5 remaining verified data sources.

**Architecture:** Add async CRUD layer between pipeline/API and existing SQLAlchemy models. New Alembic migration relaxes schema constraints. delivery_node writes Development+Lead rows; API reads via joined queries. New scrapers follow the existing BaseScraper pattern and ArcGIS field_map config.

**Tech Stack:** SQLAlchemy 2.0 async, asyncpg, Alembic, PostgreSQL 16, FastAPI, httpx

---

## Part 1: Persistent Storage

### Task 1: Alembic Migration — Relax Schema + Add Columns

**Files:**
- Create: `alembic/versions/<auto>_relax_schema_add_scoring.py`

**Step 1: Generate migration**

```bash
cd /Users/dustinmaselbas/programming/project_hunterd
source .venv/bin/activate
# We need a running postgres — use Docker on swarm1 or local
# For now, write the migration manually
```

Create `alembic/versions/0002_relax_schema_add_scoring.py`:

```python
"""relax schema constraints and add scoring columns

Revision ID: 0002
Revises: 77e8c27216a6
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '0002'
down_revision: Union[str, Sequence[str]] = '77e8c27216a6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Relax NOT NULL constraints on developments
    op.alter_column('developments', 'jurisdiction', nullable=True)
    op.alter_column('developments', 'address_city', nullable=True)
    op.alter_column('developments', 'county', nullable=True)
    op.alter_column('developments', 'permit_type', nullable=True)
    op.alter_column('developments', 'permit_status', nullable=True)
    op.alter_column('developments', 'property_type', nullable=True)

    # Add new columns
    op.add_column('developments', sa.Column(
        'content_hash', sa.String(64), nullable=True, unique=True
    ))
    op.add_column('developments', sa.Column(
        'score_breakdown', postgresql.JSONB(), nullable=True
    ))
    op.add_column('developments', sa.Column(
        'validation_status', sa.String(20), nullable=True
    ))
    op.add_column('developments', sa.Column(
        'lead_score', sa.Integer(), nullable=True
    ))
    op.add_column('developments', sa.Column(
        'tier', sa.String(20), nullable=True
    ))

    op.create_index('ix_developments_content_hash', 'developments', ['content_hash'], unique=True)
    op.create_index('ix_developments_tier', 'developments', ['tier'])


def downgrade() -> None:
    op.drop_index('ix_developments_tier', table_name='developments')
    op.drop_index('ix_developments_content_hash', table_name='developments')
    op.drop_column('developments', 'tier')
    op.drop_column('developments', 'lead_score')
    op.drop_column('developments', 'validation_status')
    op.drop_column('developments', 'score_breakdown')
    op.drop_column('developments', 'content_hash')

    op.alter_column('developments', 'property_type', nullable=False)
    op.alter_column('developments', 'permit_status', nullable=False)
    op.alter_column('developments', 'permit_type', nullable=False)
    op.alter_column('developments', 'county', nullable=False)
    op.alter_column('developments', 'address_city', nullable=False)
    op.alter_column('developments', 'jurisdiction', nullable=False)
```

**Step 2: Update Development model to match**

In `src/landscraper/models/development.py`, add columns and make fields nullable:

```python
# Add these columns to Development class:
content_hash: Mapped[str | None] = mapped_column(String(64), unique=True, index=True)
score_breakdown: Mapped[dict | None] = mapped_column(JSONB)
validation_status: Mapped[str | None] = mapped_column(String(20))
lead_score: Mapped[int | None] = mapped_column(Integer)
tier: Mapped[str | None] = mapped_column(String(20), index=True)

# Change these to nullable:
jurisdiction: Mapped[str | None] = mapped_column(String(255))
address_city: Mapped[str | None] = mapped_column(String(255), index=True)
county: Mapped[str | None] = mapped_column(String(100), index=True)
permit_type: Mapped[str | None] = mapped_column(String(50), index=True)
permit_status: Mapped[str | None] = mapped_column(String(50), index=True)
property_type: Mapped[str | None] = mapped_column(String(50), index=True)
```

**Step 3: Run migration on swarm1**

```bash
ssh swarm@192.168.0.25 'cd /opt/landscraper && docker exec docker-api-1 alembic upgrade head'
```

If the container doesn't have alembic in PATH, run via:
```bash
ssh swarm@192.168.0.25 'docker exec docker-api-1 python -m alembic upgrade head'
```

**Step 4: Commit**

```bash
git add alembic/versions/0002_relax_schema_add_scoring.py src/landscraper/models/development.py
git commit -m "feat: relax development schema constraints, add scoring columns"
```

---

### Task 2: CRUD Layer

**Files:**
- Create: `src/landscraper/db/crud.py`
- Create: `src/landscraper/db/__init__.py`
- Modify: `src/landscraper/db.py` → move to `src/landscraper/db/session.py`

**Step 1: Restructure db module**

Move `src/landscraper/db.py` → `src/landscraper/db/__init__.py` (keep engine + session factory):

```python
# src/landscraper/db/__init__.py
from .session import async_session, engine, get_session

__all__ = ["async_session", "engine", "get_session"]
```

```python
# src/landscraper/db/session.py
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from landscraper.config import settings

engine = create_async_engine(settings.database_url, echo=False)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_session() -> AsyncSession:
    async with async_session() as session:
        yield session
```

**Step 2: Write CRUD functions**

```python
# src/landscraper/db/crud.py
"""CRUD operations for developments and leads."""

import hashlib
import logging
import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from landscraper.models import Development, Lead, Tenant

logger = logging.getLogger(__name__)


def _compute_content_hash(dev: dict[str, Any]) -> str:
    """Generate a content hash for deduplication."""
    parts = [
        dev.get("permit_number", ""),
        dev.get("address_street", ""),
        dev.get("address_city", ""),
        dev.get("county", ""),
        dev.get("sources", [""])[0] if dev.get("sources") else "",
    ]
    key = "|".join(str(p).strip().lower() for p in parts)
    return hashlib.sha256(key.encode()).hexdigest()


def _parse_datetime(val: Any) -> datetime | None:
    """Parse a datetime string or return None."""
    if val is None:
        return None
    if isinstance(val, datetime):
        return val
    try:
        if isinstance(val, str):
            if "T" in val:
                return datetime.fromisoformat(val.replace("Z", "+00:00"))
            return datetime.fromisoformat(val).replace(tzinfo=timezone.utc)
    except (ValueError, TypeError):
        pass
    return None


async def ensure_poc_tenant(session: AsyncSession) -> uuid.UUID:
    """Ensure the POC tenant exists in the database. Return its UUID."""
    from landscraper.api.auth import hash_api_key

    key_hash = hash_api_key("landscraper-poc-key")
    result = await session.execute(
        select(Tenant).where(Tenant.api_key_hash == key_hash)
    )
    tenant = result.scalar_one_or_none()
    if tenant:
        return tenant.id

    tenant = Tenant(
        id=uuid.uuid4(),
        name="POC Tenant",
        api_key_hash=key_hash,
        is_active=True,
    )
    session.add(tenant)
    await session.commit()
    return tenant.id


async def upsert_development(
    session: AsyncSession, dev: dict[str, Any]
) -> Development:
    """Insert or update a development record."""
    content_hash = _compute_content_hash(dev)

    values = {
        "content_hash": content_hash,
        "permit_number": dev.get("permit_number"),
        "permit_type": dev.get("permit_type"),
        "permit_status": dev.get("permit_status"),
        "jurisdiction": dev.get("jurisdiction"),
        "address_street": dev.get("address_street"),
        "address_city": dev.get("address_city"),
        "address_state": dev.get("address_state", "CO"),
        "address_zip": dev.get("address_zip"),
        "county": dev.get("county"),
        "latitude": dev.get("latitude"),
        "longitude": dev.get("longitude"),
        "property_type": dev.get("property_type"),
        "project_name": dev.get("project_name"),
        "description": dev.get("description"),
        "valuation_usd": dev.get("valuation_usd"),
        "unit_count": dev.get("unit_count"),
        "total_sqft": dev.get("total_sqft"),
        "owner_name": dev.get("owner_name"),
        "owner_entity_type": dev.get("owner_entity_type"),
        "contractor_name": dev.get("contractor_name"),
        "filing_date": _parse_datetime(dev.get("filing_date")),
        "confidence_score": dev.get("confidence_score", 0.0),
        "source_count": dev.get("source_count", 1),
        "sources": dev.get("sources", []),
        "discovered_at": datetime.now(timezone.utc),
        "tags": dev.get("tags", []),
        "lead_score": dev.get("lead_score"),
        "tier": dev.get("tier"),
        "score_breakdown": dev.get("score_breakdown"),
        "validation_status": dev.get("validation_status"),
    }

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
            "updated_at": func.now(),
        },
    )
    await session.execute(stmt)

    # Fetch the record back
    result = await session.execute(
        select(Development).where(Development.content_hash == content_hash)
    )
    return result.scalar_one()


async def create_lead_for_development(
    session: AsyncSession,
    development: Development,
    tenant_id: uuid.UUID,
) -> Lead:
    """Create a Lead row linking tenant to development (skip if exists)."""
    result = await session.execute(
        select(Lead).where(
            Lead.tenant_id == tenant_id,
            Lead.development_id == development.id,
        )
    )
    existing = result.scalar_one_or_none()
    if existing:
        # Update score/tier on existing lead
        existing.lead_score = development.lead_score or 0
        existing.tier = development.tier or "cold"
        return existing

    lead = Lead(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        development_id=development.id,
        lead_type="development",
        lead_score=development.lead_score or 0,
        tier=development.tier or "cold",
        status="new",
        delivered_at=datetime.now(timezone.utc),
    )
    session.add(lead)
    return lead


async def store_validated_leads(
    session: AsyncSession,
    leads: list[dict[str, Any]],
    tenant_id: uuid.UUID,
) -> int:
    """Persist a batch of validated leads. Returns count stored."""
    count = 0
    for dev_dict in leads:
        dev = await upsert_development(session, dev_dict)
        await create_lead_for_development(session, dev, tenant_id)
        count += 1
    await session.commit()
    return count


async def list_leads(
    session: AsyncSession,
    tenant_id: uuid.UUID,
    tier: str | None = None,
    property_type: str | None = None,
    county: str | None = None,
    min_score: int = 0,
    page: int = 1,
    page_size: int = 50,
) -> tuple[list[Development], int]:
    """Query developments via leads for a tenant. Returns (items, total_count)."""
    base = (
        select(Development)
        .join(Lead, Lead.development_id == Development.id)
        .where(Lead.tenant_id == tenant_id)
    )

    if tier:
        base = base.where(Development.tier == tier)
    if property_type:
        base = base.where(Development.property_type == property_type)
    if county:
        base = base.where(Development.county == county)
    if min_score > 0:
        base = base.where(Development.lead_score >= min_score)

    # Count
    count_stmt = select(func.count()).select_from(base.subquery())
    total = (await session.execute(count_stmt)).scalar() or 0

    # Page
    stmt = base.order_by(Development.lead_score.desc()).offset(
        (page - 1) * page_size
    ).limit(page_size)
    result = await session.execute(stmt)
    items = list(result.scalars().all())

    return items, total


async def get_lead_by_id(
    session: AsyncSession, lead_id: uuid.UUID, tenant_id: uuid.UUID
) -> Development | None:
    """Get a single development by its lead ID."""
    result = await session.execute(
        select(Development)
        .join(Lead, Lead.development_id == Development.id)
        .where(Lead.id == lead_id, Lead.tenant_id == tenant_id)
    )
    return result.scalar_one_or_none()
```

**Step 3: Commit**

```bash
git add src/landscraper/db/
git commit -m "feat: add CRUD layer for persistent lead storage"
```

---

### Task 3: Persist POC Tenant at Startup

**Files:**
- Modify: `src/landscraper/api/main.py` (lifespan function)

**Step 1: Update lifespan to ensure POC tenant in DB**

In the `lifespan` function, after `register_default_tenant()`, add:

```python
from landscraper.db import async_session
from landscraper.db.crud import ensure_poc_tenant

async with async_session() as session:
    tenant_id = await ensure_poc_tenant(session)
    app.state.poc_tenant_id = tenant_id
    logger.info("POC tenant ensured in DB: %s", tenant_id)
```

**Step 2: Commit**

```bash
git add src/landscraper/api/main.py
git commit -m "feat: persist POC tenant to DB at startup"
```

---

### Task 4: Rewire delivery_node to Write to DB

**Files:**
- Modify: `src/landscraper/agents/nodes.py` (delivery_node function)

**Step 1: Update delivery_node**

Replace the `store_leads(validated)` call with DB persistence:

```python
async def delivery_node(state: LandscraperState) -> dict[str, Any]:
    from landscraper.api.main import update_cycle_status
    from landscraper.db import async_session
    from landscraper.db.crud import ensure_poc_tenant, store_validated_leads
    from .llm import get_llm

    validated = state.get("validated_leads", [])
    cycle_id = state.get("cycle_id", "unknown")

    # Generate LLM summaries for hot/warm leads (existing code stays)
    if validated:
        llm = get_llm("summary")
        hot_warm = [l for l in validated if l.get("tier") in ("hot", "warm")]
        for lead in hot_warm[:10]:
            try:
                # ... existing summary generation code ...
            except Exception as e:
                logger.debug("Lead summary generation failed: %s", e)

        # Persist to database
        async with async_session() as session:
            tenant_id = await ensure_poc_tenant(session)
            count = await store_validated_leads(session, validated, tenant_id)
            logger.info("Persisted %d leads to DB for cycle %s", count, cycle_id)

    update_cycle_status(
        cycle_id=cycle_id,
        status="complete",
        metrics=state.get("cycle_metrics", {}),
    )

    return {
        "current_phase": "complete",
        "messages": [f"Delivered {len(validated)} leads"],
        "errors": [],
    }
```

**Step 2: Remove old store_leads import/call**

Delete `from landscraper.api.main import store_leads` and the `store_leads(validated)` call.

**Step 3: Commit**

```bash
git add src/landscraper/agents/nodes.py
git commit -m "feat: delivery_node persists leads to PostgreSQL"
```

---

### Task 5: Rewire API Endpoints to Query DB

**Files:**
- Modify: `src/landscraper/api/main.py`

**Step 1: Update list_leads endpoint**

Replace the in-memory filtering with DB queries:

```python
from landscraper.db import async_session
from landscraper.db.crud import list_leads as db_list_leads, get_lead_by_id

@app.get("/api/v1/leads", response_model=LeadListResponse)
async def list_leads(
    tenant: Annotated[dict, Depends(verify_api_key)],
    tier: str | None = Query(None),
    property_type: str | None = Query(None),
    county: str | None = Query(None),
    min_score: int = Query(0, ge=0, le=100),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
):
    async with async_session() as session:
        tenant_id = app.state.poc_tenant_id
        items, total = await db_list_leads(
            session, tenant_id, tier, property_type, county, min_score, page, page_size
        )

    leads_out = [_dev_to_lead_out(dev) for dev in items]
    next_url = None
    end = page * page_size
    if end < total:
        next_url = f"/api/v1/leads?page={page + 1}&page_size={page_size}"
        if tier:
            next_url += f"&tier={tier}"

    return LeadListResponse(
        meta=PaginationMeta(total_count=total, page=page, page_size=page_size, next_page_url=next_url),
        leads=leads_out,
    )
```

**Step 2: Update get_lead endpoint**

```python
@app.get("/api/v1/leads/{lead_id}", response_model=LeadOut)
async def get_lead(lead_id: str, tenant: Annotated[dict, Depends(verify_api_key)]):
    import uuid as uuid_mod
    try:
        lid = uuid_mod.UUID(lead_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Lead not found")

    async with async_session() as session:
        dev = await get_lead_by_id(session, lid, app.state.poc_tenant_id)
    if not dev:
        raise HTTPException(status_code=404, detail="Lead not found")
    return _dev_to_lead_out(dev)
```

**Step 3: Write _dev_to_lead_out helper**

```python
def _dev_to_lead_out(dev: Development) -> LeadOut:
    """Convert a Development ORM object to API response."""
    return LeadOut(
        lead_id=str(dev.leads[0].id) if dev.leads else str(dev.id),
        confidence_score=dev.confidence_score or 0.0,
        source_count=dev.source_count or 0,
        sources=dev.sources or [],
        lead_score=dev.lead_score or 0,
        tier=dev.tier or "cold",
        score_breakdown=dev.score_breakdown or {},
        permit_number=dev.permit_number,
        permit_type=dev.permit_type,
        permit_status=dev.permit_status,
        jurisdiction=dev.jurisdiction,
        address=AddressOut(
            street=dev.address_street,
            city=dev.address_city,
            state=dev.address_state,
            zip=dev.address_zip,
            county=dev.county,
        ),
        coordinates=CoordinatesOut(latitude=dev.latitude, longitude=dev.longitude),
        property_type=dev.property_type,
        project_name=dev.project_name,
        description=dev.description,
        valuation_usd=dev.valuation_usd,
        unit_count=dev.unit_count,
        total_sqft=dev.total_sqft,
        owner_name=dev.owner_name,
        filing_date=dev.filing_date.isoformat() if dev.filing_date else None,
        discovered_at=dev.discovered_at.isoformat() if dev.discovered_at else None,
        updated_at=dev.updated_at.isoformat() if dev.updated_at else None,
        tags=dev.tags or [],
        validation_status=dev.validation_status,
    )
```

**Step 4: Remove old in-memory store**

Delete `_leads_store`, `store_leads()`, and the old `_to_lead_out()` function.

**Step 5: Commit**

```bash
git add src/landscraper/api/main.py
git commit -m "feat: API reads leads from PostgreSQL instead of memory"
```

---

### Task 6: Deploy and Verify

**Step 1: Deploy to swarm1**

```bash
tar czf - --exclude='.venv' --exclude='node_modules' --exclude='.git' --exclude='__pycache__' --exclude='dashboard/dist' --exclude='.mypy_cache' --exclude='.pytest_cache' --exclude='.ruff_cache' . | ssh swarm@192.168.0.25 'cd /opt/landscraper && tar xzf -'
ssh swarm@192.168.0.25 'cd /opt/landscraper/docker && docker buildx bake --allow=fs.read=.. -f docker-bake.hcl'
ssh swarm@192.168.0.25 'docker push 192.168.0.25:5000/landscraper:latest'
ssh swarm@192.168.0.25 'cd /opt/landscraper && docker compose -f docker/docker-compose.prod.yml --env-file docker/.env.prod down && docker compose -f docker/docker-compose.prod.yml --env-file docker/.env.prod up -d'
```

**Step 2: Run migration**

```bash
ssh swarm@192.168.0.25 'docker exec docker-api-1 python -m alembic upgrade head'
```

**Step 3: Trigger cycle and verify**

```bash
ssh swarm@192.168.0.25 'curl -s -X POST http://localhost:8000/api/v1/cycle/trigger -H "Authorization: Bearer landscraper-poc-key" -H "Content-Type: application/json" -d "{}"'
# Wait ~2 minutes
ssh swarm@192.168.0.25 'curl -s http://localhost:8000/api/v1/cycle/status -H "Authorization: Bearer landscraper-poc-key"'
# Verify leads persist
ssh swarm@192.168.0.25 'curl -s "http://localhost:8000/api/v1/leads?page_size=5" -H "Authorization: Bearer landscraper-poc-key"'
```

**Step 4: Verify persistence across restart**

```bash
ssh swarm@192.168.0.25 'cd /opt/landscraper && docker compose -f docker/docker-compose.prod.yml --env-file docker/.env.prod restart api'
# Wait 5s
ssh swarm@192.168.0.25 'curl -s "http://localhost:8000/api/v1/leads?page_size=5" -H "Authorization: Bearer landscraper-poc-key"'
# Should still have leads!
```

**Step 5: Commit**

```bash
git add -A
git commit -m "feat: persistent lead storage verified end-to-end"
```

---

## Part 2: UI Audit

### Task 7: Chrome Browser Inspection

Use Chrome browser tools to navigate to `http://192.168.0.25:8000/dashboard` and check:

1. **Dashboard page** (`/dashboard`) — KPI cards, charts render with real data
2. **Lead Explorer** (`/dashboard/leads`) — Table loads, pagination works, map renders
3. **Lead Detail** (`/dashboard/leads/:id`) — Radar chart, detail fields populate
4. **Pipeline Monitor** (`/dashboard/pipeline`) — React Flow graph renders

For each page: screenshot, check console errors, verify data loads from API.

---

## Part 3: Remaining Data Sources (Parallel)

### Task 8: Denver Demolition Permits

**Files:**
- Modify: `src/landscraper/scraping/arcgis_scraper.py` (add to ARCGIS_SOURCES)
- Modify: `src/landscraper/api/main.py` (add to DEFAULT_SOURCES)

Add to ARCGIS_SOURCES:
```python
"denver_demolition_permits": {
    "url": "https://services1.arcgis.com/zdB7qR0BtYrg0Xpl/arcgis/rest/services/ODC_DEV_DEMOLITIONPERMIT_P/FeatureServer/318/query",
    "where": "1=1",
    "fields": "PERMIT_NUM,DATE_ISSUED,ADDRESS,VALUATION,CONTRACTOR_NAME,NEIGHBORHOOD",
    "field_map": {
        "permit_number": "PERMIT_NUM",
        "address_street": "ADDRESS",
        "valuation": "VALUATION",
        "filing_date": "DATE_ISSUED",
        "contractor_name": "CONTRACTOR_NAME",
        "subdivision": "NEIGHBORHOOD",
    },
    "default_permit_status": "issued",
    "city": "Denver",
    "county": "Denver",
},
```

### Task 9: Aurora Active Development Applications

Add to ARCGIS_SOURCES:
```python
"aurora_dev_applications": {
    "url": "https://ags.auroragov.org/aurora/rest/services/OpenData/MapServer/180/query",
    "where": "1=1",
    "fields": "DANum,FolderName,folderdescription,FolderStatus,Address,SiteAcreage,PropNumLots,PropNumDwell,ExistZone,PropZone",
    "field_map": {
        "permit_number": "DANum",
        "permit_type": "FolderName",
        "description": "folderdescription",
        "permit_status": "FolderStatus",
        "address_street": "Address",
        "unit_count": "PropNumDwell",
    },
    "city": "Aurora",
    "county": "Arapahoe",
},
```

### Task 10: FRED Building Permits CSV Scraper

**Files:**
- Create: `src/landscraper/scraping/fred_scraper.py`
- Modify: `src/landscraper/scraping/__init__.py`
- Modify: `src/landscraper/agents/nodes.py` (_build_scraper)
- Modify: `src/landscraper/api/main.py` (DEFAULT_SOURCES)

New scraper that fetches CSV from FRED for Denver-Aurora-Lakewood MSA, Colorado Springs MSA, and Greeley MSA monthly permit counts.

### Task 11: DWR Well Permits Scraper

**Files:**
- Create: `src/landscraper/scraping/dwr_scraper.py`
- Modify: `src/landscraper/scraping/__init__.py`
- Modify: `src/landscraper/agents/nodes.py`
- Modify: `src/landscraper/api/main.py`

REST API scraper for `https://dwr.state.co.us/Rest/GET/api/v2/wellpermits/wellpermit/` filtering for Front Range counties with domestic/residential use.

### Task 12: Legistar OData Scraper

**Files:**
- Create: `src/landscraper/scraping/legistar_scraper.py`
- Modify: `src/landscraper/scraping/__init__.py`
- Modify: `src/landscraper/agents/nodes.py`
- Modify: `src/landscraper/api/main.py`

OData scraper for Denver Land Use committee and Colorado Springs Planning Commission meeting agendas via `https://webapi.legistar.com/v1/{client}/`.

### Task 13: Final Deploy with All Sources

Deploy, trigger cycle, verify all sources produce data.
