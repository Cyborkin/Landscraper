const TIER_STYLES: Record<string, string> = {
  hot: "bg-hot/10 text-hot border border-hot/20",
  warm: "bg-warm/10 text-warm border border-warm/20",
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
