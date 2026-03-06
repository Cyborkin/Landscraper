# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

Landscraper is a LangGraph-based agentic intelligence platform that discovers, scrapes, and aggregates
data indicators for new residential home developments along Colorado's Front Range. It generates
actionable leads for real estate firms. SaaS product with API access and multi-channel notifications.

## Commands

```bash
# Install
python3 -m venv .venv && source .venv/bin/activate && pip install -e ".[dev]"

# Dev services (PostgreSQL only — Redis is on the Swarm host)
docker compose -f docker/docker-compose.dev.yml up -d

# Tests
pytest                           # all tests
pytest tests/path/test_file.py   # single file
pytest -k "test_name"            # single test by name
pytest --cov=landscraper         # with coverage

# Lint & type check
ruff check src/ tests/
ruff format src/ tests/
mypy src/

# Build image (Docker Bake)
docker buildx bake -f docker/docker-bake.hcl

# Deploy to Swarm
ansible-playbook -i ansible/inventory.yml ansible/deploy.yml

# Run API server locally
uvicorn landscraper.api.main:app --reload
```

## Architecture

Multi-agent system using LangGraph's delegating orchestrator pattern:

- **Orchestrator** — task decomposition, delegation, weekly cycle management
- **Source Discovery** — OSINT-style agents that find and evaluate new data sources
- **Collection Specialists** — per-source-type scrapers (Playwright, httpx, RSS, Scrapy)
- **Data Pipeline** — correlation, aggregation, deduplication, enrichment, lead scoring
- **Consensus Layer** — cross-validation, confidence scoring, conflict resolution
- **Self-Improvement** — strategy evaluation, source quality tracking, pattern optimization

Key principle: agents select their tools based on source characteristics, not hardcoded.

## Key Directories

- `src/landscraper/agents/` — LangGraph agent definitions, graph, and node functions
- `src/landscraper/models/` — SQLAlchemy models (9 tables)
- `src/landscraper/scraping/` — 5 scraper types (Census BPS, SODA, SEC EDGAR, RSS, httpx)
- `src/landscraper/pipeline/` — dedup, correlator, enricher, 100-point scorer
- `src/landscraper/consensus/` — validators and confidence scoring
- `src/landscraper/improvement/` — cycle metrics and strategy evaluation
- `src/landscraper/api/` — FastAPI REST API with bearer auth
- `src/landscraper/notifications/` — Slack, webhook, email delivery channels
- `src/landscraper/llm/` — LLM routing (local vs cloud)
- `docs/research/` — Phase 0 research (data sources, lead format)
- `docs/plans/` — implementation plans
- `ansible/` — Ansible playbooks for Swarm deployment
- `docker/` — Dockerfile, docker-bake.hcl, dev/prod compose

## Tracing (LangSmith)

LangSmith observability is integrated. Set `LANDSCRAPER_LANGSMITH_API_KEY` in `.env` to enable.
Pipeline functions (dedup, correlator, enricher, scorer, confidence) use `@traceable` decorators.
LangGraph nodes and Send() delegations are traced automatically.
View traces at https://smith.langchain.com (project: `landscraper`).

## Conventions

- All config via environment variables with `LANDSCRAPER_` prefix (see `.env.example`)
- Async-first: use async/await for DB, HTTP, and scraping operations
- All tables have `tenant_id` column for multi-tenancy
- Agent decisions are logged to `agent_runs` table for auditability
- TDD: write failing test first, then implement
- Build with Docker Bake (`docker/docker-bake.hcl`), deploy with Ansible to Swarm at 192.168.0.12
- Redis is shared from `iranwatch_default` network (db 1) — not managed by us

## Research (Phase 0)

- `docs/research/sources.md` — Validated data source registry with tiered classification and POC sprint order
- `docs/research/lead_format.md` — Lead record schema (45 fields), scoring model, CRM mappings, API spec
- `docs/research/gemini_*_raw.md` — Raw Gemini research output (for reference)
