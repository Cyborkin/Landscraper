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
): "idle" | "active" | "complete" | "error" {
  if (cycleStatus === "error") {
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
    case "completed": case "complete": return "text-secondary";
    case "running": case "triggered": case "in_progress": return "text-cta";
    case "error": return "text-error";
    default: return "text-text-secondary";
  }
}

// All 17 data sources grouped by type
const API_SOURCES = [
  { id: "src-soda", label: "SODA Permits", subtitle: "Socrata API" },
  { id: "src-census", label: "Census BPS", subtitle: "Building Permits" },
  { id: "src-dola", label: "DOLA Demography", subtitle: "Population Data" },
  { id: "src-edgar", label: "SEC EDGAR", subtitle: "SEC Filings" },
  { id: "src-dwr", label: "DWR Well Permits", subtitle: "Water Rights" },
  { id: "src-legistar", label: "Legistar Planning", subtitle: "City Councils" },
];

const ARCGIS_SOURCES = [
  { id: "src-fc-permits", label: "Fort Collins", subtitle: "ArcGIS Permits" },
  { id: "src-aurora-permits", label: "Aurora Permits", subtitle: "ArcGIS" },
  { id: "src-aurora-dev", label: "Aurora Dev Apps", subtitle: "ArcGIS" },
  { id: "src-den-res", label: "Denver Residential", subtitle: "ArcGIS Permits" },
  { id: "src-den-rez", label: "Denver Rezoning", subtitle: "ArcGIS" },
  { id: "src-den-demo", label: "Denver Demolition", subtitle: "ArcGIS" },
  { id: "src-den-comm", label: "Denver Commercial", subtitle: "ArcGIS" },
];

const RSS_SOURCES = [
  { id: "src-bizwest", label: "BizWest RSS", subtitle: "News" },
  { id: "src-denpost", label: "Denver Post RSS", subtitle: "Real Estate" },
  { id: "src-infill", label: "DenverInfill RSS", subtitle: "Development" },
];

