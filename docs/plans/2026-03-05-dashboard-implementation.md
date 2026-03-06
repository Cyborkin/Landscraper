# Landscraper Dashboard Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a Vite + React dashboard served by FastAPI for monitoring and demoing Landscraper to executive leadership.

**Architecture:** Single-deployment SPA. Vite builds static files to `dashboard/dist/`, FastAPI serves them via `StaticFiles` mount. TanStack Query polls the existing REST API. Four views: KPI Dashboard, Lead Explorer (table + map), Lead Detail, Pipeline Monitor.

**Tech Stack:** Vite, React 18, TypeScript, Tailwind CSS v4, shadcn/ui, Tremor, Leaflet, React Flow, TanStack Query, React Router v6, Recharts (radar chart)

---

### Task 1: Backend — Add CORS and score_breakdown to API

**Files:**
- Modify: `src/landscraper/api/main.py`
- Modify: `src/landscraper/api/schemas.py`
- Modify: `tests/test_api.py`

**Step 1: Add `score_breakdown` to `LeadOut` schema**

In `src/landscraper/api/schemas.py`, add the field to `LeadOut`:

```python
class LeadOut(BaseModel):
    lead_id: str
    confidence_score: float = 0.0
    source_count: int = 0
    sources: list[str] = []
    lead_score: int = 0
    tier: str = "cold"
    score_breakdown: dict[str, int] = {}   # <-- ADD THIS LINE
    permit_number: str | None = None
    # ... rest unchanged
```

**Step 2: Pass `score_breakdown` through `_to_lead_out`**

In `src/landscraper/api/main.py`, add to the `_to_lead_out` function:

```python
def _to_lead_out(lead: dict[str, Any]) -> LeadOut:
    return LeadOut(
        lead_id=lead.get("lead_id", ""),
        confidence_score=lead.get("confidence_score", 0.0),
        source_count=lead.get("source_count", 0),
        sources=lead.get("sources", []),
        lead_score=lead.get("lead_score", 0),
        tier=lead.get("tier", "cold"),
        score_breakdown=lead.get("score_breakdown", {}),   # <-- ADD THIS LINE
        # ... rest unchanged
    )
```

**Step 3: Add CORS middleware**

In `src/landscraper/api/main.py`, after the `app = FastAPI(...)` block, add:

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Vite dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**Step 4: Write test for score_breakdown**

In `tests/test_api.py`, add:

```python
def test_lead_includes_score_breakdown():
    store_leads([{
        "lead_id": "bd-test",
        "tier": "hot",
        "lead_score": 85,
        "score_breakdown": {"project_scale": 20, "permit_status": 15, "unit_count": 10},
    }])

    response = client.get("/api/v1/leads/bd-test", headers=AUTH_HEADER)
    data = response.json()
    assert data["score_breakdown"]["project_scale"] == 20
    assert data["score_breakdown"]["permit_status"] == 15
```

**Step 5: Run tests**

Run: `.venv/bin/pytest tests/test_api.py -v`
Expected: ALL PASS

**Step 6: Commit**

```bash
git add src/landscraper/api/schemas.py src/landscraper/api/main.py tests/test_api.py
git commit -m "feat: add CORS middleware and score_breakdown to lead API"
```

---

### Task 2: Scaffold Vite + React project

**Files:**
- Create: `dashboard/` (entire directory via npm create)
- Create: `dashboard/vite.config.ts`
- Create: `dashboard/src/index.css`

**Step 1: Create Vite project**

```bash
cd /Users/dustinmaselbas/programming/project_hunterd
npm create vite@latest dashboard -- --template react-ts
```

**Step 2: Install dependencies**

```bash
cd dashboard

npm install @tanstack/react-query react-router-dom recharts @tremor/react \
  leaflet react-leaflet @xyflow/react lucide-react clsx tailwind-merge \
  class-variance-authority

npm install -D tailwindcss @tailwindcss/vite @types/leaflet @types/node
```

**Step 3: Configure Vite**

Replace `dashboard/vite.config.ts`:

```typescript
import path from "path";
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";

export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  base: "/dashboard/",
  server: {
    port: 3000,
    proxy: {
      "/api": {
        target: "http://localhost:8000",
        changeOrigin: true,
      },
      "/health": {
        target: "http://localhost:8000",
        changeOrigin: true,
      },
    },
  },
});
```

**Step 4: Configure Tailwind v4 theme**

Replace `dashboard/src/index.css`:

```css
@import "tailwindcss";

@theme {
  --color-background: #020617;
  --color-surface: #0f172a;
  --color-border: #1e293b;
  --color-primary: #10b981;
  --color-hot: #fbbf24;
  --color-warm: #38bdf8;
  --color-monitor: #94a3b8;
  --color-cold: #475569;
  --color-error: #f87171;
  --color-text-primary: #f8fafc;
  --color-text-secondary: #94a3b8;

  --radius-lg: 0.5rem;
  --radius-md: calc(0.5rem - 2px);
  --radius-sm: calc(0.5rem - 4px);
}

@layer base {
  body {
    background-color: var(--color-background);
    color: var(--color-text-primary);
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
  }
}
```

**Step 5: Update tsconfig for path aliases**

In `dashboard/tsconfig.app.json`, add to `compilerOptions`:

```json
{
  "compilerOptions": {
    "baseUrl": ".",
    "paths": {
      "@/*": ["./src/*"]
    }
  }
}
```

**Step 6: Verify it builds**

```bash
cd dashboard && npm run build
```

Expected: Build succeeds, `dashboard/dist/` created

**Step 7: Commit**

```bash
cd /Users/dustinmaselbas/programming/project_hunterd
git add dashboard/
git commit -m "feat: scaffold Vite + React dashboard with Tailwind v4"
```

---

### Task 3: API client and TanStack Query hooks

**Files:**
- Create: `dashboard/src/lib/api.ts`
- Create: `dashboard/src/lib/hooks.ts`
- Create: `dashboard/src/lib/types.ts`

**Step 1: Create TypeScript types**

Create `dashboard/src/lib/types.ts`:

```typescript
export interface Address {
  street: string | null;
  city: string | null;
  state: string | null;
  zip: string | null;
  county: string | null;
}

export interface Coordinates {
  latitude: number | null;
  longitude: number | null;
}

export interface Lead {
  lead_id: string;
  confidence_score: number;
  source_count: number;
  sources: string[];
  lead_score: number;
  tier: "hot" | "warm" | "monitor" | "cold";
  score_breakdown: Record<string, number>;
  permit_number: string | null;
  permit_type: string | null;
  permit_status: string | null;
  jurisdiction: string | null;
  address: Address;
  coordinates: Coordinates;
  property_type: string | null;
  project_name: string | null;
  description: string | null;
  valuation_usd: number | null;
  unit_count: number | null;
  total_sqft: number | null;
  owner_name: string | null;
  filing_date: string | null;
  discovered_at: string | null;
  updated_at: string | null;
  tags: string[];
  validation_status: string | null;
}

export interface PaginationMeta {
  total_count: number;
  page: number;
  page_size: number;
  next_page_url: string | null;
}

export interface LeadListResponse {
  meta: PaginationMeta;
  leads: Lead[];
}

export interface HealthResponse {
  status: string;
  version: string;
  cycle_count: number;
}

export interface CycleStatus {
  cycle_id: string | null;
  status: string;
  metrics: Record<string, unknown>;
}

export interface TracingStatus {
  enabled: boolean;
  project: string | null;
}

export interface LeadFilters {
  tier?: string;
  county?: string;
  min_score?: number;
  property_type?: string;
  page?: number;
  page_size?: number;
}

export interface TierDistribution {
  hot: number;
  warm: number;
  monitor: number;
  cold: number;
}

export interface CycleMetrics {
  total_raw_records: number;
  total_developments: number;
  total_validated_leads: number;
  total_errors: number;
  yield_rate: number;
  conversion_rate: number;
  error_rate: number;
  unique_source_count: number;
  tier_distribution: TierDistribution;
  avg_confidence: number;
  avg_lead_score: number;
}
```

