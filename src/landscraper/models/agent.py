import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, UUIDPrimaryKeyMixin


class AgentRun(UUIDPrimaryKeyMixin, Base):
    """Audit log of every agent execution."""

    __tablename__ = "agent_runs"

    agent_type: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True
    )  # orchestrator, source_discovery, collection, correlation, aggregation, dedup, enrichment, scoring, consensus, self_improvement
    agent_name: Mapped[str] = mapped_column(String(255), nullable=False)
    task_description: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, index=True
    )  # started, completed, failed, timeout
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    duration_seconds: Mapped[float | None] = mapped_column(Float)
    llm_model_used: Mapped[str | None] = mapped_column(String(100))
    llm_tokens_used: Mapped[int | None] = mapped_column(Integer)
    records_processed: Mapped[int | None] = mapped_column(Integer)
    error_message: Mapped[str | None] = mapped_column(Text)
    run_metadata: Mapped[dict | None] = mapped_column(JSONB)


class ImprovementLog(UUIDPrimaryKeyMixin, Base):
    """Self-improvement tracking: strategy changes and performance metrics."""

    __tablename__ = "improvement_logs"

    metric_type: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True
    )  # yield_rate, false_positive_rate, source_freshness, scrape_success_rate
    metric_value: Mapped[float] = mapped_column(Float, nullable=False)
    previous_value: Mapped[float | None] = mapped_column(Float)
    strategy_change: Mapped[str | None] = mapped_column(Text)
    rationale: Mapped[str | None] = mapped_column(Text)
    agent_run_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
