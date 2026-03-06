interface StatCardProps {
  label: string;
  value: string | number;
  accent?: string;
}

export default function StatCard({ label, value, accent }: StatCardProps) {
  return (
    <div className="rounded-xl border border-border bg-gradient-to-br from-surface to-surface-raised p-5 shadow-sm">
      <p className="text-xs font-medium uppercase tracking-wide text-text-secondary">
        {label}
      </p>
      <p className={`mt-1 text-3xl font-bold data-mono ${accent ?? "text-text-primary"}`}>
        {value}
      </p>
    </div>
  );
}
