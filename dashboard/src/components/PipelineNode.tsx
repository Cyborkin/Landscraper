import { Handle, Position, type Node, type NodeProps } from "@xyflow/react";
import { Check } from "lucide-react";

export type PipelineNodeData = {
  label: string;
  stage: string;
  status: "idle" | "active" | "complete" | "error";
  subtitle?: string;
};

export type PipelineNodeType = Node<PipelineNodeData, "pipeline">;

const STATUS_STYLES: Record<string, string> = {
  idle: "border-border text-text-secondary opacity-50",
  active: "border-primary text-text-primary node-active-glow",
  complete: "border-emerald-600 text-primary",
  error: "border-error text-error",
};

export default function PipelineNode({ data }: NodeProps<PipelineNodeType>) {
  const { label, stage, status, subtitle } = data;

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
