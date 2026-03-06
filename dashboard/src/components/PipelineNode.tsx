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
  active: "border-secondary bg-secondary/5 text-text-primary node-active-glow",
  complete: "border-secondary/60 bg-secondary/5 text-secondary",
  error: "border-error bg-error/5 text-error node-error-glow",
};

const STATUS_ICONS: Record<string, React.ReactNode> = {
  complete: (
    <div className="absolute -right-1.5 -top-1.5 flex h-5 w-5 items-center justify-center rounded-full bg-secondary shadow-sm">
      <Check size={11} className="text-white" strokeWidth={3} />
    </div>
  ),
  error: (
    <div className="absolute -right-1.5 -top-1.5 flex h-5 w-5 items-center justify-center rounded-full bg-error shadow-sm">
      <X size={11} className="text-white" strokeWidth={3} />
    </div>
  ),
  active: (
    <div className="absolute -right-1.5 -top-1.5 flex h-5 w-5 items-center justify-center rounded-full bg-secondary">
      <Loader2 size={11} className="animate-spin text-white" strokeWidth={3} />
    </div>
  ),
};

export default function PipelineNode({ data }: NodeProps<PipelineNodeType>) {
  const { label, stage, status, subtitle } = data;

  return (
    <div
      className={`relative min-w-[150px] rounded-xl border-2 px-4 py-3 shadow-sm transition-all duration-300 ${STATUS_STYLES[status]}`}
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
