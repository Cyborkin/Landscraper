# LangSmith Tracing Integration — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Integrate LangSmith observability into the Landscraper LangGraph pipeline so every cycle run, node execution, and LLM call is traced and visible in the LangSmith dashboard.

**Architecture:** LangSmith tracing activates via environment variables that LangChain/LangGraph read automatically. We add config settings to control tracing, a setup module to configure it programmatically (project name, tags, metadata per cycle), and ensure tests never send traces. The graph compilation gets a `project_name` tag, and the API gets a `/tracing/status` endpoint.

**Tech Stack:** langsmith 0.7.x (already installed as transitive dep), LangGraph, Pydantic Settings

---

### Task 1: Add LangSmith Config Settings

**Files:**
- Modify: `src/landscraper/config.py`
- Modify: `.env.example`

**Step 1: Add LangSmith settings to config**

Add these fields to the `Settings` class in `src/landscraper/config.py`:

```python
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    model_config = {"env_prefix": "LANDSCRAPER_"}

    # Database
    database_url: str = "postgresql+asyncpg://landscraper:landscraper@localhost:5432/landscraper"

    # Redis
    redis_url: str = "redis://redis:6379/1"  # db 1 to avoid iranwatch collision

    # LLM
    anthropic_api_key: str = ""
    ollama_base_url: str = "http://localhost:11434"
    default_cloud_model: str = "claude-sonnet-4-20250514"
    default_local_model: str = "mistral"

    # LangSmith
    langsmith_api_key: str = ""
    langsmith_project: str = "landscraper"
    langsmith_tracing_enabled: bool = True

    # Scraping
    scrape_rate_limit_seconds: float = 2.0
    playwright_headless: bool = True

    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000


settings = Settings()
```

**Step 2: Add LangSmith vars to `.env.example`**

Append to `.env.example`:

```bash
# LangSmith Observability
LANDSCRAPER_LANGSMITH_API_KEY=lsv2_pt_...
LANDSCRAPER_LANGSMITH_PROJECT=landscraper
LANDSCRAPER_LANGSMITH_TRACING_ENABLED=true
```

**Step 3: Commit**

```bash
git add src/landscraper/config.py .env.example
git commit -m "feat: add LangSmith config settings

LANDSCRAPER_LANGSMITH_API_KEY, _PROJECT, _TRACING_ENABLED settings."
```

---

### Task 2: Create Tracing Setup Module

**Files:**
- Create: `src/landscraper/tracing.py`

**Step 1: Write the tracing setup module**

This module sets the environment variables that LangChain/LangGraph read at import time, and provides a helper to create per-cycle run metadata.

```python
"""LangSmith tracing configuration.

Sets environment variables that LangChain/LangGraph auto-detect.
Call configure_tracing() at application startup (before any LangChain imports
in production — in our case, LangChain is imported at module level so we
call it early in app lifespan and graph entry points).
"""

import os
from typing import Any


def configure_tracing() -> bool:
    """Configure LangSmith tracing from Landscraper settings.

    Sets the LANGCHAIN_* env vars that LangChain/LangGraph auto-detect.
    Returns True if tracing was enabled, False otherwise.
    """
    from landscraper.config import settings

    if not settings.langsmith_tracing_enabled or not settings.langsmith_api_key:
        os.environ.pop("LANGCHAIN_TRACING_V2", None)
        return False

    os.environ["LANGCHAIN_TRACING_V2"] = "true"
    os.environ["LANGCHAIN_API_KEY"] = settings.langsmith_api_key
    os.environ["LANGCHAIN_PROJECT"] = settings.langsmith_project

    return True


def disable_tracing() -> None:
    """Explicitly disable tracing (used in tests)."""
    os.environ.pop("LANGCHAIN_TRACING_V2", None)
    os.environ.pop("LANGCHAIN_API_KEY", None)
    os.environ.pop("LANGCHAIN_PROJECT", None)


def tracing_is_enabled() -> bool:
    """Check if tracing is currently active."""
    return os.environ.get("LANGCHAIN_TRACING_V2", "").lower() == "true"


def cycle_run_metadata(cycle_id: str, sources: list[str] | None = None) -> dict[str, Any]:
    """Build metadata dict for a cycle run.

    Passed as config to graph.ainvoke() so LangSmith tags the run.
    """
    metadata: dict[str, Any] = {
        "cycle_id": cycle_id,
        "app": "landscraper",
    }
    if sources:
        metadata["sources"] = sources

    return metadata


def cycle_run_config(cycle_id: str, sources: list[str] | None = None) -> dict[str, Any]:
    """Build LangGraph run config with LangSmith metadata and tags.

    Usage: await graph.ainvoke(state, config=cycle_run_config(cycle_id))
    """
    return {
        "metadata": cycle_run_metadata(cycle_id, sources),
        "tags": ["landscraper", "cycle"],
        "run_name": f"landscraper-cycle-{cycle_id[:8]}",
    }
```