**Step 2: Create API client**

Create `dashboard/src/lib/api.ts`:

```typescript
import type {
  CycleStatus,
  HealthResponse,
  Lead,
  LeadFilters,
  LeadListResponse,
  TracingStatus,
} from "./types";

const API_KEY = "landscraper-poc-key";

const headers: Record<string, string> = {
  Authorization: `Bearer ${API_KEY}`,
  "Content-Type": "application/json",
};

async function fetchApi<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(path, { ...init, headers: { ...headers, ...init?.headers } });
  if (!res.ok) {
    throw new Error(`API error: ${res.status} ${res.statusText}`);
  }
  return res.json();
}

export async function fetchHealth(): Promise<HealthResponse> {
  return fetchApi("/health");
}

export async function fetchLeads(filters: LeadFilters = {}): Promise<LeadListResponse> {
  const params = new URLSearchParams();
  if (filters.tier) params.set("tier", filters.tier);
  if (filters.county) params.set("county", filters.county);
  if (filters.min_score) params.set("min_score", String(filters.min_score));
  if (filters.property_type) params.set("property_type", filters.property_type);
  if (filters.page) params.set("page", String(filters.page));
  if (filters.page_size) params.set("page_size", String(filters.page_size));
  const qs = params.toString();
  return fetchApi(`/api/v1/leads${qs ? `?${qs}` : ""}`);
}

export async function fetchLead(leadId: string): Promise<Lead> {
  return fetchApi(`/api/v1/leads/${leadId}`);
}

export async function fetchCycleStatus(): Promise<CycleStatus> {
  return fetchApi("/api/v1/cycle/status");
}

export async function triggerCycle(): Promise<CycleStatus> {
  return fetchApi("/api/v1/cycle/trigger", {
    method: "POST",
    body: JSON.stringify({ sources: null }),
  });
}

export async function fetchTracingStatus(): Promise<TracingStatus> {
  return fetchApi("/api/v1/tracing/status");
}
```

**Step 3: Create TanStack Query hooks**

Create `dashboard/src/lib/hooks.ts`:

```typescript
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  fetchHealth,
  fetchLeads,
  fetchLead,
  fetchCycleStatus,
  triggerCycle,
  fetchTracingStatus,
} from "./api";
import type { LeadFilters } from "./types";

export function useHealth() {
  return useQuery({
    queryKey: ["health"],
    queryFn: fetchHealth,
    refetchInterval: 30_000,
  });
}

export function useLeads(filters: LeadFilters = {}) {
  return useQuery({
    queryKey: ["leads", filters],
    queryFn: () => fetchLeads(filters),
  });
}

export function useLead(leadId: string) {
  return useQuery({
    queryKey: ["lead", leadId],
    queryFn: () => fetchLead(leadId),
    enabled: !!leadId,
  });
}

export function useCycleStatus() {
  return useQuery({
    queryKey: ["cycleStatus"],
    queryFn: fetchCycleStatus,
    refetchInterval: (query) => {
      const status = query.state.data?.status;
      return status === "triggered" || status === "in_progress" ? 5_000 : 30_000;
    },
  });
}

export function useTriggerCycle() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: triggerCycle,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["cycleStatus"] });
    },
  });
}

export function useTracingStatus() {
  return useQuery({
    queryKey: ["tracingStatus"],
    queryFn: fetchTracingStatus,
  });
}
```

**Step 4: Verify build**

```bash
cd dashboard && npm run build
```

Expected: Build succeeds

**Step 5: Commit**

```bash
cd /Users/dustinmaselbas/programming/project_hunterd
git add dashboard/src/lib/
git commit -m "feat: add TypeScript API client and TanStack Query hooks"
```

---

### Task 4: React Router + Layout Shell

**Files:**
- Create: `dashboard/src/components/Layout.tsx`
- Create: `dashboard/src/pages/Dashboard.tsx` (placeholder)
- Create: `dashboard/src/pages/LeadExplorer.tsx` (placeholder)
- Create: `dashboard/src/pages/LeadDetail.tsx` (placeholder)
- Create: `dashboard/src/pages/Pipeline.tsx` (placeholder)
- Modify: `dashboard/src/App.tsx`
- Modify: `dashboard/src/main.tsx`

**Step 1: Create Layout shell**

Create `dashboard/src/components/Layout.tsx`:

```tsx
import { NavLink, Outlet } from "react-router-dom";
import {
  LayoutDashboard,
  Search,
  GitBranch,
} from "lucide-react";
import { useHealth, useTracingStatus, useCycleStatus } from "@/lib/hooks";

const NAV_ITEMS = [
  { to: "/dashboard", icon: LayoutDashboard, label: "Dashboard" },
  { to: "/dashboard/leads", icon: Search, label: "Leads" },
  { to: "/dashboard/pipeline", icon: GitBranch, label: "Pipeline" },
];

function StatusDot({ ok }: { ok: boolean }) {
  return (
    <span
      className={`inline-block h-2 w-2 rounded-full ${ok ? "bg-primary" : "bg-error"}`}
    />
  );
}

export default function Layout() {
  const health = useHealth();
  const tracing = useTracingStatus();
  const cycle = useCycleStatus();

  const isHealthy = health.data?.status === "ok";
  const tracingEnabled = tracing.data?.enabled ?? false;
  const cycleStatus = cycle.data?.status ?? "idle";

  return (
    <div className="flex h-screen overflow-hidden">
      {/* Sidebar */}
      <aside className="flex w-16 flex-col items-center gap-4 border-r border-border bg-surface py-4">
        <div className="mb-4 text-xl font-bold text-primary">L</div>
        {NAV_ITEMS.map(({ to, icon: Icon, label }) => (
          <NavLink
            key={to}
            to={to}
            end={to === "/dashboard"}
            className={({ isActive }) =>
              `flex h-10 w-10 items-center justify-center rounded-lg transition-colors ${
                isActive
                  ? "bg-primary/10 text-primary"
                  : "text-text-secondary hover:bg-border hover:text-text-primary"
              }`
            }
            title={label}
          >
            <Icon size={20} />
          </NavLink>
        ))}
      </aside>

      {/* Main area */}
      <div className="flex flex-1 flex-col overflow-hidden">
        {/* Top bar */}
        <header className="flex h-12 items-center justify-between border-b border-border bg-surface px-6">
          <h1 className="text-sm font-semibold tracking-wide text-text-secondary uppercase">
            Landscraper
          </h1>
          <div className="flex items-center gap-4 text-xs">
            <div className="flex items-center gap-1.5">
              <StatusDot ok={isHealthy} />
              <span className="text-text-secondary">System</span>
            </div>
            <div className="flex items-center gap-1.5">
              <StatusDot ok={tracingEnabled} />
              <span className="text-text-secondary">Tracing</span>
            </div>
            <div
              className={`rounded-full px-2.5 py-0.5 text-xs font-medium ${
                cycleStatus === "idle"
                  ? "bg-border text-text-secondary"
                  : cycleStatus === "triggered"
                    ? "bg-primary/20 text-primary"
                    : "bg-hot/20 text-hot"
              }`}
            >
              {cycleStatus}
            </div>
          </div>
        </header>

        {/* Content */}
        <main className="flex-1 overflow-y-auto p-6">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
```

