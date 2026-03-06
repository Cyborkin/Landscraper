# Landscraper Dashboard — Design Document

**Goal:** Build a modern, visually compelling web-based UI for monitoring and demoing the Landscraper platform to executive leadership.

**Decision Log:**
- FastAPI-served SPA (static files via StaticFiles mount)
- Leaflet + CartoDB Dark Matter tiles (no API key dependency)
- Live API data (no seed/mock data)
- Open access (no authentication on dashboard)
- Vite + React over Next.js (simpler for static SPA, no SSR needed)

---

## Architecture

```
FastAPI (uvicorn)
  /api/v1/*          → REST API endpoints (existing)
  /dashboard/*       → Vite SPA static files
  /health            → Health check (existing)

dashboard/dist/      → Vite build output
  index.html
  assets/*.js
  assets/*.css
```

Single deployment. `npm run build` produces `dist/`, FastAPI serves via `StaticFiles` mount with `html=True` for SPA catch-all routing.

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Framework | Vite + React 18 + TypeScript |
| Styling | Tailwind CSS |
| Components | shadcn/ui (Radix primitives) |
| Charts | Tremor (DonutChart, BarChart, BarList) |
| Map | Leaflet + react-leaflet + CartoDB Dark Matter tiles |
| Pipeline Viz | React Flow |
| Data Fetching | TanStack Query (React Query) |
| Routing | React Router v6 |

## Design System — "Midnight Emerald"

Dark mode only. Optimized for executive demos on large screens.

| Role | Color | Hex |
|------|-------|-----|
| Background | Slate 950 | #020617 |
| Card/Surface | Slate 900 | #0f172a |
| Border | Slate 800 | #1e293b |
| Primary/Action | Emerald 500 | #10b981 |
| Hot Tier | Amber 400 | #fbbf24 |
| Warm Tier | Sky 400 | #38bdf8 |
| Monitor Tier | Slate 400 | #94a3b8 |
| Cold Tier | Slate 600 | #475569 |
| Error/Alert | Red 400 | #f87171 |
| Text Primary | Slate 50 | #f8fafc |
| Text Secondary | Slate 400 | #94a3b8 |

Glassmorphism card effects with subtle emerald glows on active elements.

## Layout Shell

- **Left sidebar** (collapsed, ~64px): Navigation icons, Landscraper logo at top
- **Top bar**: View title, system health dot (green/red), tracing status badge, cycle status pill
- **Main content area**: Full width, scrollable

## Views

### View 1: Executive KPI Dashboard (`/dashboard`)

Landing page. Answers "so what?" in 3 seconds.

**Hero metrics row** — 4 stat cards:
- Total Leads (count + trend)
- Hot Leads (count, amber glow)
- Pipeline Value (sum of valuation_usd, formatted $12.4M)
- Avg Confidence (percentage with color ring)

**Charts row:**
- Tier Distribution — Tremor DonutChart (4 tiers with tier colors)
- Lead Score Distribution — Tremor BarChart (histogram: 0-20, 20-40, 40-60, 60-80, 80-100)
- County Heatmap — Tremor BarList (lead count by county, sorted desc)

**Recent Activity** — Last 10 leads: tier badge + city + score + timestamp

### View 2: Lead Explorer (`/dashboard/leads`)

**Top half:** Leaflet map
- CartoDB Dark Matter tiles
- Zoomed to Colorado Front Range (~39.5-40.7N, -105.3 to -104.5W)
- Circle markers color-coded by tier
- Marker clustering (leaflet.markercluster)
- Click marker → highlight table row + popup

**Filter bar:**
- Tier multi-select, County multi-select, Min score slider, Property type dropdown

**Bottom half:** shadcn/ui DataTable
- Columns: Score (color bar), Tier (badge), City, County, Property Type, Confidence, Valuation
- Sortable, clickable rows → navigate to detail

### View 3: Lead Detail (`/dashboard/leads/:id`)

**Header:** Lead name, tier badge, score (large), confidence meter

**Left column:**
- Scoring Breakdown — Radar chart showing 10 factors (Scale, Permit Status, Units, Property Type, Location, Owner Type, Contacts, Recency, Confidence, Sources)
- Source Corroboration — Source list with badges

**Right column:**
- Location Card — Mini map + full address
- Permit Info — Number, type, status, jurisdiction, filing date
- Project Details — Property type, units, sqft, valuation
- Stakeholders — Owner, applicant, contractor, architect

### View 4: Pipeline Monitor (`/dashboard/pipeline`)

**React Flow diagram** — Horizontal left-to-right:

```
[Source Discovery] → [Collection Specialists] → [Data Pipeline] → [Consensus] → [Self-Improvement] → [Delivery]
                        |- Census BPS
                        |- SODA Permits
                        |- SEC EDGAR          (fan-out group node)
                        |- RSS Feeds
                        |- HTTP Generic
```

- Dot grid background (#1e293b)
- Node states: Idle (dim/slate), Active (emerald border + pulse glow + animated edges), Complete (emerald + checkmark)
- Animated marching-ant edges during active cycle
- Stage labels ("ST-01"..."ST-06") in monospace

**Sidebar panel (right):**
- Trigger Cycle button
- Cycle status + phase indicator
- Metrics when complete: raw records, developments, validated leads, yield/conversion/error rates, tier distribution mini-chart

## Data Flow

```
TanStack Query hooks:
  useLeads(filters)     → GET /api/v1/leads?tier=...&county=...
  useLead(id)           → GET /api/v1/leads/:id
  useCycleStatus()      → GET /api/v1/cycle/status  (poll 5s during active cycle)
  useTriggerCycle()     → POST /api/v1/cycle/trigger
  useHealth()           → GET /health               (poll 30s)
  useTracingStatus()    → GET /api/v1/tracing/status
```

API key (`landscraper-poc-key`) configured in Vite env file, sent as Bearer token on all requests.

## Build & Deployment

```bash
# Dev: Vite dev server with proxy to FastAPI
cd dashboard && npm run dev

# Prod: build static files
cd dashboard && npm run build  # → dashboard/dist/

# FastAPI mount
app.mount("/dashboard", StaticFiles(directory="dashboard/dist", html=True))
```

Docker: multi-stage build (Node for frontend, Python for backend). Single image.
Ansible deploys to Swarm at 192.168.0.12.
