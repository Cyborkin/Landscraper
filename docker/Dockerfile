# Stage 1: Build dashboard
FROM node:20-slim AS frontend
WORKDIR /app/dashboard
COPY dashboard/package*.json dashboard/.npmrc ./
RUN npm ci
COPY dashboard/ ./
RUN npm run build

# Stage 2: Python app
FROM python:3.14-slim AS base
WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential curl \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml .
COPY src/ src/
COPY alembic/ alembic/
COPY alembic.ini .

RUN pip install --no-cache-dir .
RUN playwright install --with-deps chromium

# Copy dashboard build
COPY --from=frontend /app/dashboard/dist dashboard/dist

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["sh", "-c", "alembic upgrade head && uvicorn landscraper.api.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
