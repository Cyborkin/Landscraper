# Dashboard Polish & Pipeline History Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. After each visual task, verify changes in Chrome using mcp__claude-in-chrome__ tools.

**Goal:** Fix chart visibility, map markers, pipeline layout/status colors, add confidence score explanation, pipeline run history panel, and general visual polish to make the dashboard look professional.

**Architecture:** Pure frontend changes across 9 dashboard files plus 2 backend files for cycle history. No DB migrations — cycle history stored in-memory (list of recent runs). All visual changes use existing Tailwind v4 theme tokens with new chart-specific CSS custom properties.

**Tech Stack:** React 19, Tailwind v4, Tremor v3 (charts), Leaflet/react-leaflet (maps), @xyflow/react (pipeline flow), recharts (radar), FastAPI (backend cycle history endpoint)

---

### Task 1: Theme — Add Chart Color Palette to CSS

**Files:**
- Modify: `dashboard/src/index.css`

These chart colors are optimized for visibility on slate-950 dark backgrounds. The current Tremor colors ("amber", "sky", "slate", "zinc") have poor contrast on our #020617 bg.

**Step 1: Add chart color tokens to index.css**

Add new CSS custom properties inside the existing `@theme` block for chart-specific colors, plus a card gradient utility:

```css
@import "tailwindcss";

@theme {
  --color-background: #020617;
  --color-surface: #0f172a;
  --color-surface-raised: #1a2332;
  --color-border: #1e293b;
  --color-border-subtle: #162032;
  --color-primary: #10b981;
  --color-hot: #f59e0b;
  --color-warm: #3b82f6;
  --color-monitor: #94a3b8;
  --color-cold: #475569;
  --color-error: #f43f5e;
  --color-text-primary: #f1f5f9;
  --color-text-secondary: #94a3b8;

  /* Chart palette — high vibrancy for dark bg */
  --color-chart-emerald: #34d399;
  --color-chart-indigo: #818cf8;
  --color-chart-amber: #fbbf24;
  --color-chart-rose: #fb7185;
  --color-chart-sky: #38bdf8;
  --color-chart-teal: #2dd4bf;

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

@layer utilities {
  .node-active-glow {
    animation: pulse-border 2s infinite;
  }

  .node-error-glow {
    animation: error-pulse-border 2s infinite;
  }

  .card-gradient {
    background: linear-gradient(135deg, #0f172a 0%, #0c1322 100%);
  }

  .data-mono {
    font-family: ui-monospace, 'JetBrains Mono', 'Cascadia Code', 'Fira Code', monospace;
    font-variant-numeric: tabular-nums;
  }
}

@keyframes pulse-border {
  0% { box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.7); }
  70% { box-shadow: 0 0 0 10px rgba(16, 185, 129, 0); }
  100% { box-shadow: 0 0 0 0 rgba(16, 185, 129, 0); }
}

@keyframes error-pulse-border {
  0% { box-shadow: 0 0 0 0 rgba(244, 63, 94, 0.6); }
  70% { box-shadow: 0 0 0 8px rgba(244, 63, 94, 0); }
  100% { box-shadow: 0 0 0 0 rgba(244, 63, 94, 0); }
}
```

**Step 2: Verify CSS compiles**

Run: `cd dashboard && npx vite build --mode development 2>&1 | head -20`
Expected: No CSS errors

**Step 3: Commit**

```bash
git add dashboard/src/index.css
git commit -m "style: add chart color palette and utility classes for dark theme visibility"
```

---

### Task 2: Fix Dashboard Chart Colors

**Files:**
- Modify: `dashboard/src/pages/Dashboard.tsx`
- Modify: `dashboard/src/components/StatCard.tsx`

The Tremor charts currently use named colors like "amber", "sky", "slate", "zinc" which render nearly invisible on our dark background. Switch to high-contrast colors and add card-gradient styling.

**Step 1: Update Dashboard.tsx chart colors and tier data**

Replace the tier data colors and chart color arrays. Also update the hot color reference from `amber` to match our `--color-hot` (amber-500):

```tsx
// Tier donut data — use vivid, distinct colors
const tierData = [
  { name: "Hot", value: leads.filter((l) => l.tier === "hot").length, color: "amber" },
  { name: "Warm", value: leads.filter((l) => l.tier === "warm").length, color: "blue" },
  { name: "Monitor", value: leads.filter((l) => l.tier === "monitor").length, color: "slate" },
  { name: "Cold", value: leads.filter((l) => l.tier === "cold").length, color: "gray" },
].filter((d) => d.value > 0);
```

In the JSX, update the `DonutChart` colors prop to use vibrant variants:
```tsx
<DonutChart
  data={tierData}
  category="value"
  index="name"
  colors={["amber", "blue", "slate", "gray"]}
  showLabel
  className="h-48"
/>
```