**Step 2: Create placeholder pages**

Create `dashboard/src/pages/Dashboard.tsx`:

```tsx
export default function Dashboard() {
  return <div className="text-text-secondary">KPI Dashboard — coming soon</div>;
}
```

Create `dashboard/src/pages/LeadExplorer.tsx`:

```tsx
export default function LeadExplorer() {
  return <div className="text-text-secondary">Lead Explorer — coming soon</div>;
}
```

Create `dashboard/src/pages/LeadDetail.tsx`:

```tsx
import { useParams } from "react-router-dom";

export default function LeadDetail() {
  const { leadId } = useParams<{ leadId: string }>();
  return <div className="text-text-secondary">Lead Detail: {leadId}</div>;
}
```

Create `dashboard/src/pages/Pipeline.tsx`:

```tsx
export default function Pipeline() {
  return <div className="text-text-secondary">Pipeline Monitor — coming soon</div>;
}
```

**Step 3: Wire up App.tsx with Router**

Replace `dashboard/src/App.tsx`:

```tsx
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import Layout from "@/components/Layout";
import Dashboard from "@/pages/Dashboard";
import LeadExplorer from "@/pages/LeadExplorer";
import LeadDetail from "@/pages/LeadDetail";
import Pipeline from "@/pages/Pipeline";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      staleTime: 10_000,
    },
  },
});

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          <Route element={<Layout />}>
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/dashboard/leads" element={<LeadExplorer />} />
            <Route path="/dashboard/leads/:leadId" element={<LeadDetail />} />
            <Route path="/dashboard/pipeline" element={<Pipeline />} />
          </Route>
          <Route path="*" element={<Navigate to="/dashboard" replace />} />
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  );
}
```

**Step 4: Update main.tsx**

Replace `dashboard/src/main.tsx`:

```tsx
import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import "./index.css";
import App from "./App";

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <App />
  </StrictMode>,
);
```

**Step 5: Verify dev server runs**

```bash
cd dashboard && npm run dev
```

Visit `http://localhost:3000/dashboard` — should see sidebar + top bar + placeholder content.

**Step 6: Verify build**

```bash
cd dashboard && npm run build
```

**Step 7: Commit**

```bash
cd /Users/dustinmaselbas/programming/project_hunterd
git add dashboard/src/
git commit -m "feat: add React Router layout shell with sidebar and top bar"
```

---

### Task 5: Shared UI components (tier badge, stat card, section header)

**Files:**
- Create: `dashboard/src/components/TierBadge.tsx`
- Create: `dashboard/src/components/StatCard.tsx`

**Step 1: Create TierBadge**

Create `dashboard/src/components/TierBadge.tsx`:

```tsx
const TIER_STYLES: Record<string, string> = {
  hot: "bg-hot/20 text-hot",
  warm: "bg-warm/20 text-warm",
  monitor: "bg-monitor/20 text-monitor",
  cold: "bg-cold/20 text-cold",
};

export default function TierBadge({ tier }: { tier: string }) {
  return (
    <span
      className={`inline-block rounded-full px-2.5 py-0.5 text-xs font-semibold uppercase tracking-wide ${
        TIER_STYLES[tier] ?? TIER_STYLES.cold
      }`}
    >
      {tier}
    </span>
  );
}
```

**Step 2: Create StatCard**

Create `dashboard/src/components/StatCard.tsx`:

```tsx
interface StatCardProps {
  label: string;
  value: string | number;
  accent?: string; // tailwind color class e.g. "text-hot"
}

export default function StatCard({ label, value, accent }: StatCardProps) {
  return (
    <div className="rounded-xl border border-border bg-surface p-5">
      <p className="text-xs font-medium uppercase tracking-wide text-text-secondary">
        {label}
      </p>
      <p className={`mt-1 text-3xl font-bold ${accent ?? "text-text-primary"}`}>
        {value}
      </p>
    </div>
  );
}
```

**Step 3: Verify build**

```bash
cd dashboard && npm run build
```

**Step 4: Commit**

```bash
cd /Users/dustinmaselbas/programming/project_hunterd
git add dashboard/src/components/TierBadge.tsx dashboard/src/components/StatCard.tsx
git commit -m "feat: add TierBadge and StatCard shared components"
```

---

### Task 6: KPI Dashboard view

**Files:**
- Modify: `dashboard/src/pages/Dashboard.tsx`

**Step 1: Implement the KPI Dashboard**

Replace `dashboard/src/pages/Dashboard.tsx`:

```tsx
import { useLeads } from "@/lib/hooks";
import StatCard from "@/components/StatCard";
import TierBadge from "@/components/TierBadge";
import { DonutChart, BarChart, BarList } from "@tremor/react";
import type { Lead } from "@/lib/types";

function formatUsd(val: number): string {
  if (val >= 1_000_000) return `$${(val / 1_000_000).toFixed(1)}M`;
  if (val >= 1_000) return `$${(val / 1_000).toFixed(0)}K`;
  return `$${val}`;
}

export default function Dashboard() {
  const { data, isLoading } = useLeads({ page_size: 200 });

  if (isLoading) {
    return <div className="text-text-secondary">Loading...</div>;
  }

  const leads = data?.leads ?? [];
  const totalLeads = data?.meta.total_count ?? 0;

  // Compute KPIs
  const hotCount = leads.filter((l) => l.tier === "hot").length;
  const pipelineValue = leads.reduce((sum, l) => sum + (l.valuation_usd ?? 0), 0);
  const avgConfidence =
    leads.length > 0
      ? leads.reduce((sum, l) => sum + l.confidence_score, 0) / leads.length
      : 0;

  // Tier distribution for donut
  const tierData = [
    { name: "Hot", value: leads.filter((l) => l.tier === "hot").length, color: "amber" },
    { name: "Warm", value: leads.filter((l) => l.tier === "warm").length, color: "sky" },
    { name: "Monitor", value: leads.filter((l) => l.tier === "monitor").length, color: "slate" },
    { name: "Cold", value: leads.filter((l) => l.tier === "cold").length, color: "zinc" },
  ].filter((d) => d.value > 0);

  // Score distribution for bar chart
  const scoreBuckets = [
    { range: "0-19", count: 0 },
    { range: "20-39", count: 0 },
    { range: "40-59", count: 0 },
    { range: "60-79", count: 0 },
    { range: "80-100", count: 0 },
  ];
  for (const lead of leads) {
    const idx = Math.min(Math.floor(lead.lead_score / 20), 4);
    scoreBuckets[idx].count++;
  }

  // County distribution for bar list
  const countyCounts: Record<string, number> = {};
  for (const lead of leads) {
    const county = lead.address?.county ?? "Unknown";
    countyCounts[county] = (countyCounts[county] ?? 0) + 1;
  }
  const countyData = Object.entries(countyCounts)
    .map(([name, value]) => ({ name, value }))
    .sort((a, b) => b.value - a.value)
    .slice(0, 10);

  // Recent leads (last 10)
  const recentLeads = [...leads]
    .sort((a, b) => {
      const da = a.discovered_at ?? "";
      const db = b.discovered_at ?? "";
      return db.localeCompare(da);
    })
    .slice(0, 10);

  return (
    <div className="space-y-6">
      {/* Hero metrics */}
      <div className="grid grid-cols-4 gap-4">
        <StatCard label="Total Leads" value={totalLeads} />
        <StatCard label="Hot Leads" value={hotCount} accent="text-hot" />
        <StatCard label="Pipeline Value" value={formatUsd(pipelineValue)} accent="text-primary" />
        <StatCard
          label="Avg Confidence"
          value={`${(avgConfidence * 100).toFixed(0)}%`}
          accent={avgConfidence >= 0.7 ? "text-primary" : "text-text-secondary"}
        />
      </div>

      {/* Charts */}
      <div className="grid grid-cols-3 gap-4">
        {/* Tier Distribution Donut */}
        <div className="rounded-xl border border-border bg-surface p-5">
          <h3 className="mb-3 text-sm font-medium text-text-secondary">
            Tier Distribution
          </h3>
          <DonutChart
            data={tierData}
            category="value"
            index="name"
            colors={["amber", "sky", "slate", "zinc"]}
            showLabel
            className="h-48"
          />
        </div>

        {/* Score Distribution Bar */}
        <div className="rounded-xl border border-border bg-surface p-5">
          <h3 className="mb-3 text-sm font-medium text-text-secondary">
            Score Distribution
          </h3>
          <BarChart
            data={scoreBuckets}
            index="range"
            categories={["count"]}
            colors={["emerald"]}
            showLegend={false}
            className="h-48"
          />
        </div>

        {/* County Heatmap */}
        <div className="rounded-xl border border-border bg-surface p-5">
          <h3 className="mb-3 text-sm font-medium text-text-secondary">
            Leads by County
          </h3>
          <BarList data={countyData} color="emerald" className="mt-2" />
        </div>
      </div>

      {/* Recent Activity */}
      <div className="rounded-xl border border-border bg-surface p-5">
        <h3 className="mb-3 text-sm font-medium text-text-secondary">
          Recent Activity
        </h3>
        <div className="space-y-2">
          {recentLeads.map((lead) => (
            <RecentLeadRow key={lead.lead_id} lead={lead} />
          ))}
          {recentLeads.length === 0 && (
            <p className="text-sm text-text-secondary">No leads discovered yet.</p>
          )}
        </div>
      </div>
    </div>
  );
}

function RecentLeadRow({ lead }: { lead: Lead }) {
  return (
    <div className="flex items-center justify-between rounded-lg px-3 py-2 hover:bg-border/50">
      <div className="flex items-center gap-3">
        <TierBadge tier={lead.tier} />
        <span className="text-sm text-text-primary">
          {lead.project_name ?? lead.permit_number ?? lead.lead_id.slice(0, 8)}
        </span>
        <span className="text-xs text-text-secondary">
          {lead.address?.city ?? ""}{lead.address?.county ? `, ${lead.address.county}` : ""}
        </span>
      </div>
      <div className="flex items-center gap-4">
        <span className="text-sm font-semibold text-text-primary">{lead.lead_score}</span>
        <span className="text-xs text-text-secondary">
          {lead.discovered_at ? new Date(lead.discovered_at).toLocaleDateString() : ""}
        </span>
      </div>
    </div>
  );
}
```

