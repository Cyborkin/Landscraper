import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, Integer, String, Text
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Development(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Core entity: a normalized development project discovered by the pipeline."""

    __tablename__ = "developments"

    # Permit info
    permit_number: Mapped[str | None] = mapped_column(String(100))
    permit_type: Mapped[str | None] = mapped_column(String(50), index=True)
    permit_status: Mapped[str | None] = mapped_column(String(50), index=True)
    jurisdiction: Mapped[str | None] = mapped_column(String(255))

    # Location
    address_street: Mapped[str | None] = mapped_column(String(500))
    address_city: Mapped[str | None] = mapped_column(String(255), index=True)
    address_state: Mapped[str] = mapped_column(String(2), default="CO", nullable=False)
    address_zip: Mapped[str | None] = mapped_column(String(10))
    county: Mapped[str | None] = mapped_column(String(100), index=True)
    apn: Mapped[str | None] = mapped_column(String(50))
    latitude: Mapped[float | None] = mapped_column(Float)
    longitude: Mapped[float | None] = mapped_column(Float)

    # Zoning
    zoning_current: Mapped[str | None] = mapped_column(String(50))
    zoning_proposed: Mapped[str | None] = mapped_column(String(50))

    # Project details
    property_type: Mapped[str | None] = mapped_column(String(50), index=True)
    project_name: Mapped[str | None] = mapped_column(String(500))
    description: Mapped[str | None] = mapped_column(Text)
    valuation_usd: Mapped[float | None] = mapped_column(Float)
    unit_count: Mapped[int | None] = mapped_column(Integer)
    total_sqft: Mapped[int | None] = mapped_column(Integer)
    lot_size_acres: Mapped[float | None] = mapped_column(Float)
    stories: Mapped[int | None] = mapped_column(Integer)

    # Owner / stakeholders
    owner_name: Mapped[str | None] = mapped_column(String(500))
    owner_entity_type: Mapped[str | None] = mapped_column(String(50))
    owner_phone: Mapped[str | None] = mapped_column(String(20))
    owner_email: Mapped[str | None] = mapped_column(String(255))
    owner_mailing_address: Mapped[str | None] = mapped_column(Text)
    applicant_name: Mapped[str | None] = mapped_column(String(500))
    applicant_phone: Mapped[str | None] = mapped_column(String(20))
    applicant_email: Mapped[str | None] = mapped_column(String(255))
    contractor_name: Mapped[str | None] = mapped_column(String(500))
    contractor_license: Mapped[str | None] = mapped_column(String(100))
    architect_name: Mapped[str | None] = mapped_column(String(500))

    # Dates
    filing_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    approval_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    estimated_start_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    estimated_completion_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # Consensus
    confidence_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    source_count: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    sources: Mapped[list[str]] = mapped_column(ARRAY(String), nullable=False)

    # Discovery metadata
    discovered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    tags: Mapped[list[str] | None] = mapped_column(ARRAY(String))

    # Dedup / scoring
    content_hash: Mapped[str | None] = mapped_column(String(64), unique=True, index=True)
    score_breakdown: Mapped[dict | None] = mapped_column(JSONB)
    validation_status: Mapped[str | None] = mapped_column(String(20))
    lead_score: Mapped[int | None] = mapped_column(Integer)
    tier: Mapped[str | None] = mapped_column(String(20), index=True)

    leads: Mapped[list["Lead"]] = relationship(back_populates="development")  # noqa: F821


class Builder(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Entity record for a builder or development company."""

    __tablename__ = "builders"

    company_name: Mapped[str] = mapped_column(String(500), nullable=False, index=True)
    entity_type: Mapped[str | None] = mapped_column(String(50))
    headquarters_city: Mapped[str | None] = mapped_column(String(255))
    headquarters_state: Mapped[str | None] = mapped_column(String(2))
    geographic_regions: Mapped[list[str] | None] = mapped_column(ARRAY(String))
    website: Mapped[str | None] = mapped_column(Text)

    # Primary contact
    primary_contact_name: Mapped[str | None] = mapped_column(String(255))
    primary_contact_title: Mapped[str | None] = mapped_column(String(255))
    primary_contact_email: Mapped[str | None] = mapped_column(String(255))
    primary_contact_phone: Mapped[str | None] = mapped_column(String(20))
    primary_contact_linkedin: Mapped[str | None] = mapped_column(Text)

    # Pipeline
    active_project_count: Mapped[int | None] = mapped_column(Integer)
    pipeline_value_usd: Mapped[float | None] = mapped_column(Float)
    historical_units_delivered: Mapped[int | None] = mapped_column(Integer)
    historical_sqft_delivered: Mapped[int | None] = mapped_column(Integer)
    asset_specialization: Mapped[dict | None] = mapped_column(JSONB)
    preferred_partnership_model: Mapped[str | None] = mapped_column(String(50))

    # Bonding
    bonding_capacity_single_usd: Mapped[float | None] = mapped_column(Float)
    bonding_capacity_aggregate_usd: Mapped[float | None] = mapped_column(Float)

    # Consensus
    confidence_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    source_count: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    sources: Mapped[list[str]] = mapped_column(ARRAY(String), nullable=False)

    # Discovery
    discovered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    leads: Mapped[list["Lead"]] = relationship(back_populates="builder")  # noqa: F821