Update `BarChart` for score distribution — use "emerald" (this one is fine, but add `showGridLines={false}` for cleaner look):
```tsx
<BarChart
  data={scoreBuckets}
  index="range"
  categories={["count"]}
  colors={["emerald"]}
  showLegend={false}
  showGridLines={false}
  className="h-48"
/>
```

Update `BarList` — change from "emerald" to "indigo" so it's visually distinct from the BarChart:
```tsx
<BarList data={countyData} color="indigo" className="mt-2" />
```

Add `card-gradient` class to all three chart container divs:
```tsx
<div className="rounded-xl border border-border card-gradient p-5">
```

**Step 2: Update StatCard.tsx with gradient and monospace values**

```tsx
interface StatCardProps {
  label: string;
  value: string | number;
  accent?: string;
}

export default function StatCard({ label, value, accent }: StatCardProps) {
  return (
    <div className="rounded-xl border border-border card-gradient p-5">
      <p className="text-xs font-medium uppercase tracking-wide text-text-secondary">
        {label}
      </p>
      <p className={`mt-1 text-3xl font-bold data-mono ${accent ?? "text-text-primary"}`}>
        {value}
      </p>
    </div>
  );
}
```

**Step 3: Verify in browser**

Run: `cd dashboard && npm run dev` (if not already running)
Navigate to `/dashboard` — charts should show vibrant colors against the dark background. The donut chart should have amber (hot), blue (warm), slate (monitor), gray (cold). Bar chart should be emerald. County list should be indigo/purple.

**Step 4: Commit**

```bash
git add dashboard/src/pages/Dashboard.tsx dashboard/src/components/StatCard.tsx
git commit -m "fix: chart color scheme — use high-contrast colors visible on dark background"
```

---

### Task 3: Fix Map — County Centroid Fallback + Status Badge

**Files:**
- Modify: `dashboard/src/components/LeadMap.tsx`

Most leads lack lat/lng coordinates, so the map shows nothing. Fix: 1) add a county centroid lookup so leads with city/county but no coords still appear on the map (with reduced opacity to indicate imprecise location), 2) show a status badge indicating how many leads have precise locations.

**Step 1: Add county centroid lookup and fallback rendering to LeadMap.tsx**

```tsx
import { MapContainer, TileLayer, CircleMarker, Popup } from "react-leaflet";
import "leaflet/dist/leaflet.css";
import type { Lead } from "@/lib/types";

const TIER_COLORS: Record<string, string> = {
  hot: "#f59e0b",
  warm: "#3b82f6",
  monitor: "#94a3b8",
  cold: "#475569",
};

// Approximate centroids for Front Range counties
const COUNTY_CENTROIDS: Record<string, [number, number]> = {
  Adams: [39.87, -104.82],
  Arapahoe: [39.65, -104.34],
  Boulder: [40.09, -105.36],
  Broomfield: [39.92, -105.05],
  Denver: [39.74, -104.99],
  Douglas: [39.33, -104.93],
  "El Paso": [38.83, -104.76],
  Jefferson: [39.59, -105.25],
  Larimer: [40.66, -105.46],
  Weld: [40.55, -104.39],
};

// City centroids for common Front Range cities
const CITY_CENTROIDS: Record<string, [number, number]> = {
  Denver: [39.7392, -104.9903],
  "Colorado Springs": [38.8339, -104.8214],
  Aurora: [39.7294, -104.8319],
  "Fort Collins": [40.5853, -105.0844],
  Lakewood: [39.7047, -105.0814],
  Thornton: [39.8680, -104.9719],
  Arvada: [39.8028, -105.0875],
  Westminster: [39.8367, -105.0372],
  Centennial: [39.5681, -104.9694],
  Boulder: [40.0150, -105.2705],
  Greeley: [40.4233, -104.7091],
  Longmont: [40.1672, -105.1019],
  Loveland: [40.3978, -105.0750],
  "Castle Rock": [39.3722, -104.8561],
  Brighton: [39.9853, -104.8206],
  Broomfield: [39.9205, -105.0867],
  Parker: [39.5186, -104.7614],
  Commerce City: [39.8083, -104.9339],
};

const CENTER: [number, number] = [39.75, -104.9];
const ZOOM = 9;

const TILE_URL = "https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png";
const TILE_ATTR = '&copy; <a href="https://www.openstreetmap.org/copyright">OSM</a> &copy; <a href="https://carto.com/">CARTO</a>';

interface LeadMapProps {
  leads: Lead[];
  selectedId?: string;
  onSelect?: (leadId: string) => void;
}

function getLeadPosition(lead: Lead): { coords: [number, number]; precise: boolean } | null {
  if (lead.coordinates?.latitude != null && lead.coordinates?.longitude != null) {
    return { coords: [lead.coordinates.latitude, lead.coordinates.longitude], precise: true };
  }
  // Fallback: city centroid
  const city = lead.address?.city;
  if (city && CITY_CENTROIDS[city]) {
    return { coords: CITY_CENTROIDS[city], precise: false };
  }
  // Fallback: county centroid
  const county = lead.address?.county;
  if (county && COUNTY_CENTROIDS[county]) {
    return { coords: COUNTY_CENTROIDS[county], precise: false };
  }
  return null;
}

export default function LeadMap({ leads, selectedId, onSelect }: LeadMapProps) {
  const positioned = leads
    .map((lead) => ({ lead, pos: getLeadPosition(lead) }))
    .filter((item): item is { lead: Lead; pos: { coords: [number, number]; precise: boolean } } => item.pos !== null);

  const preciseCount = positioned.filter((p) => p.pos.precise).length;

  return (
    <div className="relative h-full w-full">
      <MapContainer
        center={CENTER}
        zoom={ZOOM}
        className="h-full w-full rounded-xl"
        style={{ background: "#020617" }}
      >
        <TileLayer url={TILE_URL} attribution={TILE_ATTR} />
        {positioned.map(({ lead, pos }) => {
          const isSelected = lead.lead_id === selectedId;
          const color = TIER_COLORS[lead.tier] ?? TIER_COLORS.cold;
          return (
            <CircleMarker
              key={lead.lead_id}
              center={pos.coords}
              radius={isSelected ? 10 : pos.precise ? 6 : 4}
              pathOptions={{
                color,
                fillColor: color,
                fillOpacity: isSelected ? 0.9 : pos.precise ? 0.6 : 0.25,
                weight: isSelected ? 3 : 1,
                dashArray: pos.precise ? undefined : "3 3",
              }}
              eventHandlers={{ click: () => onSelect?.(lead.lead_id) }}
            >
              <Popup>
                <div className="text-sm">
                  <div className="font-semibold">
                    {lead.project_name ?? lead.permit_number ?? lead.lead_id.slice(0, 8)}
                  </div>
                  <div>Score: {lead.lead_score} | {lead.tier.toUpperCase()}</div>
                  <div>{lead.address?.city}{lead.address?.county ? `, ${lead.address.county}` : ""}</div>
                  {!pos.precise && <div className="italic text-gray-400">Approximate location</div>}
                </div>
              </Popup>
            </CircleMarker>
          );
        })}
      </MapContainer>
      {/* Location precision badge */}
      <div className="absolute bottom-2 left-2 z-[1000] rounded-md bg-surface/90 px-2.5 py-1 text-[10px] text-text-secondary backdrop-blur-sm">
        {preciseCount} precise / {positioned.length} mapped of {leads.length} leads
      </div>
    </div>
  );
}
```

