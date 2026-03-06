# Phase 0: Research & Project Setup — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Establish the Landscraper project scaffolding and complete data source + lead format research before writing any application code.

**Architecture:** LangGraph-based multi-agent intelligence platform that discovers, scrapes, and aggregates indicators of new residential developments along Colorado's Front Range to generate actionable leads for real estate firms. Phase 0 sets up the project skeleton and completes research (via Gemini collaboration) that will inform schema design and agent implementation in subsequent phases.

**Tech Stack:** Python 3.14+, LangGraph, FastAPI, PostgreSQL, Redis, Playwright, Scrapy, httpx, feedparser, Docker

**Environment:** macOS (darwin), Gemini CLI at `/opt/homebrew/bin/gemini`, Docker 29.x

---

### Task 1: Initialize Repository and Directory Structure

**Files:**
- Create: `.gitignore`
- Create: `README.md`
- Create: directory tree under `src/landscraper/`, `tests/`, `docs/`, `docker/`, `ansible/`

**Step 1: Initialize git repo**

```bash
cd /Users/dustinmaselbas/programming/project_hunterd
git init
```

**Step 2: Create `.gitignore`**

```gitignore
# Python
__pycache__/
*.py[cod]
*$py.class
*.egg-info/
*.egg
dist/
build/
.eggs/

# Virtual environments
.venv/
venv/
env/

# IDE
.vscode/
.idea/
*.swp
*.swo

# Environment
.env
.env.local

# Docker
docker/data/

# OS
.DS_Store
Thumbs.db

# Testing
.coverage
htmlcov/
.pytest_cache/

# mypy
.mypy_cache/

# Scrapy
*.log
```

**Step 3: Create `README.md`**

```markdown
# Landscraper

LangGraph-based agentic intelligence platform that discovers, scrapes, and aggregates data indicators for new residential home developments along Colorado's Front Range. Generates actionable leads — development locations and builder/developer partnership opportunities — for real estate firms.

## Status

Phase 0: Research & Project Setup

## Quick Start

```bash
# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install in development mode
pip install -e ".[dev]"

# Start development services (PostgreSQL only — Redis on Swarm host)
docker compose -f docker/docker-compose.dev.yml up -d

# Run tests
pytest
```
```

**Step 4: Create directory structure**

```bash
mkdir -p src/landscraper/{agents,models,scraping,api,notifications,llm}
mkdir -p tests
mkdir -p docs/{plans,research}
mkdir -p docker
mkdir -p ansible
touch src/landscraper/__init__.py
touch src/landscraper/agents/__init__.py
touch src/landscraper/models/__init__.py
touch src/landscraper/scraping/__init__.py
touch src/landscraper/api/__init__.py
touch src/landscraper/notifications/__init__.py
touch src/landscraper/llm/__init__.py
touch tests/__init__.py
```

**Step 5: Commit**

```bash
git add .gitignore README.md src/ tests/ docs/ docker/
git commit -m "chore: initialize project structure

Set up directory layout for Landscraper: src/landscraper with agent,
model, scraping, api, notification, and llm packages. Added tests,
docs, and docker directories."
```

---

### Task 2: Python Project Configuration

**Files:**
- Create: `pyproject.toml`
- Create: `src/landscraper/config.py`

**Step 1: Create `pyproject.toml`**

```toml
[build-system]
requires = ["setuptools>=68.0", "setuptools-scm>=8.0"]
build-backend = "setuptools.backends._legacy:_Backend"

[project]
name = "landscraper"
version = "0.1.0"
description = "Agentic intelligence platform for discovering new residential developments along Colorado's Front Range"
requires-python = ">=3.11"
dependencies = [
    # Agent framework
    "langgraph>=0.2",
    "langchain-core>=0.3",
    "langchain-anthropic>=0.3",
    "langchain-community>=0.3",

    # API
    "fastapi>=0.115",
    "uvicorn[standard]>=0.32",

    # Database
    "sqlalchemy[asyncio]>=2.0",
    "alembic>=1.14",
    "asyncpg>=0.30",
    "redis>=5.0",

    # Scraping
    "playwright>=1.48",
    "scrapy>=2.11",
    "httpx>=0.28",
    "feedparser>=6.0",

    # Utilities
    "pydantic>=2.9",
    "pydantic-settings>=2.6",
    "python-dotenv>=1.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.3",
    "pytest-asyncio>=0.24",
    "pytest-cov>=6.0",
    "ruff>=0.8",
    "mypy>=1.13",
]

[tool.setuptools.packages.find]
where = ["src"]

[tool.pytest.ini_options]
testpaths = ["tests"]
asyncio_mode = "auto"

[tool.ruff]
target-version = "py311"
line-length = 100

[tool.ruff.lint]
select = ["E", "F", "I", "N", "W", "UP"]

[tool.mypy]
python_version = "3.11"
strict = true
warn_return_any = true
warn_unused_configs = true
```

