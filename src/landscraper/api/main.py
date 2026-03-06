"""FastAPI application entry point."""

import asyncio
import logging
import os
import uuid
from contextlib import asynccontextmanager
from typing import Annotated, Any

from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse

from landscraper.api.auth import verify_api_key
from landscraper.api.schemas import (
    AddressOut,
    CoordinatesOut,
    CycleStatusResponse,
    HealthResponse,
    LeadListResponse,
    LeadOut,
    PaginationMeta,
    TracingStatusResponse,
    TriggerCycleRequest,
)
from landscraper.api.tenant_registry import register_default_tenant
from landscraper.db import async_session
from landscraper.db.crud import ensure_poc_tenant, get_lead_by_id
from landscraper.db.crud import list_leads as db_list_leads
from landscraper.models.development import Development
from landscraper.models.lead import Lead

logger = logging.getLogger(__name__)

_last_cycle: dict[str, Any] = {"cycle_id": None, "status": "idle", "metrics": {}}


@asynccontextmanager
async def lifespan(app: FastAPI):
    from landscraper.tracing import configure_tracing

    register_default_tenant()
    tracing = configure_tracing()
    if tracing:
        logger.info(
            "LangSmith tracing enabled (project: %s)",
            os.environ.get("LANGCHAIN_PROJECT", "default"),
        )

    # Ensure POC tenant exists in database
    from landscraper.db import async_session
    from landscraper.db.crud import ensure_poc_tenant

    async with async_session() as session:
        tenant_id = await ensure_poc_tenant(session)
        app.state.poc_tenant_id = tenant_id
        logger.info("POC tenant ensured in DB: %s", tenant_id)

    yield