**Step 2: Commit**

```bash
git add src/landscraper/tracing.py
git commit -m "feat: add LangSmith tracing setup module

configure_tracing(), disable_tracing(), cycle_run_config() helpers."
```

---

### Task 3: Wire Tracing into Application Startup

**Files:**
- Modify: `src/landscraper/api/main.py` (lifespan)

**Step 1: Call configure_tracing() in the FastAPI lifespan**

In `src/landscraper/api/main.py`, update the lifespan to call `configure_tracing()`:

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    from landscraper.tracing import configure_tracing

    register_default_tenant()
    tracing = configure_tracing()
    if tracing:
        import logging
        logging.getLogger(__name__).info("LangSmith tracing enabled (project: %s)",
            os.environ.get("LANGCHAIN_PROJECT", "default"))
    yield
```

Add `import os` to the imports at the top of the file.

**Step 2: Commit**

```bash
git add src/landscraper/api/main.py
git commit -m "feat: enable LangSmith tracing at API startup"
```

---

### Task 4: Add Run Config to Graph Invocations

**Files:**
- Modify: `src/landscraper/api/main.py` (trigger_cycle endpoint)

**Step 1: Pass cycle_run_config when triggering a cycle**

Update the `trigger_cycle` endpoint in `src/landscraper/api/main.py` to show how the graph would be invoked with tracing config. Since the graph isn't actually invoked async yet (it's a TODO), add the config preparation:

```python
@app.post("/api/v1/cycle/trigger", response_model=CycleStatusResponse)
async def trigger_cycle(
    body: TriggerCycleRequest,
    tenant: Annotated[dict, Depends(verify_api_key)],
):
    """Trigger a new data collection cycle."""
    from landscraper.tracing import cycle_run_config

    cycle_id = str(uuid.uuid4())
    run_config = cycle_run_config(cycle_id)
    _last_cycle.update({
        "cycle_id": cycle_id,
        "status": "triggered",
        "metrics": {},
    })
    # TODO: invoke graph with: await app.ainvoke(state, config=run_config)
    return CycleStatusResponse(**_last_cycle)
```

**Step 2: Commit**

```bash
git add src/landscraper/api/main.py
git commit -m "feat: prepare LangSmith run config for cycle triggers"
```

---

### Task 5: Add Tracing Status API Endpoint

**Files:**
- Modify: `src/landscraper/api/schemas.py`
- Modify: `src/landscraper/api/main.py`

**Step 1: Add TracingStatusResponse schema**

Add to `src/landscraper/api/schemas.py`:

```python
class TracingStatusResponse(BaseModel):
    enabled: bool
    project: str | None = None
