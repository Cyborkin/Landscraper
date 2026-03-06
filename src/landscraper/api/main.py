"""FastAPI application entry point."""

import logging
import os
import uuid
from contextlib import asynccontextmanager
from typing import Annotated, Any

from fastapi import Depends, FastAPI, Query

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

logger = logging.getLogger(__name__)

# In-memory lead store for POC (production: database)
_leads_store: list[dict[str, Any]] = []
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
    yield


app = FastAPI(
    title="Landscraper API",
    description="Development lead intelligence for Colorado's Front Range",
    version="0.1.0",
    lifespan=lifespan,
)


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
    filtered = _leads_store

    if tier:
        filtered = [l for l in filtered if l.get("tier") == tier]
    if property_type:
        filtered = [l for l in filtered if l.get("property_type") == property_type]
    if county:
        filtered = [l for l in filtered if l.get("county") == county]
    if min_score > 0:
        filtered = [l for l in filtered if l.get("lead_score", 0) >= min_score]

    total = len(filtered)
    start = (page - 1) * page_size
    end = start + page_size
    page_items = filtered[start:end]

    leads_out = [_to_lead_out(l) for l in page_items]

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
    for lead in _leads_store:
        if lead.get("lead_id") == lead_id:
            return _to_lead_out(lead)

    from fastapi import HTTPException

    raise HTTPException(status_code=404, detail="Lead not found")


@app.get("/api/v1/cycle/status", response_model=CycleStatusResponse)
async def cycle_status(
    tenant: Annotated[dict, Depends(verify_api_key)],
):
    """Get the status of the last cycle."""
    return CycleStatusResponse(**_last_cycle)


@app.post("/api/v1/cycle/trigger", response_model=CycleStatusResponse)
async def trigger_cycle(
    body: TriggerCycleRequest,
    tenant: Annotated[dict, Depends(verify_api_key)],
):
    """Trigger a new data collection cycle."""
    from landscraper.tracing import cycle_run_config

    cycle_id = str(uuid.uuid4())
    run_config = cycle_run_config(cycle_id)  # noqa: F841 — used when graph invocation is wired
    _last_cycle.update({
        "cycle_id": cycle_id,
        "status": "triggered",
        "metrics": {},
    })
    # TODO: invoke graph with: await compiled_graph.ainvoke(state, config=run_config)
    return CycleStatusResponse(**_last_cycle)


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


def store_leads(leads: list[dict[str, Any]]) -> None:
    """Store validated leads (called by delivery_node)."""
    for lead in leads:
        if "lead_id" not in lead:
            lead["lead_id"] = str(uuid.uuid4())
        _leads_store.append(lead)


def update_cycle_status(cycle_id: str, status: str, metrics: dict | None = None) -> None:
    """Update cycle status (called by graph nodes)."""
    _last_cycle.update({
        "cycle_id": cycle_id,
        "status": status,
        "metrics": metrics or {},
    })


def _to_lead_out(lead: dict[str, Any]) -> LeadOut:
    """Convert internal lead dict to API response model."""
    return LeadOut(
        lead_id=lead.get("lead_id", ""),
        confidence_score=lead.get("confidence_score", 0.0),
        source_count=lead.get("source_count", 0),
        sources=lead.get("sources", []),
        lead_score=lead.get("lead_score", 0),
        tier=lead.get("tier", "cold"),
        permit_number=lead.get("permit_number"),
        permit_type=lead.get("permit_type"),
        permit_status=lead.get("permit_status"),
        jurisdiction=lead.get("jurisdiction"),
        address=AddressOut(
            street=lead.get("address_street"),
            city=lead.get("address_city"),
            state=lead.get("address_state"),
            zip=lead.get("address_zip"),
            county=lead.get("county"),
        ),
        coordinates=CoordinatesOut(
            latitude=lead.get("latitude"),
            longitude=lead.get("longitude"),
        ),
        property_type=lead.get("property_type"),
        project_name=lead.get("project_name"),
        description=lead.get("description"),
        valuation_usd=lead.get("valuation_usd"),
        unit_count=lead.get("unit_count"),
        total_sqft=lead.get("total_sqft"),
        owner_name=lead.get("owner_name"),
        filing_date=lead.get("filing_date"),
        discovered_at=lead.get("discovered_at"),
        updated_at=lead.get("updated_at"),
        tags=lead.get("tags", []),
        validation_status=lead.get("validation_status"),
    )