**Step 2: Create `src/landscraper/config.py`**

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

    # Scraping
    scrape_rate_limit_seconds: float = 2.0
    playwright_headless: bool = True

    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000


settings = Settings()
```

**Step 3: Create virtual environment and install**

```bash
cd /Users/dustinmaselbas/programming/project_hunterd
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

**Step 4: Verify installation**

```bash
python -c "from landscraper.config import Settings; print('OK')"
```

Expected: `OK`

**Step 5: Commit**

```bash
git add pyproject.toml src/landscraper/config.py
git commit -m "chore: add pyproject.toml and config module

Core dependencies: LangGraph, FastAPI, SQLAlchemy, Playwright, Scrapy.
Pydantic-settings based config with env var support."
```

---

### Task 3: Docker & Infrastructure Configuration

**Note:** Redis already runs on the Docker Swarm host (`192.168.0.12`) — do NOT include it in compose/bake configs. Build uses Docker Bake; deployment uses Ansible targeting the Swarm.

**Files:**
- Create: `docker/Dockerfile`
- Create: `docker/docker-bake.hcl`
- Create: `docker/docker-compose.dev.yml` (local dev — PostgreSQL only)
- Create: `ansible/inventory.yml`
- Create: `ansible/deploy.yml`
- Create: `.env.example`

**Step 1: Create `docker/Dockerfile`**

```dockerfile
FROM python:3.14-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml .
COPY src/ src/

RUN pip install --no-cache-dir .

RUN playwright install --with-deps chromium

EXPOSE 8000

CMD ["uvicorn", "landscraper.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Step 2: Create `docker/docker-bake.hcl`**

```hcl
group "default" {
  targets = ["landscraper"]
}

variable "TAG" {
  default = "latest"
}

variable "REGISTRY" {
  default = "192.168.0.12:5000"
}

target "landscraper" {
  context    = ".."
  dockerfile = "docker/Dockerfile"
  tags       = ["${REGISTRY}/landscraper:${TAG}", "${REGISTRY}/landscraper:latest"]
  platforms  = ["linux/amd64"]
}

target "landscraper-dev" {
  inherits = ["landscraper"]
  tags     = ["landscraper:dev"]
  cache-from = ["type=local,src=/tmp/.buildx-cache"]
  cache-to   = ["type=local,dest=/tmp/.buildx-cache"]
}
```

**Step 3: Create `docker/docker-compose.dev.yml` (local PostgreSQL only — Redis is on the Swarm host)**

```yaml
services:
  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: landscraper
      POSTGRES_PASSWORD: landscraper
      POSTGRES_DB: landscraper
    ports:
      - "5432:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U landscraper"]
      interval: 5s
      timeout: 5s
      retries: 5

volumes:
  pgdata:
```

**Step 4: Create `ansible/inventory.yml`**

```yaml
all:
  hosts:
    swarm_manager:
      ansible_host: 192.168.0.12
      ansible_user: swarm
      ansible_password: swarm
  vars:
    registry: "192.168.0.12:5000"
    landscraper_tag: "latest"
    redis_url: "redis://redis:6379/1"
    db_url: "postgresql+asyncpg://landscraper:landscraper@postgres:5432/landscraper"
    redis_network: "iranwatch_default"
```

**Step 5: Create `ansible/deploy.yml`**

```yaml
---
- name: Deploy Landscraper to Docker Swarm
  hosts: swarm_manager
  tasks:
    - name: Pull latest image
      community.docker.docker_image:
        name: "{{ registry }}/landscraper:{{ landscraper_tag }}"
        source: pull
        force_source: true

    - name: Deploy stack
      community.docker.docker_stack:
        name: landscraper
        compose:
          - version: "3.8"
            services:
              api:
                image: "{{ registry }}/landscraper:{{ landscraper_tag }}"
                environment:
                  LANDSCRAPER_DATABASE_URL: "{{ db_url }}"
                  LANDSCRAPER_REDIS_URL: "{{ redis_url }}"
                networks:
                  - default
                  - redis_net
                ports:
                  - "8000:8000"
                deploy:
                  replicas: 1
                  restart_policy:
                    condition: on-failure
                    delay: 5s
                    max_attempts: 3

              postgres:
                image: postgres:16-alpine
                environment:
                  POSTGRES_USER: landscraper
                  POSTGRES_PASSWORD: landscraper
                  POSTGRES_DB: landscraper
                volumes:
                  - pgdata:/var/lib/postgresql/data
                deploy:
                  placement:
                    constraints:
                      - node.role == manager

            networks:
              redis_net:
                external: true
                name: "{{ redis_network }}"

            volumes:
              pgdata:
        state: present
