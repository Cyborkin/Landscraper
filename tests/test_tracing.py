"""Tests for LangSmith tracing configuration."""

import os

import pytest

from landscraper.tracing import (
    configure_tracing,
    cycle_run_config,
    cycle_run_metadata,
    disable_tracing,
    tracing_is_enabled,
)


@pytest.fixture(autouse=True)
def cleanup_env():
    """Ensure tracing env vars are cleaned up after each test."""
    yield
    disable_tracing()


def test_configure_tracing_enabled(monkeypatch):
    monkeypatch.setattr(
        "landscraper.tracing.settings",
        type("S", (), {
            "langsmith_api_key": "lsv2_pt_test_key",
            "langsmith_project": "test-project",
            "langsmith_tracing_enabled": True,
        })(),
    )

    result = configure_tracing()

    assert result is True
    assert os.environ.get("LANGCHAIN_TRACING_V2") == "true"
    assert os.environ.get("LANGCHAIN_API_KEY") == "lsv2_pt_test_key"
    assert os.environ.get("LANGCHAIN_PROJECT") == "test-project"


def test_configure_tracing_disabled_no_key(monkeypatch):
    monkeypatch.setattr(
        "landscraper.tracing.settings",
        type("S", (), {
            "langsmith_api_key": "",
            "langsmith_project": "test",
            "langsmith_tracing_enabled": True,
        })(),
    )

    result = configure_tracing()

    assert result is False
    assert os.environ.get("LANGCHAIN_TRACING_V2") is None


def test_configure_tracing_disabled_flag(monkeypatch):
    monkeypatch.setattr(
        "landscraper.tracing.settings",
        type("S", (), {
            "langsmith_api_key": "lsv2_pt_test",
            "langsmith_project": "test",
            "langsmith_tracing_enabled": False,
        })(),
    )

    result = configure_tracing()
    assert result is False


def test_disable_tracing():
    os.environ["LANGCHAIN_TRACING_V2"] = "true"
    os.environ["LANGCHAIN_API_KEY"] = "test"
    os.environ["LANGCHAIN_PROJECT"] = "test"

    disable_tracing()

    assert os.environ.get("LANGCHAIN_TRACING_V2") is None
    assert os.environ.get("LANGCHAIN_API_KEY") is None
    assert os.environ.get("LANGCHAIN_PROJECT") is None


def test_tracing_is_enabled():
    disable_tracing()
    assert tracing_is_enabled() is False

    os.environ["LANGCHAIN_TRACING_V2"] = "true"
    assert tracing_is_enabled() is True


def test_cycle_run_config():
    config = cycle_run_config("abc-123", sources=["soda", "census"])

    assert config["run_name"] == "landscraper-cycle-abc-123"
    assert "landscraper" in config["tags"]
    assert "cycle" in config["tags"]
    assert config["metadata"]["cycle_id"] == "abc-123"
    assert config["metadata"]["sources"] == ["soda", "census"]
    assert config["metadata"]["source_count"] == 2


def test_cycle_run_config_no_sources():
    config = cycle_run_config("xyz-789")

    assert config["metadata"]["cycle_id"] == "xyz-789"
    assert "sources" not in config["metadata"]
    assert "source_count" not in config["metadata"]


def test_cycle_run_metadata():
    meta = cycle_run_metadata("test-cycle")

    assert meta["cycle_id"] == "test-cycle"
    assert meta["app"] == "landscraper"