**Step 2: Verify dev server**

```bash
cd dashboard && npm run dev
```

Visit `http://localhost:3000/dashboard` — KPI cards should render (with zeros if no API data yet).

**Step 3: Verify build**

```bash
cd dashboard && npm run build
```

**Step 4: Commit**

```bash
cd /Users/dustinmaselbas/programming/project_hunterd
git add dashboard/src/pages/Dashboard.tsx
git commit -m "feat: implement KPI dashboard with tier donut, score histogram, county bar list"
```

---

### Task 7: Lead Explorer — table with filters

**Files:**
- Modify: `dashboard/src/pages/LeadExplorer.tsx`

**Step 1: Implement Lead Explorer with filters and table**

Replace `dashboard/src/pages/LeadExplorer.tsx`:

```tsx
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useLeads } from "@/lib/hooks";
import TierBadge from "@/components/TierBadge";
import type { LeadFilters } from "@/lib/types";

const TIERS = ["", "hot", "warm", "monitor", "cold"];
const COUNTIES = [
  "",
  "Adams",
  "Arapahoe",
  "Boulder",
  "Broomfield",
  "Denver",
  "Douglas",
  "El Paso",
  "Jefferson",
  "Larimer",
  "Weld",
];

export default function LeadExplorer() {
  const navigate = useNavigate();
  const [filters, setFilters] = useState<LeadFilters>({ page_size: 50 });
  const { data, isLoading } = useLeads(filters);

  const leads = data?.leads ?? [];

  return (
    <div className="space-y-4">
      {/* Filter bar */}
      <div className="flex items-center gap-3 rounded-xl border border-border bg-surface p-3">
        <Select
          label="Tier"
          value={filters.tier ?? ""}
          options={TIERS.map((t) => ({ value: t, label: t || "All Tiers" }))}
          onChange={(v) => setFilters((f) => ({ ...f, tier: v || undefined }))}
        />
        <Select
          label="County"
          value={filters.county ?? ""}
          options={COUNTIES.map((c) => ({ value: c, label: c || "All Counties" }))}
          onChange={(v) => setFilters((f) => ({ ...f, county: v || undefined }))}
        />
        <div className="flex items-center gap-2">
          <label className="text-xs text-text-secondary">Min Score</label>
          <input
            type="range"
            min={0}
            max={100}
            step={5}
            value={filters.min_score ?? 0}
            onChange={(e) =>
              setFilters((f) => ({ ...f, min_score: Number(e.target.value) || undefined }))
            }
            className="w-24 accent-primary"
          />
          <span className="w-6 text-xs text-text-secondary">{filters.min_score ?? 0}</span>
        </div>
      </div>

      {/* Results count */}
      <div className="text-xs text-text-secondary">
        {data?.meta.total_count ?? 0} leads found
      </div>

      {/* Table */}
      <div className="overflow-hidden rounded-xl border border-border bg-surface">
        <table className="w-full text-left text-sm">
          <thead>
            <tr className="border-b border-border text-xs uppercase text-text-secondary">
              <th className="px-4 py-3">Score</th>
              <th className="px-4 py-3">Tier</th>
              <th className="px-4 py-3">City</th>
              <th className="px-4 py-3">County</th>
              <th className="px-4 py-3">Type</th>
              <th className="px-4 py-3">Confidence</th>
              <th className="px-4 py-3">Valuation</th>
            </tr>
          </thead>
          <tbody>
            {isLoading ? (
              <tr>
                <td colSpan={7} className="px-4 py-8 text-center text-text-secondary">
                  Loading...
                </td>
              </tr>
            ) : leads.length === 0 ? (
              <tr>
                <td colSpan={7} className="px-4 py-8 text-center text-text-secondary">
                  No leads match the current filters.
                </td>
              </tr>
            ) : (
              leads.map((lead) => (
                <tr
                  key={lead.lead_id}
                  onClick={() => navigate(`/dashboard/leads/${lead.lead_id}`)}
                  className="cursor-pointer border-b border-border/50 transition-colors hover:bg-border/30"
                >
                  <td className="px-4 py-3">
                    <ScoreBar score={lead.lead_score} />
                  </td>
                  <td className="px-4 py-3">
                    <TierBadge tier={lead.tier} />
                  </td>
                  <td className="px-4 py-3 text-text-primary">
                    {lead.address?.city ?? "—"}
                  </td>
                  <td className="px-4 py-3 text-text-secondary">
                    {lead.address?.county ?? "—"}
                  </td>
                  <td className="px-4 py-3 text-text-secondary">
                    {lead.property_type ?? "—"}
                  </td>
                  <td className="px-4 py-3 text-text-secondary">
                    {(lead.confidence_score * 100).toFixed(0)}%
                  </td>
                  <td className="px-4 py-3 text-text-secondary">
                    {lead.valuation_usd
                      ? `$${(lead.valuation_usd / 1_000_000).toFixed(1)}M`
                      : "—"}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function ScoreBar({ score }: { score: number }) {
  const color =
    score >= 80
      ? "bg-hot"
      : score >= 50
        ? "bg-warm"
        : score >= 20
          ? "bg-monitor"
          : "bg-cold";
  return (
    <div className="flex items-center gap-2">
      <div className="h-1.5 w-16 overflow-hidden rounded-full bg-border">
        <div className={`h-full rounded-full ${color}`} style={{ width: `${score}%` }} />
      </div>
      <span className="text-xs font-semibold text-text-primary">{score}</span>
    </div>
  );
}

function Select({
  label,
  value,
  options,
  onChange,
}: {
  label: string;
  value: string;
  options: { value: string; label: string }[];
  onChange: (v: string) => void;
}) {
  return (
    <div className="flex items-center gap-2">
      <label className="text-xs text-text-secondary">{label}</label>
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="rounded-md border border-border bg-background px-2 py-1 text-xs text-text-primary focus:border-primary focus:outline-none"
      >
        {options.map((o) => (
          <option key={o.value} value={o.value}>
            {o.label}
          </option>
        ))}
      </select>
    </div>
  );
}
```