```

**Step 2: Add the endpoint to `src/landscraper/api/main.py`**

```python
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
```

Import `TracingStatusResponse` in the existing import block.

**Step 3: Commit**

```bash
git add src/landscraper/api/schemas.py src/landscraper/api/main.py
git commit -m "feat: add /api/v1/tracing/status endpoint"
```

---

### Task 6: Disable Tracing in Tests

**Files:**
- Modify: `tests/conftest.py`

**Step 1: Add autouse fixture to disable tracing**

Add to `tests/conftest.py` (before the existing fixtures):

```python
@pytest.fixture(autouse=True, scope="session")
def disable_langsmith_tracing():
    """Ensure LangSmith tracing is disabled during tests."""
    from landscraper.tracing import disable_tracing
    disable_tracing()
    yield
```

**Step 2: Run all tests to verify nothing breaks**

Run: `.venv/bin/pytest -v`
Expected: 97 passed

**Step 3: Commit**

```bash
git add tests/conftest.py
git commit -m "test: disable LangSmith tracing in test suite"
```

---

### Task 7: Write Tests for Tracing Module

**Files:**
- Create: `tests/test_tracing.py`

**Step 1: Write tests**

```python
"""Tests for LangSmith tracing configuration."""

import os

import pytest


def test_configure_tracing_enabled(monkeypatch):
    """Tracing should set LANGCHAIN env vars when API key is present."""
    monkeypatch.setenv("LANDSCRAPER_LANGSMITH_API_KEY", "lsv2_pt_test_key")
    monkeypatch.setenv("LANDSCRAPER_LANGSMITH_PROJECT", "test-project")
    monkeypatch.setenv("LANDSCRAPER_LANGSMITH_TRACING_ENABLED", "true")

    # Force Settings reload
    from landscraper.config import Settings
    monkeypatch.setattr("landscraper.tracing.settings", Settings(), raising=False)
    # Re-import to pick up monkeypatched settings
    import importlib
    import landscraper.tracing
    importlib.reload(landscraper.tracing)
    from landscraper.tracing import configure_tracing

    result = configure_tracing()

    assert result is True
    assert os.environ.get("LANGCHAIN_TRACING_V2") == "true"
    assert os.environ.get("LANGCHAIN_API_KEY") == "lsv2_pt_test_key"
    assert os.environ.get("LANGCHAIN_PROJECT") == "test-project"

    # Cleanup
    from landscraper.tracing import disable_tracing
    disable_tracing()


def test_configure_tracing_disabled_no_key(monkeypatch):
    """Tracing should not activate without an API key."""
    monkeypatch.delenv("LANDSCRAPER_LANGSMITH_API_KEY", raising=False)
    monkeypatch.setenv("LANDSCRAPER_LANGSMITH_TRACING_ENABLED", "true")

    from landscraper.config import Settings
    import importlib
    import landscraper.tracing
    importlib.reload(landscraper.tracing)
    from landscraper.tracing import configure_tracing

    result = configure_tracing()

    assert result is False
    assert os.environ.get("LANGCHAIN_TRACING_V2") is None


def test_disable_tracing():
    """disable_tracing should remove all LANGCHAIN env vars."""
    os.environ["LANGCHAIN_TRACING_V2"] = "true"
    os.environ["LANGCHAIN_API_KEY"] = "test"
    os.environ["LANGCHAIN_PROJECT"] = "test"

    from landscraper.tracing import disable_tracing
    disable_tracing()

    assert os.environ.get("LANGCHAIN_TRACING_V2") is None
    assert os.environ.get("LANGCHAIN_API_KEY") is None
    assert os.environ.get("LANGCHAIN_PROJECT") is None


def test_tracing_is_enabled():
    from landscraper.tracing import disable_tracing, tracing_is_enabled

    disable_tracing()
    assert tracing_is_enabled() is False

    os.environ["LANGCHAIN_TRACING_V2"] = "true"
    assert tracing_is_enabled() is True

    disable_tracing()


def test_cycle_run_config():
    from landscraper.tracing import cycle_run_config

    config = cycle_run_config("abc-123", sources=["soda", "census"])

    assert config["run_name"] == "landscraper-cycle-abc-123"
    assert "landscraper" in config["tags"]
    assert "cycle" in config["tags"]
    assert config["metadata"]["cycle_id"] == "abc-123"
    assert config["metadata"]["sources"] == ["soda", "census"]


