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
