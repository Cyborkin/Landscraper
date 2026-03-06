"""Tests for self-improvement: metrics and strategy evaluation."""

import pytest

from landscraper.improvement.metrics import compute_cycle_metrics
from landscraper.improvement.strategy import evaluate_strategy


# --- Metrics ---


def test_metrics_basic():
    metrics = compute_cycle_metrics(
        raw_data=[{"a": 1}, {"b": 2}, {"c": 3}],
        developments=[{"sources": ["src_a"], "tier": "warm", "confidence_score": 0.8, "lead_score": 65}],
        validated_leads=[{"sources": ["src_a"], "tier": "warm", "confidence_score": 0.8, "lead_score": 65}],
        errors=[],
    )

    assert metrics["total_raw_records"] == 3
    assert metrics["total_developments"] == 1
    assert metrics["total_validated_leads"] == 1
    assert metrics["total_errors"] == 0
    assert metrics["yield_rate"] > 0
    assert metrics["conversion_rate"] == 1.0
    assert metrics["error_rate"] == 0.0


def test_metrics_empty():
    metrics = compute_cycle_metrics([], [], [], [])
    assert metrics["total_raw_records"] == 0
    assert metrics["yield_rate"] == 0.0
    assert metrics["avg_confidence"] == 0.0


def test_metrics_with_errors():
    metrics = compute_cycle_metrics(
        raw_data=[{} for _ in range(10)],
        developments=[],
        validated_leads=[],
        errors=["error1", "error2", "error3", "error4"],
    )
    assert metrics["error_rate"] == 0.4


def test_metrics_tier_distribution():
    leads = [
        {"tier": "hot", "sources": ["a"], "confidence_score": 0.9, "lead_score": 85},
        {"tier": "hot", "sources": ["a"], "confidence_score": 0.95, "lead_score": 90},
        {"tier": "warm", "sources": ["b"], "confidence_score": 0.7, "lead_score": 60},
        {"tier": "monitor", "sources": ["c"], "confidence_score": 0.5, "lead_score": 35},
    ]
    metrics = compute_cycle_metrics(
        raw_data=[{} for _ in range(20)],
        developments=[{} for _ in range(6)],
        validated_leads=leads,
        errors=[],
    )
    assert metrics["tier_distribution"]["hot"] == 2
    assert metrics["tier_distribution"]["warm"] == 1
    assert metrics["tier_distribution"]["monitor"] == 1


# --- Strategy ---


def test_strategy_good_metrics():
    metrics = {
        "error_rate": 0.02,
        "yield_rate": 0.15,
        "conversion_rate": 0.8,
        "unique_source_count": 3,
        "total_raw_records": 50,
        "total_developments": 10,
        "total_validated_leads": 8,
        "tier_distribution": {"hot": 3, "warm": 4, "monitor": 1, "cold": 0},
        "avg_confidence": 0.75,
    }
    recs = evaluate_strategy(metrics)
    assert len(recs) == 1
    assert recs[0]["severity"] == "info"
    assert "well" in recs[0]["recommendation"].lower()


def test_strategy_high_error_rate():
    metrics = {
        "error_rate": 0.5,
        "yield_rate": 0.1,
        "conversion_rate": 0.5,
        "unique_source_count": 2,
        "total_raw_records": 20,
        "total_developments": 5,
        "total_validated_leads": 3,
        "tier_distribution": {"hot": 1, "warm": 1, "monitor": 1, "cold": 0},
        "avg_confidence": 0.6,
    }
    recs = evaluate_strategy(metrics)
    critical = [r for r in recs if r["severity"] == "critical"]
    assert len(critical) >= 1
    assert critical[0]["area"] == "scraping"


def test_strategy_low_conversion():
    metrics = {
        "error_rate": 0.0,
        "yield_rate": 0.1,
        "conversion_rate": 0.1,
        "unique_source_count": 3,
        "total_raw_records": 100,
        "total_developments": 10,
        "total_validated_leads": 1,
        "tier_distribution": {"hot": 0, "warm": 0, "monitor": 1, "cold": 0},
        "avg_confidence": 0.3,
    }
    recs = evaluate_strategy(metrics)
    areas = [r["area"] for r in recs]
    assert "consensus" in areas


def test_strategy_low_source_diversity():
    metrics = {
        "error_rate": 0.0,
        "yield_rate": 0.1,
        "conversion_rate": 0.8,
        "unique_source_count": 1,
        "total_raw_records": 10,
        "total_developments": 5,
        "total_validated_leads": 4,
        "tier_distribution": {"hot": 1, "warm": 2, "monitor": 1, "cold": 0},
        "avg_confidence": 0.6,
    }
    recs = evaluate_strategy(metrics)
    areas = [r["area"] for r in recs]
    assert "sources" in areas


# --- Self-improvement node integration ---


@pytest.mark.asyncio
async def test_self_improvement_node():
    from landscraper.agents.nodes import self_improvement_node

    state = {
        "raw_data": [{} for _ in range(10)],
        "developments": [
            {"sources": ["a"], "tier": "warm", "confidence_score": 0.7, "lead_score": 55},
        ],
        "validated_leads": [
            {"sources": ["a"], "tier": "warm", "confidence_score": 0.7, "lead_score": 55},
        ],
        "errors": ["one error"],
        "current_phase": "improvement",
        "messages": [],
        "cycle_id": "test",
        "active_sources": [],
        "builders": [],
        "cycle_metrics": {},
    }

    result = await self_improvement_node(state)
    assert result["current_phase"] == "delivery"
    assert "total_raw_records" in result["cycle_metrics"]
    assert "recommendations" in result["cycle_metrics"]
