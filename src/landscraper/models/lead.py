import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Lead(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Tenant-scoped scored lead linking to a development and/or builder."""

    __tablename__ = "leads"

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True
    )
    development_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("developments.id"), index=True
    )
    builder_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("builders.id"), index=True
    )
    lead_type: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True
    )  # development, partnership
    lead_score: Mapped[int] = mapped_column(Integer, default=0, nullable=False, index=True)
    tier: Mapped[str] = mapped_column(
        String(20), default="cold", nullable=False, index=True
    )  # hot, warm, monitor, cold
    status: Mapped[str] = mapped_column(
        String(20), default="new", nullable=False, index=True
    )  # new, contacted, qualified, converted, rejected, archived
    rejection_reason: Mapped[str | None] = mapped_column(Text)
    delivered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    delivered_via: Mapped[list[str] | None] = mapped_column(ARRAY(String))

    tenant: Mapped["Tenant"] = relationship(back_populates="leads")  # noqa: F821
    development: Mapped["Development | None"] = relationship(  # noqa: F821
        back_populates="leads"
    )
    builder: Mapped["Builder | None"] = relationship(back_populates="leads")  # noqa: F821
