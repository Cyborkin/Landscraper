import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, Integer, String, Text
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class DataSource(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "data_sources"

    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    url: Mapped[str] = mapped_column(Text, nullable=False)
    source_type: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True
    )  # permit_portal, planning_agenda, assessor, rss, api, news, sec_filing
    access_method: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # public_web, api, rss, auth_required, paid
    scrape_complexity: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # static_html, js_rendered, pdf, api, rss
    geographic_coverage: Mapped[list[str] | None] = mapped_column(ARRAY(String))
    reliability_score: Mapped[float] = mapped_column(Float, default=0.5, nullable=False)
    tier: Mapped[str] = mapped_column(
        String(20), default="tier_2", nullable=False
    )  # tier_1, tier_2, tier_3
    scrape_config: Mapped[dict | None] = mapped_column(JSONB)
    last_scraped_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_success_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    scrape_frequency_hours: Mapped[int] = mapped_column(Integer, default=6, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    error_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_error: Mapped[str | None] = mapped_column(Text)

    raw_collections: Mapped[list["RawCollection"]] = relationship(  # noqa: F821
        back_populates="source"
    )