def test_cycle_run_config_no_sources():
    from landscraper.tracing import cycle_run_config

    config = cycle_run_config("xyz-789")

    assert config["metadata"]["cycle_id"] == "xyz-789"
    assert "sources" not in config["metadata"]


def test_cycle_run_metadata():
    from landscraper.tracing import cycle_run_metadata

    meta = cycle_run_metadata("test-cycle")

    assert meta["cycle_id"] == "test-cycle"
    assert meta["app"] == "landscraper"
```

**Step 2: Run tests**

Run: `.venv/bin/pytest tests/test_tracing.py -v`
Expected: 7 passed

**Step 3: Commit**

```bash
git add tests/test_tracing.py
git commit -m "test: add tests for LangSmith tracing module

7 tests covering enable/disable, config, run metadata."
```

---

### Task 8: Write Test for Tracing Status Endpoint

**Files:**
- Modify: `tests/test_api.py`

**Step 1: Add tracing status test**

Add to the end of `tests/test_api.py`:

```python
def test_tracing_status():
    response = client.get("/api/v1/tracing/status", headers=AUTH_HEADER)
    assert response.status_code == 200
    data = response.json()
    assert "enabled" in data
    assert isinstance(data["enabled"], bool)
```

**Step 2: Run API tests**

Run: `.venv/bin/pytest tests/test_api.py -v`
Expected: 15 passed

**Step 3: Commit**

```bash
git add tests/test_api.py
git commit -m "test: add tracing status endpoint test"
```

---

### Task 9: Add `.env` File with API Key

**Files:**
- Create: `.env` (git-ignored)

**Step 1: Create `.env` with the LangSmith API key**

```bash
# LangSmith
LANDSCRAPER_LANGSMITH_API_KEY=YOUR_LANGSMITH_API_KEY_HERE
LANDSCRAPER_LANGSMITH_PROJECT=landscraper
LANDSCRAPER_LANGSMITH_TRACING_ENABLED=true
```

**Step 2: Verify `.env` is in `.gitignore`**

Run: `grep -c '\.env' .gitignore`
Expected: At least 1 match (`.env` is already gitignored).

**Step 3: Add `langsmith` as explicit dependency**

In `pyproject.toml`, add `"langsmith>=0.7"` to the dependencies list under `# Agent framework`:

```toml
dependencies = [
    # Agent framework
    "langgraph>=0.2",
    "langchain-core>=0.3",
    "langchain-anthropic>=0.3",
    "langchain-community>=0.3",
    "langsmith>=0.7",
    ...
```

**Step 4: Commit**

```bash
git add pyproject.toml
git commit -m "chore: add langsmith as explicit dependency"
```

---

### Task 10: Run Full Test Suite and Final Commit

**Step 1: Run all tests**

Run: `.venv/bin/pytest -v`
Expected: 105+ passed (97 existing + 7 tracing + 1 API endpoint)

**Step 2: Verify tracing works with a quick smoke test**

```bash
LANDSCRAPER_LANGSMITH_API_KEY=YOUR_LANGSMITH_API_KEY_HERE \
LANDSCRAPER_LANGSMITH_PROJECT=landscraper \
LANDSCRAPER_LANGSMITH_TRACING_ENABLED=true \
.venv/bin/python -c "
from landscraper.tracing import configure_tracing, tracing_is_enabled
configure_tracing()
print(f'Tracing enabled: {tracing_is_enabled()}')
"
```

Expected: `Tracing enabled: True`

**Step 3: Update CLAUDE.md with tracing info**

Add to the Commands section of `CLAUDE.md`:

```markdown
# Tracing (LangSmith)
# Set LANDSCRAPER_LANGSMITH_API_KEY in .env to enable
# View traces at https://smith.langchain.com
```

**Step 4: Final commit**

```bash
git add CLAUDE.md
git commit -m "docs: add LangSmith tracing to CLAUDE.md"
```