**Step 2: Verify in dev server**

```bash
cd dashboard && npm run dev
```

Visit `http://localhost:3000/dashboard/leads`

**Step 3: Commit**

```bash
cd /Users/dustinmaselbas/programming/project_hunterd
git add dashboard/src/pages/LeadExplorer.tsx
git commit -m "feat: implement Lead Explorer table with tier/county/score filters"
```

---

### Task 8: Lead Explorer — Leaflet map

**Files:**
- Create: `dashboard/src/components/LeadMap.tsx`
- Modify: `dashboard/src/pages/LeadExplorer.tsx`

**Step 1: Create LeadMap component**

Create `dashboard/src/components/LeadMap.tsx`:

```tsx
import { MapContainer, TileLayer, CircleMarker, Popup } from "react-leaflet";
import "leaflet/dist/leaflet.css";
import type { Lead } from "@/lib/types";
import TierBadge from "./TierBadge";

const TIER_COLORS: Record<string, string> = {
  hot: "#fbbf24",
  warm: "#38bdf8",
  monitor: "#94a3b8",
  cold: "#475569",
};

// Colorado Front Range bounding box center
const CENTER: [number, number] = [39.95, -104.9];
const ZOOM = 9;

// CartoDB Dark Matter tiles
const TILE_URL =
  "https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png";
const TILE_ATTR =
  '&copy; <a href="https://www.openstreetmap.org/copyright">OSM</a> &copy; <a href="https://carto.com/">CARTO</a>';

interface LeadMapProps {
  leads: Lead[];
  selectedId?: string;
  onSelect?: (leadId: string) => void;
}

export default function LeadMap({ leads, selectedId, onSelect }: LeadMapProps) {
  const mappable = leads.filter(
    (l) => l.coordinates?.latitude != null && l.coordinates?.longitude != null,
  );

  return (
    <MapContainer
      center={CENTER}
      zoom={ZOOM}
      className="h-full w-full rounded-xl"
      style={{ background: "#020617" }}
    >
      <TileLayer url={TILE_URL} attribution={TILE_ATTR} />
      {mappable.map((lead) => (
        <CircleMarker
          key={lead.lead_id}
          center={[lead.coordinates.latitude!, lead.coordinates.longitude!]}
          radius={lead.lead_id === selectedId ? 10 : 6}
          pathOptions={{
            color: TIER_COLORS[lead.tier] ?? TIER_COLORS.cold,
            fillColor: TIER_COLORS[lead.tier] ?? TIER_COLORS.cold,
            fillOpacity: lead.lead_id === selectedId ? 0.9 : 0.6,
            weight: lead.lead_id === selectedId ? 3 : 1,
          }}
          eventHandlers={{
            click: () => onSelect?.(lead.lead_id),
          }}
        >
          <Popup>
            <div className="text-sm">
              <div className="font-semibold">
                {lead.project_name ?? lead.permit_number ?? lead.lead_id.slice(0, 8)}
              </div>
              <div>Score: {lead.lead_score} | {lead.tier.toUpperCase()}</div>
              <div>{lead.address?.city}{lead.address?.county ? `, ${lead.address.county}` : ""}</div>
            </div>
          </Popup>
        </CircleMarker>
      ))}
    </MapContainer>
  );
}
```

**Step 2: Add map to LeadExplorer**

In `dashboard/src/pages/LeadExplorer.tsx`, add the map import and render it above the filter bar:

At the top, add:
```tsx
import LeadMap from "@/components/LeadMap";
```

After `const leads = data?.leads ?? [];`, add:
```tsx
const [selectedLeadId, setSelectedLeadId] = useState<string>();
```

Insert the map as the first child in the `space-y-4` div, before the filter bar:
```tsx
{/* Map */}
<div className="h-72 overflow-hidden rounded-xl border border-border">
  <LeadMap
    leads={leads}
    selectedId={selectedLeadId}
    onSelect={(id) => setSelectedLeadId(id)}
  />
</div>
```

**Step 3: Verify in dev server**

```bash
cd dashboard && npm run dev
```

Visit `http://localhost:3000/dashboard/leads` — map should render with dark tiles.

**Step 4: Commit**

```bash
cd /Users/dustinmaselbas/programming/project_hunterd
git add dashboard/src/components/LeadMap.tsx dashboard/src/pages/LeadExplorer.tsx
git commit -m "feat: add Leaflet map with CartoDB Dark Matter tiles to Lead Explorer"
```

---

### Task 9: Lead Detail view

**Files:**
- Modify: `dashboard/src/pages/LeadDetail.tsx`

**Step 1: Implement Lead Detail**

Replace `dashboard/src/pages/LeadDetail.tsx`:

