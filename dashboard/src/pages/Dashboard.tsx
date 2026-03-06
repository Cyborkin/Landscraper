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

  const hotCount = leads.filter((l) => l.tier === "hot").length;
  const pipelineValue = leads.reduce((sum, l) => sum + (l.valuation_usd ?? 0), 0);
  const avgConfidence =
    leads.length > 0
      ? leads.reduce((sum, l) => sum + l.confidence_score, 0) / leads.length
      : 0;

  const tierData = [
    { name: "Hot", value: leads.filter((l) => l.tier === "hot").length },
    { name: "Warm", value: leads.filter((l) => l.tier === "warm").length },
    { name: "Monitor", value: leads.filter((l) => l.tier === "monitor").length },
    { name: "Cold", value: leads.filter((l) => l.tier === "cold").length },
  ].filter((d) => d.value > 0);

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

  const countyCounts: Record<string, number> = {};
  for (const lead of leads) {
    const county = lead.address?.county ?? "Unknown";
    countyCounts[county] = (countyCounts[county] ?? 0) + 1;
  }
  const countyData = Object.entries(countyCounts)
    .map(([name, value]) => ({ name, value }))
    .sort((a, b) => b.value - a.value)
    .slice(0, 10);

  const recentLeads = [...leads]
    .sort((a, b) => {
      const da = a.discovered_at ?? "";
      const db = b.discovered_at ?? "";
      return db.localeCompare(da);
    })
    .slice(0, 10);

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-4 gap-4">
        <StatCard label="Total Leads" value={totalLeads} />
        <StatCard label="Hot Leads" value={hotCount} accent="text-hot" />
        <StatCard label="Pipeline Value" value={formatUsd(pipelineValue)} accent="text-primary" />
        <StatCard
          label="Avg Confidence"
          value={`${(avgConfidence * 100).toFixed(0)}%`}
          accent={avgConfidence >= 0.7 ? "text-secondary" : "text-text-secondary"}
        />
      </div>

      <div className="grid grid-cols-3 gap-4">
        <div className="rounded-xl border border-border bg-gradient-to-br from-surface to-surface-raised p-5 shadow-sm">
          <h3 className="mb-3 text-sm font-medium text-text-secondary">Tier Distribution</h3>
          <DonutChart
            data={tierData}
            category="value"
            index="name"
            colors={["rose", "amber", "sky", "slate"]}
            showLabel
            className="h-48"
          />
        </div>

        <div className="rounded-xl border border-border bg-gradient-to-br from-surface to-surface-raised p-5 shadow-sm">
          <h3 className="mb-3 text-sm font-medium text-text-secondary">Score Distribution</h3>
          <BarChart
            data={scoreBuckets}
            index="range"
            categories={["count"]}
            colors={["teal"]}
            showLegend={false}
            showGridLines={false}
            className="h-48"
          />
        </div>

        <div className="rounded-xl border border-border bg-gradient-to-br from-surface to-surface-raised p-5 shadow-sm">
          <h3 className="mb-3 text-sm font-medium text-text-secondary">Leads by County</h3>
          <BarList data={countyData} color="violet" className="mt-2" />
        </div>
      </div>

      <div className="rounded-xl border border-border bg-gradient-to-br from-surface to-surface-raised p-5 shadow-sm">
        <h3 className="mb-3 text-sm font-medium text-text-secondary">Recent Activity</h3>
        <div className="space-y-0.5">
          {recentLeads.map((lead, i) => (
            <RecentLeadRow key={lead.lead_id} lead={lead} even={i % 2 === 0} />
          ))}
          {recentLeads.length === 0 && (
            <p className="text-sm text-text-secondary">No leads discovered yet.</p>
          )}
        </div>
      </div>
    </div>
  );
}

function RecentLeadRow({ lead, even }: { lead: Lead; even: boolean }) {
  return (
    <div className={`flex items-center justify-between rounded-lg px-3 py-2 transition-colors hover:bg-primary/5 ${even ? "bg-surface-raised/60" : ""}`}>
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
        <span className="text-sm font-semibold data-mono text-text-primary">{lead.lead_score}</span>
        <span className="text-xs text-text-secondary">
          {lead.discovered_at ? new Date(lead.discovered_at).toLocaleDateString() : ""}
        </span>
      </div>
    </div>
  );
}