```

**Step 6: Create `.env.example`**

```bash
# Database
LANDSCRAPER_DATABASE_URL=postgresql+asyncpg://landscraper:landscraper@localhost:5432/landscraper

# Redis (existing instance on iranwatch_default network, use db 1)
LANDSCRAPER_REDIS_URL=redis://redis:6379/1

# LLM
LANDSCRAPER_ANTHROPIC_API_KEY=sk-ant-...
LANDSCRAPER_OLLAMA_BASE_URL=http://localhost:11434

# Scraping
LANDSCRAPER_SCRAPE_RATE_LIMIT_SECONDS=2.0
LANDSCRAPER_PLAYWRIGHT_HEADLESS=true
```

**Step 7: Start local dev services and verify**

```bash
docker compose -f docker/docker-compose.dev.yml up -d
docker compose -f docker/docker-compose.dev.yml ps
```

Expected: `postgres` service running and healthy.

**Step 8: Verify PostgreSQL connectivity**

```bash
PGPASSWORD=landscraper psql -h localhost -U landscraper -d landscraper -c "SELECT 1;"
```

Expected: Returns `1`.

**Step 9: Verify Docker Bake builds**

```bash
docker buildx bake -f docker/docker-bake.hcl landscraper-dev --print
```

Expected: Shows the build plan without errors.

**Step 10: Commit**

```bash
git add docker/ ansible/ .env.example
git commit -m "chore: add Docker Bake build + Ansible deployment

Docker Bake for image builds targeting Swarm registry.
Ansible playbook for Docker Swarm deployment at 192.168.0.12.
Local dev compose with PostgreSQL only (Redis on Swarm host).
.env.example with all configuration variables."
```

---

### Task 4: Dispatch Research Tasks to Gemini (Parallel)

Both research tasks are sent to Gemini in parallel. Save raw output for later synthesis.

**Files:**
- Create: `docs/research/gemini_sources_raw.md`
- Create: `docs/research/gemini_lead_format_raw.md`

**Step 1: Send Research Task 1 — Data Source Discovery**

```bash
gemini "You are a research analyst specializing in real estate data and web scraping. Research the best scrapeable data sources for tracking new residential home construction activity along Colorado's Front Range corridor (Denver, Jefferson, Adams, Arapahoe, Boulder, Douglas, Larimer, Weld, El Paso, Broomfield counties).

For EACH source you find, document in a markdown table:
- Source name and URL
- Data type (permits, zoning, assessor records, construction activity, etc.)
- Access method (public website, API, RSS feed, FOIA-requestable, paid)
- Scraping complexity (static HTML, JavaScript-rendered, PDF, API with auth)
- Update frequency (daily, weekly, monthly)
- Geographic coverage (which specific Front Range counties/municipalities)
- Data quality and reliability rating (1-5, with justification)

Investigate ALL of these categories:
1. County building permit databases (all 10 Front Range counties listed above)
2. Municipal planning and zoning commission agendas/minutes
3. County assessor and property records
4. Colorado DORA (Division of Real Estate) filings
5. USPS new address delivery data
6. Census Bureau building permits survey
7. Utility connection applications (water, electric, gas)
8. Environmental impact assessments / NEPA filings
9. Colorado DOT road/infrastructure projects near developments
10. MLS new construction listings
11. Developer/builder websites and press releases
12. SEC filings for publicly traded homebuilders (Lennar, DR Horton, KB Home, etc.)
13. Local business journal coverage (Denver Business Journal, etc.)
14. Social media signals (LinkedIn builder activity, planning commission discussions)
15. Satellite/aerial imagery change detection services
16. RSS feeds from county/city planning departments

ALSO investigate non-obvious leading indicators:
- Water rights transfers
- School district enrollment projections
- Traffic studies
- Soil testing permits
- Surveying company activity
- Heavy equipment rental patterns
- Material supplier delivery data
- Fiber/telecom infrastructure expansion plans