**Step 2: Verify in browser**

Navigate to `/dashboard/leads` — the map should now show markers for leads with city/county data (dashed outline, low opacity for approximate locations). The badge in the bottom-left corner should show location stats.

**Step 3: Commit**

```bash
git add dashboard/src/components/LeadMap.tsx
git commit -m "fix: map markers — add city/county centroid fallback for leads without coordinates"
```

---

### Task 4: Pipeline Node Status Colors + Error State

**Files:**
- Modify: `dashboard/src/components/PipelineNode.tsx`

Currently nodes have idle/active/complete states but no "error" visual and the colors are subtle. Make status immediately obvious: running = emerald glow, success = emerald border, failed = rose glow, idle = dim.

**Step 1: Update PipelineNode.tsx with enhanced status styling**

```tsx
import { Handle, Position, type Node, type NodeProps } from "@xyflow/react";
import { Check, X, Loader2 } from "lucide-react";

export type PipelineNodeData = {
  label: string;
  stage: string;
  status: "idle" | "active" | "complete" | "error";
  subtitle?: string;
};

export type PipelineNodeType = Node<PipelineNodeData, "pipeline">;

const STATUS_STYLES: Record<string, string> = {
  idle: "border-border bg-surface text-text-secondary opacity-60",
  active: "border-primary bg-surface text-text-primary node-active-glow",
  complete: "border-emerald-700 bg-emerald-950/30 text-primary",
  error: "border-error bg-rose-950/30 text-error node-error-glow",
};

const STATUS_ICONS: Record<string, React.ReactNode> = {
  complete: (
    <div className="absolute -right-1.5 -top-1.5 flex h-5 w-5 items-center justify-center rounded-full bg-primary shadow-md shadow-primary/30">
      <Check size={11} className="text-background" strokeWidth={3} />
    </div>
  ),
  error: (
    <div className="absolute -right-1.5 -top-1.5 flex h-5 w-5 items-center justify-center rounded-full bg-error shadow-md shadow-error/30">
      <X size={11} className="text-background" strokeWidth={3} />
    </div>
  ),
  active: (
    <div className="absolute -right-1.5 -top-1.5 flex h-5 w-5 items-center justify-center rounded-full bg-primary">
      <Loader2 size={11} className="animate-spin text-background" strokeWidth={3} />
    </div>
  ),
};

export default function PipelineNode({ data }: NodeProps<PipelineNodeType>) {
  const { label, stage, status, subtitle } = data;

  return (
    <div
      className={`relative min-w-[150px] rounded-xl border-2 px-4 py-3 transition-all duration-300 ${STATUS_STYLES[status]}`}
    >
      <Handle type="target" position={Position.Left} className="!bg-border !w-2 !h-2" />
      <div className="text-[10px] font-mono uppercase tracking-widest text-text-secondary">
        {stage}
      </div>
      <div className="mt-0.5 text-sm font-semibold">{label}</div>
      {subtitle && (
        <div className="mt-0.5 text-[10px] text-text-secondary">{subtitle}</div>
      )}
      {STATUS_ICONS[status] ?? null}
      <Handle type="source" position={Position.Right} className="!bg-border !w-2 !h-2" />
    </div>
  );
}
```

