import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Tenant(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "tenants"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    api_key_hash: Mapped[str] = mapped_column(String(128), nullable=False, unique=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    contact_email: Mapped[str | None] = mapped_column(String(255))
    settings: Mapped[dict | None] = mapped_column(JSONB)

    leads: Mapped[list["Lead"]] = relationship(back_populates="tenant")  # noqa: F821
    notification_preferences: Mapped[list["NotificationPreference"]] = relationship(
        back_populates="tenant"
    )


class NotificationPreference(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "notification_preferences"

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True
    )
    channel: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # email, slack, webhook, sms
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    config: Mapped[dict] = mapped_column(
        JSONB, nullable=False
    )  # channel-specific: webhook_url, email, slack_channel, etc.
    filters: Mapped[dict | None] = mapped_column(
        JSONB
    )  # tier, county, property_type filters
    frequency: Mapped[str] = mapped_column(
        String(50), default="realtime", nullable=False
    )  # realtime, daily, weekly

    tenant: Mapped["Tenant"] = relationship(back_populates="notification_preferences")