app = FastAPI(
    title="Landscraper API",
    description="Development lead intelligence for Colorado's Front Range",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://192.168.0.25:8000", "http://localhost:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", include_in_schema=False)
async def root_redirect():
    return RedirectResponse(url="/dashboard")


@app.get("/health", response_model=HealthResponse)
async def health():
    return HealthResponse(status="ok", version="0.1.0")


@app.get("/api/v1/leads", response_model=LeadListResponse)
async def list_leads(
    tenant: Annotated[dict, Depends(verify_api_key)],
    tier: str | None = Query(None, description="Filter by tier: hot, warm, monitor, cold"),
    property_type: str | None = Query(None, description="Filter by property type"),
    county: str | None = Query(None, description="Filter by county"),
    min_score: int = Query(0, ge=0, le=100, description="Minimum lead score"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=200, description="Results per page"),
):
    """List development leads with optional filters."""
    async with async_session() as session:
        tenant_id = await ensure_poc_tenant(session)
        items, total = await db_list_leads(
            session,
            tenant_id,
            tier=tier,
            property_type=property_type,
            county=county,
            min_score=min_score,
            page=page,
            page_size=page_size,
        )
        leads_out = [_dev_to_lead_out(dev, lead) for dev, lead in items]

    end = page * page_size
    next_url = None
    if end < total:
        next_url = f"/api/v1/leads?page={page + 1}&page_size={page_size}"
        if tier:
            next_url += f"&tier={tier}"

    return LeadListResponse(
        meta=PaginationMeta(
            total_count=total,
            page=page,
            page_size=page_size,
            next_page_url=next_url,
        ),
        leads=leads_out,
    )


@app.get("/api/v1/leads/{lead_id}", response_model=LeadOut)
async def get_lead(
    lead_id: str,
    tenant: Annotated[dict, Depends(verify_api_key)],
):
    """Get a single lead by ID."""
    async with async_session() as session:
        tenant_id = await ensure_poc_tenant(session)
        result = await get_lead_by_id(session, uuid.UUID(lead_id), tenant_id)
        if result is None:
            raise HTTPException(status_code=404, detail="Lead not found")
        dev, lead = result
        return _dev_to_lead_out(dev, lead)


@app.get("/api/v1/cycle/status", response_model=CycleStatusResponse)
async def cycle_status(
    tenant: Annotated[dict, Depends(verify_api_key)],
):
    """Get the status of the last cycle."""
    return CycleStatusResponse(**_last_cycle)


DEFAULT_SOURCES = [
    {"name": "colorado_soda_permits", "access_method": "api"},
    {"name": "census_bps", "access_method": "api"},
    {"name": "dola_demography", "access_method": "api"},
    {"name": "sec_edgar", "access_method": "api"},
    {"name": "fort_collins_permits", "access_method": "api"},
    {"name": "aurora_permits", "access_method": "api"},
    {"name": "denver_residential_permits", "access_method": "api"},
    {"name": "denver_rezoning", "access_method": "api"},
    {
        "name": "bizwest_rss",
        "access_method": "rss",
        "url": "https://bizwest.com/category/real-estate-construction/feed/",
        "keywords": ["permit", "development", "construction", "residential", "commercial"],
    },
    {
        "name": "denver_post_real_estate_rss",
        "access_method": "rss",
        "url": "https://www.denverpost.com/tag/real-estate/feed/",
        "keywords": ["development", "construction", "permit", "residential", "building", "housing"],
    },
    {
        "name": "denverinfill_rss",
        "access_method": "rss",
        "url": "https://denverinfill.com/feed",
        "keywords": ["development", "construction", "residential", "project", "proposed", "approved"],
    },
]


@app.post("/api/v1/cycle/trigger", response_model=CycleStatusResponse)
async def trigger_cycle(
    body: TriggerCycleRequest,
    background_tasks: BackgroundTasks,
    tenant: Annotated[dict, Depends(verify_api_key)],
):
    """Trigger a new data collection cycle."""
    if _last_cycle.get("status") == "running":
        return CycleStatusResponse(**_last_cycle)

    cycle_id = str(uuid.uuid4())
    sources = body.sources or DEFAULT_SOURCES
    _last_cycle.update({
        "cycle_id": cycle_id,
        "status": "running",
        "metrics": {},
    })

    background_tasks.add_task(_run_cycle, cycle_id, sources)
    return CycleStatusResponse(**_last_cycle)


async def _run_cycle(cycle_id: str, sources: list[dict[str, Any]]) -> None:
    """Execute the agent graph in the background."""
    from landscraper.agents.orchestrator import compile_graph
    from landscraper.tracing import cycle_run_config

    run_config = cycle_run_config(cycle_id)
    graph = compile_graph()

    initial_state = {
        "messages": [],
        "current_phase": "discovery",
        "cycle_id": cycle_id,
        "active_sources": sources,
        "raw_data": [],
        "developments": [],
        "builders": [],
        "validated_leads": [],
        "cycle_metrics": {},
        "errors": [],
    }

    try:
        logger.info("Cycle %s: starting with %d sources", cycle_id, len(sources))
        result = await graph.ainvoke(initial_state, config=run_config)
        logger.info(
            "Cycle %s: complete — %d leads delivered",
            cycle_id,
            len(result.get("validated_leads", [])),
        )
    except Exception as e:
        logger.error("Cycle %s: failed — %s", cycle_id, e, exc_info=True)
        _last_cycle.update({
            "cycle_id": cycle_id,
            "status": "error",
            "metrics": {"error": str(e)},
        })


@app.get("/api/v1/tracing/status", response_model=TracingStatusResponse)
async def tracing_status(
    tenant: Annotated[dict, Depends(verify_api_key)],
):
    """Check if LangSmith tracing is active."""
    from landscraper.tracing import tracing_is_enabled

    return TracingStatusResponse(
        enabled=tracing_is_enabled(),
        project=os.environ.get("LANGCHAIN_PROJECT"),
    )


def update_cycle_status(cycle_id: str, status: str, metrics: dict | None = None) -> None:
    """Update cycle status (called by graph nodes)."""
    _last_cycle.update({
        "cycle_id": cycle_id,
        "status": status,
        "metrics": metrics or {},
    })


# Serve dashboard SPA if build exists
_dashboard_candidates = [
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "dashboard", "dist"),  # dev (source tree)
    os.path.join(os.getcwd(), "dashboard", "dist"),  # container (WORKDIR /app)
]
_dashboard_dir = next((d for d in _dashboard_candidates if os.path.isdir(d)), None)
if _dashboard_dir:
    from fastapi.staticfiles import StaticFiles

    app.mount("/dashboard", StaticFiles(directory=_dashboard_dir, html=True), name="dashboard")


def _dev_to_lead_out(dev: Development, lead: Lead) -> LeadOut:
    """Convert Development + Lead ORM objects to API response model."""
    return LeadOut(
        lead_id=str(lead.id),
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
        coordinates=CoordinatesOut(
            latitude=dev.latitude,
            longitude=dev.longitude,
        ),
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