**Step 2: Verify in browser**

Navigate to `/dashboard/pipeline` — idle nodes should be dim with muted borders, active nodes should pulse green, complete nodes should have green tint with checkmark, error nodes should glow red with X icon.

**Step 3: Commit**

```bash
git add dashboard/src/components/PipelineNode.tsx
git commit -m "fix: pipeline node colors — status-driven styling with running/success/error indicators"
```

---

### Task 5: Pipeline Layout, Spacing, Last-Run Timestamp, Edge Colors

**Files:**
- Modify: `dashboard/src/pages/Pipeline.tsx`

Current problems: nodes overlap (70px vertical spacing for ~60px tall nodes), no last-run timestamp, edges don't reflect status. Fix: increase spacing to 100px vertical, widen horizontal gaps, add timestamp, color edges per status.

**Step 1: Update Pipeline.tsx node positions, edges, and sidebar**

Key layout changes:
- Collection nodes: y spacing from 70px to 100px, starting y from 0 to -50 (centers the fan)
- Horizontal spacing: discovery at x=0, collection at x=250, pipeline at x=520, consensus at x=740, improvement at x=960, delivery at x=1180
- Discovery node y: center of collection fan = y=150
- Downstream nodes: y=150 (centered)

```tsx
import { useCallback, useMemo } from "react";
import {
  ReactFlow,
  Background,
  type Edge,
  BackgroundVariant,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import PipelineNode, {
  type PipelineNodeData,
  type PipelineNodeType,
} from "@/components/PipelineNode";
import { useCycleStatus, useTriggerCycle, useCycleHistory } from "@/lib/hooks";
import type { CycleMetrics, CycleHistoryEntry } from "@/lib/types";

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
): "idle" | "active" | "complete" | "error" {
  if (cycleStatus === "error") {
    // If the overall cycle errored, mark the last active phase as error
    return nodePhase === "source_discovery" ? "error" : "idle";
  }
  if (cycleStatus === "idle") return "idle";
  if (cycleStatus === "completed" || cycleStatus === "complete") return "complete";
  if (cycleStatus !== "triggered" && cycleStatus !== "in_progress" && cycleStatus !== "running")
    return "idle";
  const currentIdx = PHASES.indexOf(
    cycleStatus === "triggered" || cycleStatus === "running" ? "source_discovery" : cycleStatus,
  );
  const nodeIdx = PHASES.indexOf(nodePhase);
  if (nodeIdx < currentIdx) return "complete";
  if (nodeIdx === currentIdx) return "active";
  return "idle";
}

function makeNode(
  id: string,
  position: { x: number; y: number },
  data: PipelineNodeData,
): PipelineNodeType {
  return { id, type: "pipeline" as const, position, data };
}

function formatTimestamp(iso: string | null | undefined): string {
  if (!iso) return "Never";
  const d = new Date(iso);
  return d.toLocaleString(undefined, {
    month: "short", day: "numeric",
    hour: "2-digit", minute: "2-digit",
  });
}

function statusColor(status: string): string {
  switch (status) {
    case "completed": case "complete": return "text-primary";
    case "running": case "triggered": case "in_progress": return "text-chart-amber";
    case "error": return "text-error";
    default: return "text-text-secondary";
  }
}

export default function Pipeline() {
  const { data: cycle } = useCycleStatus();
  const { data: history } = useCycleHistory();
  const triggerMutation = useTriggerCycle();

  const cycleStatus = cycle?.status ?? "idle";
  const metrics = cycle?.metrics as CycleMetrics | undefined;

  const statusFn = useCallback(
    (phase: string) => getNodeStatus(cycleStatus, phase),
    [cycleStatus],
  );

  // Layout: fan out 5 collection nodes vertically, everything else centered
  const collectionY = [-100, 0, 100, 200, 300];
  const centerY = 100;

  const nodes: PipelineNodeType[] = useMemo(
    () => [
      makeNode("discovery", { x: 0, y: centerY }, {
        label: "Source Discovery",
        stage: "ST-01",
        status: statusFn("source_discovery"),
      }),
      makeNode("collection-census", { x: 250, y: collectionY[0] }, {
        label: "Census BPS",
        stage: "ST-02a",
        status: statusFn("collection"),
        subtitle: "Building Permits",
      }),
      makeNode("collection-soda", { x: 250, y: collectionY[1] }, {
        label: "SODA Permits",
        stage: "ST-02b",
        status: statusFn("collection"),
        subtitle: "Socrata API",
      }),
      makeNode("collection-edgar", { x: 250, y: collectionY[2] }, {
        label: "SEC EDGAR",
        stage: "ST-02c",
        status: statusFn("collection"),
        subtitle: "SEC Filings",
      }),
      makeNode("collection-rss", { x: 250, y: collectionY[3] }, {
        label: "RSS Feeds",
        stage: "ST-02d",
        status: statusFn("collection"),
        subtitle: "News & Blogs",
      }),
      makeNode("collection-http", { x: 250, y: collectionY[4] }, {
        label: "HTTP Generic",
        stage: "ST-02e",
        status: statusFn("collection"),
        subtitle: "Web Scraper",
      }),
      makeNode("pipeline", { x: 520, y: centerY }, {
        label: "Data Pipeline",
        stage: "ST-03",
        status: statusFn("pipeline"),
        subtitle: "Dedup > Correlate > Enrich > Score",
      }),
      makeNode("consensus", { x: 740, y: centerY }, {
        label: "Consensus",
        stage: "ST-04",
        status: statusFn("consensus"),
        subtitle: "Validators + Confidence",
      }),
      makeNode("improvement", { x: 960, y: centerY }, {
        label: "Self-Improvement",
        stage: "ST-05",
        status: statusFn("self_improvement"),
        subtitle: "Metrics & Strategy",
      }),
      makeNode("delivery", { x: 1180, y: centerY }, {
        label: "Delivery",
        stage: "ST-06",
        status: statusFn("delivery"),
        subtitle: "Notifications",
      }),
    ],
    [statusFn],
  );

  const edges: Edge[] = useMemo(() => {
    const isActive = cycleStatus === "triggered" || cycleStatus === "in_progress" || cycleStatus === "running";
    const isError = cycleStatus === "error";
    const baseStroke = isError ? "#f43f5e" : isActive ? "#10b981" : "#1e293b";
    const edgeStyle = {
      stroke: baseStroke,
      strokeWidth: isActive || isError ? 2 : 1,
      ...(isActive && { strokeDasharray: "6 4" }),
    };

    return [
      { id: "e-d-c1", source: "discovery", target: "collection-census", style: edgeStyle, animated: isActive },
      { id: "e-d-c2", source: "discovery", target: "collection-soda", style: edgeStyle, animated: isActive },
      { id: "e-d-c3", source: "discovery", target: "collection-edgar", style: edgeStyle, animated: isActive },
      { id: "e-d-c4", source: "discovery", target: "collection-rss", style: edgeStyle, animated: isActive },
      { id: "e-d-c5", source: "discovery", target: "collection-http", style: edgeStyle, animated: isActive },
      { id: "e-c1-p", source: "collection-census", target: "pipeline", style: edgeStyle, animated: isActive },
      { id: "e-c2-p", source: "collection-soda", target: "pipeline", style: edgeStyle, animated: isActive },
      { id: "e-c3-p", source: "collection-edgar", target: "pipeline", style: edgeStyle, animated: isActive },
      { id: "e-c4-p", source: "collection-rss", target: "pipeline", style: edgeStyle, animated: isActive },
      { id: "e-c5-p", source: "collection-http", target: "pipeline", style: edgeStyle, animated: isActive },
      { id: "e-p-con", source: "pipeline", target: "consensus", style: edgeStyle, animated: isActive },
      { id: "e-con-i", source: "consensus", target: "improvement", style: edgeStyle, animated: isActive },
      { id: "e-i-del", source: "improvement", target: "delivery", style: edgeStyle, animated: isActive },
    ];
  }, [cycleStatus]);

  const lastRun = history?.[0];

  return (
    <div className="flex h-[calc(100vh-6rem)] gap-4">
      {/* Flow diagram */}
      <div className="flex-1 rounded-xl border border-border card-gradient">
        <ReactFlow
          nodes={nodes}
          edges={edges}
          nodeTypes={nodeTypes}
          fitView
          fitViewOptions={{ padding: 0.2 }}
          proOptions={{ hideAttribution: true }}
          nodesDraggable={false}
          nodesConnectable={false}
          elementsSelectable={false}
          panOnDrag
          zoomOnScroll
        >
          <Background
            variant={BackgroundVariant.Dots}
            color="#1e293b"
            gap={20}
          />
        </ReactFlow>
      </div>

      {/* Sidebar */}
      <div className="w-72 space-y-3 overflow-y-auto">
        <div className="rounded-xl border border-border card-gradient p-5">
          <button
            onClick={() => triggerMutation.mutate()}
            disabled={
              cycleStatus === "triggered" ||
              cycleStatus === "in_progress" ||
              cycleStatus === "running" ||
              triggerMutation.isPending
            }
            className="w-full rounded-lg bg-primary px-4 py-2.5 text-sm font-semibold text-background transition-colors hover:bg-emerald-400 disabled:opacity-50"
          >
            {triggerMutation.isPending ? "Triggering..." : "Trigger Cycle"}
          </button>
          {lastRun?.started_at && (
            <p className="mt-2 text-center text-[10px] text-text-secondary">
              Last run: {formatTimestamp(lastRun.started_at)}
            </p>
          )}
        </div>

        <div className="rounded-xl border border-border card-gradient p-5">
          <h3 className="mb-2 text-sm font-medium text-text-secondary">
            Cycle Status
          </h3>
          <div className="flex items-center gap-2">
            <span
              className={`h-2.5 w-2.5 rounded-full ${
                cycleStatus === "idle"
                  ? "bg-cold"
                  : cycleStatus === "triggered" || cycleStatus === "running"
                    ? "bg-chart-amber animate-pulse"
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

        {metrics && typeof metrics.total_validated_leads === "number" && (
          <div className="rounded-xl border border-border card-gradient p-5">
            <h3 className="mb-3 text-sm font-medium text-text-secondary">
              Cycle Metrics
            </h3>
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

        {/* Run History */}
        <div className="rounded-xl border border-border card-gradient p-5">
          <h3 className="mb-3 text-sm font-medium text-text-secondary">
            Run History
          </h3>
          {!history || history.length === 0 ? (
            <p className="text-xs text-text-secondary">No runs yet.</p>
          ) : (
            <div className="space-y-2">
              {history.slice(0, 10).map((run) => (
                <div key={run.cycle_id} className="flex items-center justify-between rounded-lg px-2 py-1.5 hover:bg-border/30">
                  <div className="flex items-center gap-2">
                    <span
                      className={`h-2 w-2 rounded-full ${
                        run.status === "completed" || run.status === "complete"
                          ? "bg-primary"
                          : run.status === "error"
                            ? "bg-error"
                            : "bg-chart-amber"
                      }`}
                    />
                    <span className="text-[10px] font-mono text-text-secondary">
                      {run.cycle_id.slice(0, 8)}
                    </span>
                  </div>
                  <div className="text-right">
                    <span className={`text-[10px] font-semibold capitalize ${statusColor(run.status)}`}>
                      {run.status}
                    </span>
                    <p className="text-[9px] text-text-secondary">
                      {formatTimestamp(run.started_at)}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
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
      <span className={`font-semibold data-mono ${isError ? "text-error" : "text-text-primary"}`}>
        {value}
      </span>
    </div>
  );
}
```

**Step 2: Verify in browser**

Navigate to `/dashboard/pipeline` — nodes should not overlap, the collection fan should have clear visual separation (~100px between each), and the downstream chain should be centered. The sidebar should show a "Run History" panel (empty until the backend is wired up).

**Step 3: Commit**

```bash
git add dashboard/src/pages/Pipeline.tsx
git commit -m "fix: pipeline layout spacing, status-colored edges, last-run timestamp, run history panel"
```

---

### Task 6: Confidence Score Explanation on Lead Detail

**Files:**
- Modify: `dashboard/src/pages/LeadDetail.tsx`

Add a 2-4 sentence explanation of how the confidence score is calculated, directly below the ConfidenceMeter component.

**Step 1: Update LeadDetail.tsx — add explanation below ConfidenceMeter**

In the "Source Corroboration" Card section, add explanation text after the `<ConfidenceMeter>`:

```tsx
<Card title="Source Corroboration">
  <div className="flex items-center gap-2">
    <span className="text-2xl font-bold text-primary data-mono">{lead.source_count}</span>
    <span className="text-sm text-text-secondary">sources</span>
  </div>
  <div className="mt-2 flex flex-wrap gap-1.5">
    {lead.sources.map((src) => (
      <span key={src} className="rounded-md border border-border bg-background px-2 py-0.5 text-xs text-text-secondary">
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
  <p className="mt-3 text-[11px] leading-relaxed text-text-secondary">
    Confidence is a weighted composite of source corroboration (40%), field
    completeness across 12 tracked data points (40%), and a data consistency
    audit that penalizes conflicting or invalid records (20%). Higher scores
    indicate the lead is well-documented across multiple authoritative sources.
  </p>
</Card>
```

Also update the radar chart card to use `card-gradient`:

```tsx
<Card title="Scoring Breakdown">
```

And update the `Card` component within this file to use `card-gradient`:

```tsx
function Card({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="rounded-xl border border-border card-gradient p-5">
      <h3 className="mb-3 text-sm font-medium text-text-secondary">{title}</h3>
      {children}
    </div>
  );
}
```

**Step 2: Verify in browser**

Navigate to a lead detail page — the "Source Corroboration" card should show the confidence meter followed by a brief explanation paragraph in small muted text.

**Step 3: Commit**

```bash
git add dashboard/src/pages/LeadDetail.tsx
git commit -m "feat: add confidence score explanation and card gradient polish on lead detail"
```

---

### Task 7: General Visual Polish

**Files:**
- Modify: `dashboard/src/components/Layout.tsx`
- Modify: `dashboard/src/components/TierBadge.tsx`
- Modify: `dashboard/src/pages/LeadExplorer.tsx`

Small touches to elevate the overall feel: sidebar refinement, tier badge colors synced, table polish, monospace on data values.

**Step 1: Update Layout.tsx — refined sidebar and header**

Update the sidebar logo and header styling:

```tsx
// In the sidebar <aside>:
<aside className="flex w-16 flex-col items-center gap-4 border-r border-border card-gradient py-4">
  <div className="mb-4 flex h-9 w-9 items-center justify-center rounded-lg bg-primary/10 text-lg font-bold text-primary">
    L
  </div>
  {/* ...rest unchanged */}
</aside>

// In the header:
<header className="flex h-12 items-center justify-between border-b border-border-subtle bg-surface px-6">
```

**Step 2: Update TierBadge.tsx — sync hot color**

Update the hot color to match the theme's warmer amber:

```tsx
const TIER_STYLES: Record<string, string> = {
  hot: "bg-hot/20 text-hot border border-hot/30",
  warm: "bg-warm/20 text-warm border border-warm/30",
  monitor: "bg-monitor/10 text-monitor border border-monitor/20",
  cold: "bg-cold/10 text-cold border border-cold/20",
};

export default function TierBadge({ tier }: { tier: string }) {
  return (
    <span
      className={`inline-block rounded-full px-2.5 py-0.5 text-[10px] font-semibold uppercase tracking-wide ${
        TIER_STYLES[tier] ?? TIER_STYLES.cold
      }`}
    >
      {tier}
    </span>
  );
}
```

**Step 3: Update LeadExplorer.tsx — monospace data, card-gradient on filter bar and table**

Add `data-mono` to score and confidence values. Add `card-gradient` to filter bar and table container:

In the filter bar div:
```tsx
<div className="flex items-center gap-3 rounded-xl border border-border card-gradient p-3">
```

In the table container div:
```tsx
<div className="overflow-hidden rounded-xl border border-border card-gradient">
```

In the score cell:
```tsx
<td className="px-4 py-3 data-mono"><ScoreBar score={lead.lead_score} /></td>
```

In the confidence cell:
```tsx
<td className="px-4 py-3 text-text-secondary data-mono">{(lead.confidence_score * 100).toFixed(0)}%</td>
```

**Step 4: Verify in browser**

Check all pages — consistent card-gradient backgrounds, refined tier badges with subtle borders, monospace on numeric data.

**Step 5: Commit**

```bash
git add dashboard/src/components/Layout.tsx dashboard/src/components/TierBadge.tsx dashboard/src/pages/LeadExplorer.tsx
git commit -m "style: visual polish — card gradients, tier badge borders, monospace data, sidebar refinement"
```

---

### Task 8: Backend — Cycle History Endpoint

**Files:**
- Modify: `src/landscraper/api/main.py`
- Modify: `src/landscraper/api/schemas.py`

Add in-memory cycle history (list of last 20 runs) and a `GET /api/v1/cycles` endpoint. No DB migration needed.

**Step 1: Read current schemas file**

Read: `src/landscraper/api/schemas.py`

**Step 2: Add CycleHistoryEntry schema to schemas.py**

Add at the end of schemas.py:

```python
class CycleHistoryEntry(BaseModel):
    cycle_id: str
    status: str
    started_at: str | None = None
    completed_at: str | None = None
    lead_count: int = 0
    error_count: int = 0
```

**Step 3: Update main.py — add cycle history storage and endpoint**

At the top of main.py, alongside `_last_cycle`, add:

```python
from datetime import datetime, timezone

_cycle_history: list[dict[str, Any]] = []
MAX_CYCLE_HISTORY = 20
```

Add the import for the new schema:
```python
from landscraper.api.schemas import (
    ...,  # existing imports
    CycleHistoryEntry,
)
```

In `trigger_cycle()`, after creating the cycle_id, append to history:

```python
history_entry = {
    "cycle_id": cycle_id,
    "status": "running",
    "started_at": datetime.now(timezone.utc).isoformat(),
    "completed_at": None,
    "lead_count": 0,
    "error_count": 0,
}
_cycle_history.insert(0, history_entry)
if len(_cycle_history) > MAX_CYCLE_HISTORY:
    _cycle_history.pop()
```

In `_run_cycle()`, update the history entry on completion/error:

After the `result = await graph.ainvoke(...)` success path:
```python
# Update history entry
for entry in _cycle_history:
    if entry["cycle_id"] == cycle_id:
        entry["status"] = "completed"
        entry["completed_at"] = datetime.now(timezone.utc).isoformat()
        entry["lead_count"] = len(result.get("validated_leads", []))
        break
```

In the except block:
```python
for entry in _cycle_history:
    if entry["cycle_id"] == cycle_id:
        entry["status"] = "error"
        entry["completed_at"] = datetime.now(timezone.utc).isoformat()
        break
```

Add the new endpoint:

```python
@app.get("/api/v1/cycles", response_model=list[CycleHistoryEntry])
async def list_cycles(
    tenant: Annotated[dict, Depends(verify_api_key)],
):
    """List recent cycle runs (most recent first, in-memory, max 20)."""
    return [CycleHistoryEntry(**entry) for entry in _cycle_history]
```

**Step 4: Test the endpoint**

Run: `cd /Users/dustinmaselbas/programming/project_hunterd && python -c "from landscraper.api.schemas import CycleHistoryEntry; print('OK')"`
Expected: OK

**Step 5: Commit**

```bash
git add src/landscraper/api/main.py src/landscraper/api/schemas.py
git commit -m "feat: add /api/v1/cycles endpoint for pipeline run history (in-memory)"
```

---

### Task 9: Frontend — Wire Up Cycle History

**Files:**
- Modify: `dashboard/src/lib/types.ts`
- Modify: `dashboard/src/lib/api.ts`
- Modify: `dashboard/src/lib/hooks.ts`

Add the types, API call, and React Query hook for the cycle history endpoint. Pipeline.tsx from Task 5 already consumes `useCycleHistory()`.

**Step 1: Add CycleHistoryEntry type to types.ts**

Add at the end:

```typescript
export interface CycleHistoryEntry {
  cycle_id: string;
  status: string;
  started_at: string | null;
  completed_at: string | null;
  lead_count: number;
  error_count: number;
}
```

**Step 2: Add fetchCycleHistory to api.ts**

Add:

```typescript
export async function fetchCycleHistory(): Promise<CycleHistoryEntry[]> {
  return fetchApi("/api/v1/cycles");
}
```

And add the import:
```typescript
import type { ..., CycleHistoryEntry } from "./types";
```

**Step 3: Add useCycleHistory hook to hooks.ts**

Add:

```typescript
export function useCycleHistory() {
  return useQuery({
    queryKey: ["cycleHistory"],
    queryFn: fetchCycleHistory,
    refetchInterval: 30_000,
  });
}
```

And add the import:
```typescript
import { ..., fetchCycleHistory } from "./api";
```

**Step 4: Verify in browser**

Navigate to `/dashboard/pipeline` — the "Run History" panel should load (empty if no cycles have run, populated after triggering a cycle).

**Step 5: Commit**

```bash
git add dashboard/src/lib/types.ts dashboard/src/lib/api.ts dashboard/src/lib/hooks.ts
git commit -m "feat: wire up cycle history API to dashboard — types, fetch, hook"
```

---

### Task 10: Final Visual Verification in Chrome

**Step 1: Build and check for errors**

Run: `cd dashboard && npm run build 2>&1 | tail -20`
Expected: Clean build with no TypeScript or CSS errors

**Step 2: Verify all 4 dashboard views in browser**

1. `/dashboard` — KPI cards with gradients, visible charts (emerald bars, amber/blue donut, indigo county list)
2. `/dashboard/leads` — Map with markers (including centroid fallbacks), precision badge, monospace data
3. `/dashboard/leads/:id` — Radar chart, confidence explanation, card gradients
4. `/dashboard/pipeline` — Properly spaced nodes, status colors, run history panel, last-run timestamp

**Step 3: Final commit**

```bash
git add -A
git commit -m "chore: dashboard polish — chart visibility, map fallbacks, pipeline layout, run history"
```

---

## Summary of Changes

| File | Change |
|------|--------|
| `dashboard/src/index.css` | Chart color tokens, card-gradient, data-mono, error-glow animation |
| `dashboard/src/pages/Dashboard.tsx` | Tremor chart colors updated for dark bg visibility |
| `dashboard/src/components/StatCard.tsx` | Card gradient, monospace values |
| `dashboard/src/components/LeadMap.tsx` | County/city centroid fallbacks, precision badge |
| `dashboard/src/components/PipelineNode.tsx` | Status-driven colors (running/success/error/idle) |
| `dashboard/src/pages/Pipeline.tsx` | Node spacing fix, last-run timestamp, run history panel, edge colors |
| `dashboard/src/pages/LeadDetail.tsx` | Confidence score explanation, card gradients |
| `dashboard/src/components/Layout.tsx` | Sidebar logo refinement, header border |
| `dashboard/src/components/TierBadge.tsx` | Subtle border on badges, synced colors |
| `dashboard/src/pages/LeadExplorer.tsx` | Card gradients, monospace on data cells |
| `dashboard/src/lib/types.ts` | CycleHistoryEntry interface |
| `dashboard/src/lib/api.ts` | fetchCycleHistory() |
| `dashboard/src/lib/hooks.ts` | useCycleHistory() hook |
| `src/landscraper/api/schemas.py` | CycleHistoryEntry Pydantic model |
| `src/landscraper/api/main.py` | In-memory cycle history, GET /api/v1/cycles endpoint |