const CSV_SOURCES = [
  { id: "src-fred", label: "FRED Permits", subtitle: "MSA-Level CSV" },
];

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

  // Layout constants
  const colX = { discovery: 0, sources: 280, pipeline: 560, consensus: 780, improve: 1000, delivery: 1220 };
  const sourceSpacing = 80;

  // Build source nodes — stacked vertically with group labels
  const allSources = [
    ...API_SOURCES.map((s, i) => ({ ...s, y: i * sourceSpacing, group: "API" })),
    ...ARCGIS_SOURCES.map((s, i) => ({ ...s, y: (API_SOURCES.length + i) * sourceSpacing, group: "ArcGIS" })),
    ...RSS_SOURCES.map((s, i) => ({ ...s, y: (API_SOURCES.length + ARCGIS_SOURCES.length + i) * sourceSpacing, group: "RSS" })),
    ...CSV_SOURCES.map((s, i) => ({ ...s, y: (API_SOURCES.length + ARCGIS_SOURCES.length + RSS_SOURCES.length + i) * sourceSpacing, group: "CSV" })),
  ];

  const totalSources = allSources.length; // 17
  const centerY = ((totalSources - 1) * sourceSpacing) / 2;

  const nodes: PipelineNodeType[] = useMemo(
    () => [
      makeNode("discovery", { x: colX.discovery, y: centerY }, {
        label: "Source Discovery",
        stage: "ST-01",
        status: statusFn("source_discovery"),
      }),
      ...allSources.map((src) =>
        makeNode(src.id, { x: colX.sources, y: src.y }, {
          label: src.label,
          stage: src.group,
          status: statusFn("collection"),
          subtitle: src.subtitle,
        }),
      ),
      makeNode("pipeline", { x: colX.pipeline, y: centerY }, {
        label: "Data Pipeline",
        stage: "ST-03",
        status: statusFn("pipeline"),
        subtitle: "Dedup > Correlate > Enrich > Score",
      }),
      makeNode("consensus", { x: colX.consensus, y: centerY }, {
        label: "Consensus",
        stage: "ST-04",
        status: statusFn("consensus"),
        subtitle: "Validators + Confidence",
      }),
      makeNode("improvement", { x: colX.improve, y: centerY }, {
        label: "Self-Improvement",
        stage: "ST-05",
        status: statusFn("self_improvement"),
        subtitle: "Metrics & Strategy",
      }),
      makeNode("delivery", { x: colX.delivery, y: centerY }, {
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
    const baseStroke = isError ? "#DC2626" : isActive ? "#4F7C59" : "#D1D5DB";
    const edgeStyle = {
      stroke: baseStroke,
      strokeWidth: isActive || isError ? 2 : 1,
      ...(isActive && { strokeDasharray: "6 4" }),
    };

    return [
      // Discovery → all sources
      ...allSources.map((src) => ({
        id: `e-d-${src.id}`, source: "discovery", target: src.id, style: edgeStyle, animated: isActive,
      })),
      // All sources → pipeline
      ...allSources.map((src) => ({
        id: `e-${src.id}-p`, source: src.id, target: "pipeline", style: edgeStyle, animated: isActive,
      })),
      // Pipeline chain
      { id: "e-p-con", source: "pipeline", target: "consensus", style: edgeStyle, animated: isActive },
      { id: "e-con-i", source: "consensus", target: "improvement", style: edgeStyle, animated: isActive },
      { id: "e-i-del", source: "improvement", target: "delivery", style: edgeStyle, animated: isActive },
    ];
  }, [cycleStatus]);

  const lastRun = history?.[0];

  return (
    <div className="flex h-[calc(100vh-4rem)] gap-4">
      {/* Flow diagram */}
      <div className="flex-1 rounded-xl border border-border bg-surface shadow-sm">
        <ReactFlow
          nodes={nodes}
          edges={edges}
          nodeTypes={nodeTypes}
          fitView
          fitViewOptions={{ padding: 0.15 }}
          proOptions={{ hideAttribution: true }}
          nodesDraggable={false}
          nodesConnectable={false}
          elementsSelectable={false}
          panOnDrag
          zoomOnScroll
        >
          <Background
            variant={BackgroundVariant.Dots}
            color="#D1D5DB"
            gap={20}
          />
        </ReactFlow>
      </div>

      {/* Sidebar */}
      <div className="w-72 space-y-3 overflow-y-auto">
        <div className="rounded-xl border border-border bg-surface p-5 shadow-sm">
          <button
            onClick={() => triggerMutation.mutate()}
            disabled={
              cycleStatus === "triggered" ||
              cycleStatus === "in_progress" ||
              cycleStatus === "running" ||
              triggerMutation.isPending
            }
            className="w-full rounded-lg bg-cta px-4 py-2.5 text-sm font-semibold text-white transition-colors hover:bg-orange-600 disabled:opacity-50"
          >
            {triggerMutation.isPending ? "Triggering..." : "Trigger Cycle"}
          </button>
          {lastRun?.started_at && (
            <p className="mt-2 text-center text-[10px] text-text-secondary">
              Last run: {formatTimestamp(lastRun.started_at)}
            </p>
          )}
        </div>

        <div className="rounded-xl border border-border bg-surface p-5 shadow-sm">
          <h3 className="mb-2 text-sm font-medium text-text-secondary">
            Cycle Status
          </h3>
          <div className="flex items-center gap-2">
            <span
              className={`h-2.5 w-2.5 rounded-full ${
                cycleStatus === "idle"
                  ? "bg-cold"
                  : cycleStatus === "triggered" || cycleStatus === "running"
                    ? "bg-cta animate-pulse"
                    : cycleStatus === "completed" || cycleStatus === "complete"
                      ? "bg-secondary"
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
          <div className="rounded-xl border border-border bg-surface p-5 shadow-sm">
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
        <div className="rounded-xl border border-border bg-surface p-5 shadow-sm">
          <h3 className="mb-3 text-sm font-medium text-text-secondary">
            Run History
          </h3>
          {!history || history.length === 0 ? (
            <p className="text-xs text-text-secondary">No runs yet.</p>
          ) : (
            <div className="space-y-2">
              {history.slice(0, 10).map((run) => (
                <div key={run.cycle_id} className="flex items-center justify-between rounded-lg px-2 py-1.5 hover:bg-surface-raised transition-colors">
                  <div className="flex items-center gap-2">
                    <span
                      className={`h-2 w-2 rounded-full ${
                        run.status === "completed" || run.status === "complete"
                          ? "bg-secondary"
                          : run.status === "error"
                            ? "bg-error"
                            : "bg-cta"
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
