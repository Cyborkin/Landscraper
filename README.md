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