```tsx
import { useParams, useNavigate } from "react-router-dom";
import { useLead } from "@/lib/hooks";
import TierBadge from "@/components/TierBadge";
import { ArrowLeft } from "lucide-react";
import {
  Radar,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  ResponsiveContainer,
} from "recharts";
import { MapContainer, TileLayer, CircleMarker } from "react-leaflet";
import "leaflet/dist/leaflet.css";

const TILE_URL = "https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png";

// Max possible values for each scoring factor (for radar chart normalization)
const FACTOR_MAX: Record<string, number> = {
  project_scale: 20,
  permit_status: 15,
  unit_count: 10,
  property_type_fit: 10,
  location_demand: 10,
  owner_entity_type: 8,
  contact_completeness: 10,
  recency: 7,
  confidence: 5,
  source_corroboration: 5,
};

const FACTOR_LABELS: Record<string, string> = {
  project_scale: "Scale",
  permit_status: "Permit",
  unit_count: "Units",
  property_type_fit: "Type Fit",
  location_demand: "Location",
  owner_entity_type: "Owner",
  contact_completeness: "Contacts",
  recency: "Recency",
  confidence: "Confidence",
  source_corroboration: "Sources",
};

export default function LeadDetail() {
  const { leadId } = useParams<{ leadId: string }>();
  const navigate = useNavigate();
  const { data: lead, isLoading, error } = useLead(leadId ?? "");

  if (isLoading) return <div className="text-text-secondary">Loading...</div>;
  if (error || !lead) return <div className="text-error">Lead not found.</div>;

  // Radar chart data
  const radarData = Object.entries(FACTOR_MAX).map(([key, max]) => ({
    factor: FACTOR_LABELS[key] ?? key,
    score: lead.score_breakdown?.[key] ?? 0,
    fullMark: max,
  }));

  const hasCoords = lead.coordinates?.latitude != null && lead.coordinates?.longitude != null;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <button
          onClick={() => navigate("/dashboard/leads")}
          className="flex h-8 w-8 items-center justify-center rounded-lg border border-border text-text-secondary hover:bg-border hover:text-text-primary"
        >
          <ArrowLeft size={16} />
        </button>
        <div className="flex-1">
          <h2 className="text-lg font-semibold text-text-primary">
            {lead.project_name ?? lead.permit_number ?? lead.lead_id.slice(0, 12)}
          </h2>
          <p className="text-xs text-text-secondary">
            {lead.address?.city}{lead.address?.county ? `, ${lead.address.county} County` : ""}
          </p>
        </div>
        <TierBadge tier={lead.tier} />
        <div className="text-right">
          <p className="text-3xl font-bold text-text-primary">{lead.lead_score}</p>
          <p className="text-xs text-text-secondary">/ 100</p>
        </div>
      </div>

      {/* Two-column layout */}
      <div className="grid grid-cols-2 gap-6">
        {/* Left: Radar + Sources */}
        <div className="space-y-4">
          <Card title="Scoring Breakdown">
            <ResponsiveContainer width="100%" height={300}>
              <RadarChart data={radarData}>
                <PolarGrid stroke="#1e293b" />
                <PolarAngleAxis
                  dataKey="factor"
                  tick={{ fill: "#94a3b8", fontSize: 11 }}
                />
                <PolarRadiusAxis
                  angle={90}
                  domain={[0, "dataMax"]}
                  tick={false}
                  axisLine={false}
                />
                <Radar
                  name="Score"
                  dataKey="score"
                  stroke="#10b981"
                  fill="#10b981"
                  fillOpacity={0.2}
                  strokeWidth={2}
                />
              </RadarChart>
            </ResponsiveContainer>
          </Card>

          <Card title="Source Corroboration">
            <div className="flex items-center gap-2">
              <span className="text-2xl font-bold text-primary">{lead.source_count}</span>
              <span className="text-sm text-text-secondary">sources</span>
            </div>
            <div className="mt-2 flex flex-wrap gap-1.5">
              {lead.sources.map((src) => (
                <span
                  key={src}
                  className="rounded-md border border-border bg-background px-2 py-0.5 text-xs text-text-secondary"
                >
                  {src}
                </span>
              ))}
              {lead.sources.length === 0 && (
                <span className="text-xs text-text-secondary">No source data</span>
              )}
            </div>
            <div className="mt-3">
              <ConfidenceMeter value={lead.confidence_score} />
            </div>
          </Card>
        </div>

        {/* Right: Location + Info cards */}
        <div className="space-y-4">
          {hasCoords && (
            <Card title="Location">
              <div className="h-40 overflow-hidden rounded-lg">
                <MapContainer
                  center={[lead.coordinates.latitude!, lead.coordinates.longitude!]}
                  zoom={13}
                  className="h-full w-full"
                  style={{ background: "#020617" }}
                  zoomControl={false}
                  attributionControl={false}
                >
                  <TileLayer url={TILE_URL} />
                  <CircleMarker
                    center={[lead.coordinates.latitude!, lead.coordinates.longitude!]}
                    radius={8}
                    pathOptions={{ color: "#10b981", fillColor: "#10b981", fillOpacity: 0.6 }}
                  />
                </MapContainer>
              </div>
              <p className="mt-2 text-sm text-text-secondary">
                {[lead.address?.street, lead.address?.city, lead.address?.state, lead.address?.zip]
                  .filter(Boolean)
                  .join(", ")}
              </p>
            </Card>
          )}

          <Card title="Permit Info">
            <InfoGrid
              items={[
                ["Number", lead.permit_number],
                ["Type", lead.permit_type],
                ["Status", lead.permit_status],
                ["Jurisdiction", lead.jurisdiction],
                ["Filing Date", lead.filing_date ? new Date(lead.filing_date).toLocaleDateString() : null],
              ]}
            />
          </Card>

          <Card title="Project Details">
            <InfoGrid
              items={[
                ["Property Type", lead.property_type],
                ["Units", lead.unit_count?.toString()],
                ["Total SqFt", lead.total_sqft?.toLocaleString()],
                ["Valuation", lead.valuation_usd ? `$${(lead.valuation_usd / 1_000_000).toFixed(2)}M` : null],
              ]}
            />
            {lead.description && (
              <p className="mt-2 text-xs text-text-secondary">{lead.description}</p>
            )}
          </Card>

          <Card title="Stakeholders">
            <InfoGrid
              items={[
                ["Owner", lead.owner_name],
                ["Validation", lead.validation_status],
              ]}
            />
          </Card>
        </div>
      </div>
    </div>
  );
}

function Card({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="rounded-xl border border-border bg-surface p-5">
      <h3 className="mb-3 text-sm font-medium text-text-secondary">{title}</h3>
      {children}
    </div>
  );
}

function InfoGrid({ items }: { items: [string, string | null | undefined][] }) {
  return (
    <div className="grid grid-cols-2 gap-2">
      {items.map(([label, value]) => (
        <div key={label}>
          <p className="text-xs text-text-secondary">{label}</p>
          <p className="text-sm text-text-primary">{value ?? "—"}</p>
        </div>
      ))}
    </div>
  );
}

function ConfidenceMeter({ value }: { value: number }) {
  const pct = Math.round(value * 100);
  const color = value >= 0.7 ? "bg-primary" : value >= 0.4 ? "bg-warm" : "bg-error";
  return (
    <div>
      <div className="flex justify-between text-xs">
        <span className="text-text-secondary">Confidence</span>
        <span className="font-semibold text-text-primary">{pct}%</span>
      </div>
      <div className="mt-1 h-2 overflow-hidden rounded-full bg-border">
        <div className={`h-full rounded-full ${color}`} style={{ width: `${pct}%` }} />
      </div>
    </div>
  );
}
```

**Step 2: Verify in dev server**

```bash
cd dashboard && npm run dev
```

Navigate to a lead detail page (click from table, or visit `/dashboard/leads/some-id`).

**Step 3: Commit**

```bash
cd /Users/dustinmaselbas/programming/project_hunterd
git add dashboard/src/pages/LeadDetail.tsx
git commit -m "feat: implement Lead Detail with radar chart, mini map, and info cards"
```

---

### Task 10: Pipeline Monitor — React Flow visualization

**Files:**
- Modify: `dashboard/src/pages/Pipeline.tsx`
- Create: `dashboard/src/components/PipelineNode.tsx`

**Step 1: Create custom pipeline node**

Create `dashboard/src/components/PipelineNode.tsx`:

```tsx
import { Handle, Position, type NodeProps } from "@xyflow/react";
import { Check } from "lucide-react";

export type PipelineNodeData = {
  label: string;
  stage: string;
  status: "idle" | "active" | "complete" | "error";
  subtitle?: string;
};

const STATUS_STYLES: Record<string, string> = {
  idle: "border-border text-text-secondary opacity-50",
  active: "border-primary text-text-primary node-active-glow",
  complete: "border-emerald-600 text-primary",
  error: "border-error text-error",
};

export default function PipelineNode({ data }: NodeProps) {
  const nodeData = data as unknown as PipelineNodeData;
  const { label, stage, status, subtitle } = nodeData;

  return (
    <div
      className={`relative min-w-[140px] rounded-xl border-2 bg-surface px-4 py-3 transition-all ${STATUS_STYLES[status]}`}
    >
      <Handle type="target" position={Position.Left} className="!bg-border" />
      <div className="text-[10px] font-mono uppercase tracking-widest text-text-secondary">
        {stage}
      </div>
      <div className="mt-0.5 text-sm font-semibold">{label}</div>
      {subtitle && (
        <div className="mt-0.5 text-[10px] text-text-secondary">{subtitle}</div>
      )}
      {status === "complete" && (
        <div className="absolute -right-1 -top-1 flex h-4 w-4 items-center justify-center rounded-full bg-primary">
          <Check size={10} className="text-background" />
        </div>
      )}
      <Handle type="source" position={Position.Right} className="!bg-border" />
    </div>
  );
}
```

