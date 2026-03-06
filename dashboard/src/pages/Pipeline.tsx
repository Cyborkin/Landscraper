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
  const currentIdx = PHASES.indexOf(
    cycleStatus === "triggered" ? "source_discovery" : cycleStatus,
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

export default function Pipeline() {
  const { data: cycle } = useCycleStatus();
  const triggerMutation = useTriggerCycle();

  const cycleStatus = cycle?.status ?? "idle";
  const metrics = cycle?.metrics as CycleMetrics | undefined;

  const statusFn = useCallback(
    (phase: string) => getNodeStatus(cycleStatus, phase),
    [cycleStatus],
  );

  const nodes: PipelineNodeType[] = useMemo(
    () => [
      makeNode("discovery", { x: 0, y: 120 }, {
        label: "Source Discovery",
        stage: "ST-01",
        status: statusFn("source_discovery"),
      }),
      makeNode("collection-census", { x: 220, y: 0 }, {
        label: "Census BPS",
        stage: "ST-02a",
        status: statusFn("collection"),
        subtitle: "Building Permits",
      }),
      makeNode("collection-soda", { x: 220, y: 70 }, {
        label: "SODA Permits",
        stage: "ST-02b",
        status: statusFn("collection"),
        subtitle: "Socrata API",
      }),
      makeNode("collection-edgar", { x: 220, y: 140 }, {
        label: "SEC EDGAR",
        stage: "ST-02c",
        status: statusFn("collection"),
        subtitle: "SEC Filings",
      }),
      makeNode("collection-rss", { x: 220, y: 210 }, {
        label: "RSS Feeds",
        stage: "ST-02d",
        status: statusFn("collection"),
        subtitle: "News & Blogs",
      }),
      makeNode("collection-http", { x: 220, y: 280 }, {
        label: "HTTP Generic",
        stage: "ST-02e",
        status: statusFn("collection"),
        subtitle: "Web Scraper",
      }),
      makeNode("pipeline", { x: 460, y: 120 }, {
        label: "Data Pipeline",
        stage: "ST-03",
        status: statusFn("pipeline"),
        subtitle: "Dedup \u2192 Correlate \u2192 Enrich \u2192 Score",
      }),
      makeNode("consensus", { x: 660, y: 120 }, {
        label: "Consensus",
        stage: "ST-04",
        status: statusFn("consensus"),
        subtitle: "Validators + Confidence",
      }),
      makeNode("improvement", { x: 860, y: 120 }, {
        label: "Self-Improvement",
        stage: "ST-05",
        status: statusFn("self_improvement"),
        subtitle: "Metrics & Strategy",
      }),
      makeNode("delivery", { x: 1060, y: 120 }, {
        label: "Delivery",
        stage: "ST-06",
        status: statusFn("delivery"),
        subtitle: "Notifications",
      }),
    ],
    [statusFn],
  );

  const edges: Edge[] = useMemo(() => {
    const isActive =
      cycleStatus === "triggered" || cycleStatus === "in_progress";
    const edgeStyle = isActive
      ? { stroke: "#10b981", strokeWidth: 2, strokeDasharray: "5 5" }
      : { stroke: "#1e293b", strokeWidth: 1 };

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
          <Background
            variant={BackgroundVariant.Dots}
            color="#1e293b"
            gap={20}
          />
        </ReactFlow>
      </div>

      {/* Sidebar */}
      <div className="w-72 space-y-4">
        <div className="rounded-xl border border-border bg-surface p-5">
          <button
            onClick={() => triggerMutation.mutate()}
            disabled={
              cycleStatus === "triggered" ||
              cycleStatus === "in_progress" ||
              triggerMutation.isPending
            }
            className="w-full rounded-lg bg-primary px-4 py-2.5 text-sm font-semibold text-background transition-colors hover:bg-emerald-400 disabled:opacity-50"
          >
            {triggerMutation.isPending ? "Triggering..." : "Trigger Cycle"}
          </button>
        </div>

        <div className="rounded-xl border border-border bg-surface p-5">
          <h3 className="mb-2 text-sm font-medium text-text-secondary">
            Cycle Status
          </h3>
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

        {metrics && typeof metrics.total_validated_leads === "number" && (
          <div className="rounded-xl border border-border bg-surface p-5">
            <h3 className="mb-3 text-sm font-medium text-text-secondary">
              Cycle Metrics
            </h3>
            <div className="space-y-2 text-sm">
              <MetricRow label="Raw Records" value={metrics.total_raw_records} />
              <MetricRow
                label="Developments"
                value={metrics.total_developments}
              />
              <MetricRow
                label="Validated Leads"
                value={metrics.total_validated_leads}
              />
              <MetricRow
                label="Errors"
                value={metrics.total_errors}
                isError={metrics.total_errors > 0}
              />
              <div className="my-2 border-t border-border" />
              <MetricRow
                label="Yield Rate"
                value={`${(metrics.yield_rate * 100).toFixed(1)}%`}
              />
              <MetricRow
                label="Conversion"
                value={`${(metrics.conversion_rate * 100).toFixed(1)}%`}
              />
              <MetricRow
                label="Avg Score"
                value={metrics.avg_lead_score.toFixed(1)}
              />
              <MetricRow
                label="Avg Confidence"
                value={`${(metrics.avg_confidence * 100).toFixed(0)}%`}
              />
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
      <span
        className={`font-semibold ${isError ? "text-error" : "text-text-primary"}`}
      >
        {value}
      </span>
    </div>
  );
}
