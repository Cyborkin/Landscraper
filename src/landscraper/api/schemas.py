"""Pydantic schemas for API request/response models."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class AddressOut(BaseModel):
    street: str | None = None
    city: str | None = None
    state: str | None = None
    zip: str | None = None
    county: str | None = None


class CoordinatesOut(BaseModel):
    latitude: float | None = None
    longitude: float | None = None


class StakeholderOut(BaseModel):
    name: str | None = None
    phone: str | None = None
    email: str | None = None
    entity_type: str | None = None
    license: str | None = None


class LeadOut(BaseModel):
    lead_id: str
    confidence_score: float = 0.0
    source_count: int = 0
    sources: list[str] = []
    lead_score: int = 0
    tier: str = "cold"
    score_breakdown: dict[str, int] = {}
    permit_number: str | None = None
    permit_type: str | None = None
    permit_status: str | None = None
    jurisdiction: str | None = None
    address: AddressOut = Field(default_factory=AddressOut)
    coordinates: CoordinatesOut = Field(default_factory=CoordinatesOut)
    property_type: str | None = None
    project_name: str | None = None
    description: str | None = None
    valuation_usd: float | None = None
    unit_count: int | None = None
    total_sqft: int | None = None
    owner_name: str | None = None
    filing_date: str | None = None
    discovered_at: str | None = None
    updated_at: str | None = None
    tags: list[str] = []
    validation_status: str | None = None


class PaginationMeta(BaseModel):
    total_count: int
    page: int
    page_size: int
    next_page_url: str | None = None


class LeadListResponse(BaseModel):
    meta: PaginationMeta
    leads: list[LeadOut]


class HealthResponse(BaseModel):
    status: str
    version: str
    cycle_count: int = 0


class CycleStatusResponse(BaseModel):
    cycle_id: str | None = None
    status: str
    metrics: dict[str, Any] = {}


class TriggerCycleRequest(BaseModel):
    sources: list[dict[str, Any]] | None = None


class TracingStatusResponse(BaseModel):
    enabled: bool
    project: str | None = None