**Step 2: Implement Pipeline page**

Replace `dashboard/src/pages/Pipeline.tsx`:

```tsx
import { useCallback, useMemo } from "react";
import {
  ReactFlow,
  Background,
  type Node,
  type Edge,
  BackgroundVariant,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import PipelineNode, { type PipelineNodeData } from "@/components/PipelineNode";
import { useCycleStatus, useTriggerCycle } from "@/lib/hooks";
import type { CycleMetrics } from "@/lib/types";

const nodeTypes = { pipeline: PipelineNode };

const PHASES = [
  "source_discovery",
  "collection",
  "pipeline",
  "consensus",
  "self_improvement",
  "delivery",
  "complete",
];

function getNodeStatus(
  cycleStatus: string,
  nodePhase: string,
): "idle" | "active" | "complete" {
  if (cycleStatus === "idle") return "idle";
  if (cycleStatus === "completed" || cycleStatus === "complete") return "complete";
  if (cycleStatus !== "triggered" && cycleStatus !== "in_progress") return "idle";

  // For "triggered", show source_discovery as active
  const currentIdx = PHASES.indexOf(cycleStatus === "triggered" ? "source_discovery" : cycleStatus);
  const nodeIdx = PHASES.indexOf(nodePhase);

  if (nodeIdx < currentIdx) return "complete";
  if (nodeIdx === currentIdx) return "active";
  return "idle";
}

export default function Pipeline() {
  const { data: cycle } = useCycleStatus();
  const triggerMutation = useTriggerCycle();

  const cycleStatus = cycle?.status ?? "idle";
  const metrics = cycle?.metrics as CycleMetrics | undefined;

  const statusFn = useCallback(
    (phase: string) => getNodeStatus(cycleStatus, phase),
    [cycleStatus],
  );

  const nodes: Node[] = useMemo(
    () => [
      {
        id: "discovery",
        type: "pipeline",
        position: { x: 0, y: 120 },
        data: { label: "Source Discovery", stage: "ST-01", status: statusFn("source_discovery") },
      },
      // Collection group
      {
        id: "collection-group",
        type: "pipeline",
        position: { x: 220, y: 0 },
        data: { label: "Census BPS", stage: "ST-02a", status: statusFn("collection"), subtitle: "Building Permits" },
      },
      {
        id: "collection-soda",
        type: "pipeline",
        position: { x: 220, y: 70 },
        data: { label: "SODA Permits", stage: "ST-02b", status: statusFn("collection"), subtitle: "Socrata API" },
      },
      {
        id: "collection-edgar",
        type: "pipeline",
        position: { x: 220, y: 140 },
        data: { label: "SEC EDGAR", stage: "ST-02c", status: statusFn("collection"), subtitle: "SEC Filings" },
      },
      {
        id: "collection-rss",
        type: "pipeline",
        position: { x: 220, y: 210 },
        data: { label: "RSS Feeds", stage: "ST-02d", status: statusFn("collection"), subtitle: "News & Blogs" },
      },
      {
        id: "collection-http",
        type: "pipeline",
        position: { x: 220, y: 280 },
        data: { label: "HTTP Generic", stage: "ST-02e", status: statusFn("collection"), subtitle: "Web Scraper" },
      },
      // Pipeline
      {
        id: "pipeline",
        type: "pipeline",
        position: { x: 460, y: 120 },
        data: { label: "Data Pipeline", stage: "ST-03", status: statusFn("pipeline"), subtitle: "Dedup → Correlate → Enrich → Score" },
      },
      {
        id: "consensus",
        type: "pipeline",
        position: { x: 660, y: 120 },
        data: { label: "Consensus", stage: "ST-04", status: statusFn("consensus"), subtitle: "Validators + Confidence" },
      },
      {
        id: "improvement",
        type: "pipeline",
        position: { x: 860, y: 120 },
        data: { label: "Self-Improvement", stage: "ST-05", status: statusFn("self_improvement"), subtitle: "Metrics & Strategy" },
      },
      {
        id: "delivery",
        type: "pipeline",
        position: { x: 1060, y: 120 },
        data: { label: "Delivery", stage: "ST-06", status: statusFn("delivery"), subtitle: "Notifications" },
      },
    ],
    [statusFn],
  );

  const edges: Edge[] = useMemo(() => {
    const isActive = cycleStatus === "triggered" || cycleStatus === "in_progress";
    const edgeStyle = isActive
      ? { stroke: "#10b981", strokeWidth: 2, strokeDasharray: "5 5" }
      : { stroke: "#1e293b", strokeWidth: 1 };

    return [
      // Discovery → all collectors
      { id: "e-d-c1", source: "discovery", target: "collection-group", style: edgeStyle, animated: isActive },
      { id: "e-d-c2", source: "discovery", target: "collection-soda", style: edgeStyle, animated: isActive },
      { id: "e-d-c3", source: "discovery", target: "collection-edgar", style: edgeStyle, animated: isActive },
      { id: "e-d-c4", source: "discovery", target: "collection-rss", style: edgeStyle, animated: isActive },
      { id: "e-d-c5", source: "discovery", target: "collection-http", style: edgeStyle, animated: isActive },
      // All collectors → pipeline
      { id: "e-c1-p", source: "collection-group", target: "pipeline", style: edgeStyle, animated: isActive },
      { id: "e-c2-p", source: "collection-soda", target: "pipeline", style: edgeStyle, animated: isActive },
      { id: "e-c3-p", source: "collection-edgar", target: "pipeline", style: edgeStyle, animated: isActive },
      { id: "e-c4-p", source: "collection-rss", target: "pipeline", style: edgeStyle, animated: isActive },
      { id: "e-c5-p", source: "collection-http", target: "pipeline", style: edgeStyle, animated: isActive },
      // Sequential
      { id: "e-p-con", source: "pipeline", target: "consensus", style: edgeStyle, animated: isActive },
      { id: "e-con-i", source: "consensus", target: "improvement", style: edgeStyle, animated: isActive },
      { id: "e-i-del", source: "improvement", target: "delivery", style: edgeStyle, animated: isActive },
    ];
  }, [cycleStatus]);

  return (
    <div className="flex h-[calc(100vh-6rem)] gap-4">
      {/* Flow diagram */}
      <div className="flex-1 rounded-xl border border-border bg-surface">
        <ReactFlow
          nodes={nodes}
          edges={edges}
          nodeTypes={nodeTypes}
          fitView
          proOptions={{ hideAttribution: true }}
          nodesDraggable={false}
          nodesConnectable={false}
          elementsSelectable={false}
          panOnDrag
          zoomOnScroll
        >
          <Background variant={BackgroundVariant.Dots} color="#1e293b" gap={20} />
        </ReactFlow>
      </div>

      {/* Sidebar */}
      <div className="w-72 space-y-4">
        {/* Trigger */}
        <div className="rounded-xl border border-border bg-surface p-5">
          <button
            onClick={() => triggerMutation.mutate()}
            disabled={cycleStatus === "triggered" || cycleStatus === "in_progress" || triggerMutation.isPending}
            className="w-full rounded-lg bg-primary px-4 py-2.5 text-sm font-semibold text-background transition-colors hover:bg-emerald-400 disabled:opacity-50"
          >
            {triggerMutation.isPending ? "Triggering..." : "Trigger Cycle"}
          </button>
        </div>

        {/* Cycle Status */}
        <div className="rounded-xl border border-border bg-surface p-5">
          <h3 className="mb-2 text-sm font-medium text-text-secondary">Cycle Status</h3>
          <div className="flex items-center gap-2">
            <span
              className={`h-2 w-2 rounded-full ${
                cycleStatus === "idle"
                  ? "bg-cold"
                  : cycleStatus === "triggered"
                    ? "bg-hot animate-pulse"
                    : cycleStatus === "completed" || cycleStatus === "complete"
                      ? "bg-primary"
                      : "bg-error"
              }`}
            />
            <span className="text-sm font-semibold capitalize text-text-primary">
              {cycleStatus}
            </span>
          </div>
          {cycle?.cycle_id && (
            <p className="mt-1 text-[10px] font-mono text-text-secondary">
              {cycle.cycle_id.slice(0, 8)}
            </p>
          )}
        </div>

        {/* Metrics (show when available) */}
        {metrics && typeof metrics.total_validated_leads === "number" && (
          <div className="rounded-xl border border-border bg-surface p-5">
            <h3 className="mb-3 text-sm font-medium text-text-secondary">Cycle Metrics</h3>
            <div className="space-y-2 text-sm">
              <MetricRow label="Raw Records" value={metrics.total_raw_records} />
              <MetricRow label="Developments" value={metrics.total_developments} />
              <MetricRow label="Validated Leads" value={metrics.total_validated_leads} />
              <MetricRow label="Errors" value={metrics.total_errors} isError={metrics.total_errors > 0} />
              <div className="my-2 border-t border-border" />
              <MetricRow label="Yield Rate" value={`${(metrics.yield_rate * 100).toFixed(1)}%`} />
              <MetricRow label="Conversion" value={`${(metrics.conversion_rate * 100).toFixed(1)}%`} />
              <MetricRow label="Avg Score" value={metrics.avg_lead_score.toFixed(1)} />
              <MetricRow label="Avg Confidence" value={`${(metrics.avg_confidence * 100).toFixed(0)}%`} />
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

function MetricRow({
  label,
  value,
  isError,
}: {
  label: string;
  value: string | number;
  isError?: boolean;
}) {
  return (
    <div className="flex justify-between">
      <span className="text-text-secondary">{label}</span>
      <span className={`font-semibold ${isError ? "text-error" : "text-text-primary"}`}>
        {value}
      </span>
    </div>
  );
}
```

