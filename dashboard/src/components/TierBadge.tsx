const TIER_STYLES: Record<string, string> = {
  hot: "bg-red-100 text-red-700 border border-red-200",
  warm: "bg-amber-100 text-amber-700 border border-amber-200",
  monitor: "bg-sky-100 text-sky-700 border border-sky-200",
  cold: "bg-slate-100 text-slate-500 border border-slate-200",
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