For each source, provide the ACTUAL URL where data can be accessed, not just a general description. Be specific about the access method and any authentication requirements.

Format your entire response as a structured markdown document with sections per category." > docs/research/gemini_sources_raw.md
```

**Step 2: Send Research Task 2 — Ideal Lead Record Format (parallel with Step 1)**

```bash
gemini "You are a research analyst specializing in real estate technology and CRM systems. Research what real estate firms and homebuilders expect in an actionable development lead for new residential construction. This is for a SaaS product that generates leads about new home developments.

Document the following in a structured markdown document:

## 1. Required Fields for a Development Lead
What fields make a development lead actionable? Think: location, permit numbers, developer name, project size, timeline, zoning status, etc. Be exhaustive — list every field a real estate professional would want.

## 2. Required Fields for a Builder/Developer Partnership Lead
What fields are needed when the lead is about partnering with a builder or developer? Think: company info, project pipeline, financial health, past projects, contact info.

## 3. Lead Scoring Criteria
What makes one lead more valuable than another? Research industry-standard scoring models. Consider: project size, timeline certainty, data source count, developer track record, market conditions.

## 4. Common CRM Systems
Which CRM systems do real estate firms use? For each, note:
- Market share / popularity
- API availability for integration
- Key field mappings (how our lead fields map to their CRM fields)
- Focus on: Salesforce, HubSpot, Follow Up Boss, kvCORE, Chime, LionDesk, BoomTown

## 5. Typical Lead Workflow
How does a real estate firm act on a development lead? Document the step-by-step workflow from receiving a lead to closing a deal. Include decision points and timing.

## 6. Delivery Format Preferences
What formats do firms prefer for receiving leads? Rate preference for:
- Email digest (daily/weekly summary)
- Dashboard with real-time updates
- API/webhook for CRM integration
- Slack/Teams notifications
- SMS alerts

## 7. Competitive Analysis
Analyze these existing services and what they provide:
- BuildZoom
- Construction Monitor
- PermitData
- Dodge Construction (now Dodge Construction Network)
- Any other relevant competitors

For each competitor, document: pricing model, data coverage, lead format, strengths, weaknesses, and gaps we could fill.

Be specific and cite sources where possible." > docs/research/gemini_lead_format_raw.md
```

**Step 3: Verify Gemini output was captured**

```bash
wc -l docs/research/gemini_sources_raw.md docs/research/gemini_lead_format_raw.md
```

Expected: Both files contain substantial content (50+ lines each).

**Step 4: Commit raw research**

```bash
git add docs/research/gemini_sources_raw.md docs/research/gemini_lead_format_raw.md
git commit -m "research: add raw Gemini research output

Research Task 1: Front Range data source discovery
Research Task 2: Ideal lead record format and competitive analysis"
```

---

### Task 5: Cross-Validate Source Research

Review Gemini's source findings critically. Use web search to verify the top sources actually exist and are accessible.

**Files:**
- Create: `docs/research/sources.md`

**Step 1: Web-verify Gemini's top 10 sources**

For each of the top 10 sources Gemini identified:
1. Visit the actual URL (use WebFetch)
2. Confirm the data is accessible
3. Note any discrepancies from Gemini's description
4. Rate actual scraping difficulty from firsthand observation

Flag sources that are:
- URLs that 404 or redirect to paywalls
- Described as "API" but actually require paid accounts
- Overstated in data quality or coverage
- Behind heavy anti-bot protection

**Step 2: Investigate 2-3 novel sources Gemini may have missed**

Use WebSearch to find additional sources not in Gemini's output, particularly:
- County-specific permit portals that Gemini may have listed generically
- Colorado-specific data aggregators
- Any open data portals (data.colorado.gov, etc.)

**Step 3: Create `docs/research/sources.md`**

Synthesize Gemini's research + your cross-validation into a final document with this structure:

```markdown
# Landscraper: Data Source Registry

## Validation Summary
- Sources verified: X/Y
- Sources flagged as unreliable: [list]
- Novel sources added: [list]

## Tier 1: High-Confidence Sources (verified, accessible, reliable)
[Table: source, url, data_type, access_method, complexity, frequency, coverage, quality_rating, validation_notes]

## Tier 2: Promising but Unverified
[Same table format]

## Tier 3: Experimental / Novel Indicators
[Same table format]

## Flagged / Rejected Sources
[Sources from Gemini's output that don't check out, with reasons]

## POC Priority Order
Recommended scraping implementation order for Phase 4, starting with
highest-value, lowest-complexity sources.
```

**Step 4: Commit**

```bash
git add docs/research/sources.md
git commit -m "research: synthesize and validate data source registry