**Step 3: Add the active glow CSS animation**

Append to `dashboard/src/index.css`:

```css
@layer utilities {
  .node-active-glow {
    animation: pulse-border 2s infinite;
  }
}

@keyframes pulse-border {
  0% { box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.7); }
  70% { box-shadow: 0 0 0 10px rgba(16, 185, 129, 0); }
  100% { box-shadow: 0 0 0 0 rgba(16, 185, 129, 0); }
}
```

**Step 4: Verify in dev server**

```bash
cd dashboard && npm run dev
```

Visit `http://localhost:3000/dashboard/pipeline` — React Flow diagram should render with nodes + edges.

**Step 5: Commit**

```bash
cd /Users/dustinmaselbas/programming/project_hunterd
git add dashboard/src/pages/Pipeline.tsx dashboard/src/components/PipelineNode.tsx dashboard/src/index.css
git commit -m "feat: implement Pipeline Monitor with React Flow visualization"
```

---

### Task 11: FastAPI StaticFiles mount

**Files:**
- Modify: `src/landscraper/api/main.py`

**Step 1: Add StaticFiles mount for dashboard**

In `src/landscraper/api/main.py`, add the static files mount after all route definitions (at the bottom of the file, before any helper functions):

```python
import os as _os
from pathlib import Path as _Path

# Serve dashboard SPA if build exists
_dashboard_dir = _Path(__file__).resolve().parent.parent.parent.parent / "dashboard" / "dist"
if _dashboard_dir.is_dir():
    from fastapi.staticfiles import StaticFiles

    app.mount("/dashboard", StaticFiles(directory=str(_dashboard_dir), html=True), name="dashboard")
```

Also add a root redirect so `/` goes to `/dashboard`:

```python
from fastapi.responses import RedirectResponse

@app.get("/", include_in_schema=False)
async def root_redirect():
    return RedirectResponse(url="/dashboard")
```

**Step 2: Test the full stack**

```bash
# Build the dashboard
cd /Users/dustinmaselbas/programming/project_hunterd/dashboard && npm run build

# Start FastAPI
cd /Users/dustinmaselbas/programming/project_hunterd
.venv/bin/uvicorn landscraper.api.main:app --reload
```

Visit `http://localhost:8000/dashboard` — should see the full dashboard SPA.

**Step 3: Run existing backend tests**

```bash
.venv/bin/pytest tests/test_api.py -v
```

Expected: ALL PASS

**Step 4: Commit**

```bash
git add src/landscraper/api/main.py
git commit -m "feat: mount dashboard SPA via FastAPI StaticFiles"
```

---

### Task 12: Update Docker build for dashboard

**Files:**
- Modify: `docker/Dockerfile`

**Step 1: Update Dockerfile with multi-stage build**

Replace `docker/Dockerfile`:

```dockerfile
# Stage 1: Build dashboard
FROM node:20-slim AS frontend
WORKDIR /app/dashboard
COPY dashboard/package*.json ./
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

CMD ["uvicorn", "landscraper.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Step 2: Commit**

```bash
git add docker/Dockerfile
git commit -m "feat: multi-stage Docker build with dashboard frontend"
```

---

### Task 13: Add dashboard to .gitignore and clean up

**Files:**
- Modify: `.gitignore`

**Step 1: Add node_modules and dist to gitignore**

Add to `.gitignore`:

```
# Dashboard
dashboard/node_modules/
dashboard/dist/
```

**Step 2: Remove Vite boilerplate files**

Delete default files not needed:
- `dashboard/src/App.css`
- `dashboard/public/vite.svg`
- `dashboard/src/assets/react.svg`

**Step 3: Verify full build**

```bash
cd /Users/dustinmaselbas/programming/project_hunterd/dashboard && npm run build
cd /Users/dustinmaselbas/programming/project_hunterd && .venv/bin/pytest tests/test_api.py -v
```

**Step 4: Commit**

```bash
git add .gitignore
git add -u dashboard/  # stages deletions
git commit -m "chore: add dashboard ignores and remove Vite boilerplate"
```

---

### Execution Sequence Summary

| Task | What | Key Files |
|------|------|-----------|
| 1 | Backend: CORS + score_breakdown | `api/main.py`, `api/schemas.py` |
| 2 | Scaffold Vite + React | `dashboard/` |
| 3 | API client + hooks | `dashboard/src/lib/` |
| 4 | Router + Layout shell | `dashboard/src/components/Layout.tsx`, `App.tsx` |
| 5 | Shared UI components | `TierBadge.tsx`, `StatCard.tsx` |
| 6 | KPI Dashboard | `pages/Dashboard.tsx` |
| 7 | Lead Explorer table | `pages/LeadExplorer.tsx` |
| 8 | Lead Explorer map | `components/LeadMap.tsx` |
| 9 | Lead Detail | `pages/LeadDetail.tsx` |
| 10 | Pipeline Monitor | `pages/Pipeline.tsx`, `PipelineNode.tsx` |
| 11 | FastAPI StaticFiles | `api/main.py` |
| 12 | Docker multi-stage | `docker/Dockerfile` |
| 13 | Gitignore + cleanup | `.gitignore` |