Cross-validated Gemini findings with web research.
Tiered source classification with POC priority order."
```

---

### Task 6: Synthesize Lead Format Research

Review Gemini's lead format research and create the final specification.

**Files:**
- Create: `docs/research/lead_format.md`

**Step 1: Review Gemini's lead format output**

Read `docs/research/gemini_lead_format_raw.md` and evaluate:
- Are the required fields comprehensive?
- Does the scoring model make sense for the Front Range market?
- Are the CRM integrations realistic for a POC?
- Is the competitive analysis accurate?

**Step 2: Create `docs/research/lead_format.md`**

Synthesize into a final specification with this structure:

```markdown
# Landscraper: Lead Format Specification

## Development Lead Record
| Field | Type | Required | Description | Example |
[All fields with types, constraints, and examples]

## Builder/Developer Partnership Lead Record
| Field | Type | Required | Description | Example |
[All fields]

## Lead Scoring Model
| Factor | Weight | Scoring Criteria |
[Scoring factors with weights that sum to 100]

## CRM Integration Targets (POC)
[Top 2-3 CRMs with field mapping tables]

## Lead Lifecycle
[Workflow diagram: discovery → enrichment → scoring → delivery → feedback]

## Delivery Channels (POC)
[Email digest + Slack webhook + API endpoint specs]

## Competitive Positioning
[Summary table: us vs competitors, with gap analysis]
```

**Step 3: Commit**

```bash
git add docs/research/lead_format.md
git commit -m "research: synthesize lead format specification

Lead record schema, scoring model, CRM mappings,
and competitive positioning documented."
```

---

### Task 7: Create CLAUDE.md and Final Phase 0 Commit

**Files:**
- Create: `CLAUDE.md`

**Step 1: Create `CLAUDE.md`**

```markdown
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

- `src/landscraper/agents/` — LangGraph agent definitions and graph
- `src/landscraper/models/` — SQLAlchemy models and Pydantic schemas
- `src/landscraper/scraping/` — scraping tool implementations
- `src/landscraper/api/` — FastAPI routes
- `src/landscraper/llm/` — LLM routing (local vs cloud)
- `src/landscraper/notifications/` — email, Slack, webhook delivery
- `docs/research/` — Phase 0 research (data sources, lead format)
- `docs/plans/` — implementation plans
- `ansible/` — Ansible playbooks for Swarm deployment
- `docker/` — Dockerfile, docker-bake.hcl, dev compose

## Conventions

- All config via environment variables with `LANDSCRAPER_` prefix (see `.env.example`)
- Async-first: use async/await for DB, HTTP, and scraping operations
- All tables have `tenant_id` column for multi-tenancy
- Agent decisions are logged to `agent_runs` table for auditability
- TDD: write failing test first, then implement
- Build with Docker Bake (`docker/docker-bake.hcl`), deploy with Ansible to Swarm at 192.168.0.12
- Redis is shared from `iranwatch_default` network (db 1) — not managed by us
```

**Step 2: Commit**

```bash
git add CLAUDE.md
git commit -m "docs: add CLAUDE.md for Claude Code context"
```

**Step 3: Tag Phase 0 complete**

```bash
git tag phase-0-complete
```

---

## Subsequent Phase Roadmap

After Phase 0, proceed through these phases sequentially. Each phase will get its own detailed implementation plan.

| Phase | Description | Key Deliverables |
|-------|-------------|------------------|
| 1 | PostgreSQL Schema | Alembic migrations, SQLAlchemy models for all 8 tables |
| 2 | LangGraph Orchestrator | Agent graph definition, state schema, orchestrator agent |
| 3 | Collection Specialists | Playwright, httpx, RSS, Scrapy tool implementations; first source (county permits) |
| 4 | Data Pipeline | Correlation, aggregation, dedup, enrichment, scoring agents |
| 5 | Consensus Layer | Multi-agent validation, confidence scoring, source weighting |
| 6 | Self-Improvement | Metric tracking, strategy evaluation, source degradation monitoring |
| 7 | FastAPI Layer | REST endpoints, tenant auth, rate limiting, OpenAPI docs |
| 8 | Notifications | Email, Slack, webhook delivery; per-tenant preferences |
| 9 | Docker Bake + Ansible Swarm Deploy | Production bake targets, Ansible roles, Swarm stack configs, health checks |
| 10 | First Full Cycle | End-to-end weekly aggregation against real Front Range data |
