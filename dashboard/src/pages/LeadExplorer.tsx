import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useLeads } from "@/lib/hooks";
import TierBadge from "@/components/TierBadge";
import LeadMap from "@/components/LeadMap";
import type { LeadFilters } from "@/lib/types";

const TIERS = ["", "hot", "warm", "monitor", "cold"];
const COUNTIES = [
  "", "Adams", "Arapahoe", "Boulder", "Broomfield", "Denver",
  "Douglas", "El Paso", "Jefferson", "Larimer", "Weld",
];

export default function LeadExplorer() {
  const navigate = useNavigate();
  const [filters, setFilters] = useState<LeadFilters>({ page_size: 50 });
  const [selectedLeadId, setSelectedLeadId] = useState<string>();
  const { data, isLoading } = useLeads(filters);

  const leads = data?.leads ?? [];

  return (
    <div className="space-y-4">
      {/* Map */}
      <div className="h-72 overflow-hidden rounded-xl border border-border">
        <LeadMap
          leads={leads}
          selectedId={selectedLeadId}
          onSelect={(id) => setSelectedLeadId(id)}
        />
      </div>

      <div className="flex items-center gap-3 rounded-xl border border-border bg-surface p-3">
        <Select
          label="Tier"
          value={filters.tier ?? ""}
          options={TIERS.map((t) => ({ value: t, label: t || "All Tiers" }))}
          onChange={(v) => setFilters((f) => ({ ...f, tier: v || undefined }))}
        />
        <Select
          label="County"
          value={filters.county ?? ""}
          options={COUNTIES.map((c) => ({ value: c, label: c || "All Counties" }))}
          onChange={(v) => setFilters((f) => ({ ...f, county: v || undefined }))}
        />
        <div className="flex items-center gap-2">
          <label className="text-xs text-text-secondary">Min Score</label>
          <input
            type="range"
            min={0}
            max={100}
            step={5}
            value={filters.min_score ?? 0}
            onChange={(e) =>
              setFilters((f) => ({ ...f, min_score: Number(e.target.value) || undefined }))
            }
            className="w-24 accent-primary"
          />
          <span className="w-6 text-xs text-text-secondary">{filters.min_score ?? 0}</span>
        </div>
      </div>

      <div className="text-xs text-text-secondary">
        {data?.meta.total_count ?? 0} leads found
      </div>

      <div className="overflow-hidden rounded-xl border border-border bg-surface">
        <table className="w-full text-left text-sm">
          <thead>
            <tr className="border-b border-border text-xs uppercase text-text-secondary">
              <th className="px-4 py-3">Score</th>
              <th className="px-4 py-3">Tier</th>
              <th className="px-4 py-3">City</th>
              <th className="px-4 py-3">County</th>
              <th className="px-4 py-3">Type</th>
              <th className="px-4 py-3">Confidence</th>
              <th className="px-4 py-3">Valuation</th>
            </tr>
          </thead>
          <tbody>
            {isLoading ? (
              <tr>
                <td colSpan={7} className="px-4 py-8 text-center text-text-secondary">Loading...</td>
              </tr>
            ) : leads.length === 0 ? (
              <tr>
                <td colSpan={7} className="px-4 py-8 text-center text-text-secondary">
                  No leads match the current filters.
                </td>
              </tr>
            ) : (
              leads.map((lead) => (
                <tr
                  key={lead.lead_id}
                  onClick={() => navigate(`/dashboard/leads/${lead.lead_id}`)}
                  className="cursor-pointer border-b border-border/50 transition-colors hover:bg-border/30"
                >
                  <td className="px-4 py-3"><ScoreBar score={lead.lead_score} /></td>
                  <td className="px-4 py-3"><TierBadge tier={lead.tier} /></td>
                  <td className="px-4 py-3 text-text-primary">{lead.address?.city ?? "—"}</td>
                  <td className="px-4 py-3 text-text-secondary">{lead.address?.county ?? "—"}</td>
                  <td className="px-4 py-3 text-text-secondary">{lead.property_type ?? "—"}</td>
                  <td className="px-4 py-3 text-text-secondary">{(lead.confidence_score * 100).toFixed(0)}%</td>
                  <td className="px-4 py-3 text-text-secondary">
                    {lead.valuation_usd ? `$${(lead.valuation_usd / 1_000_000).toFixed(1)}M` : "—"}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function ScoreBar({ score }: { score: number }) {
  const color =
    score >= 80 ? "bg-hot" : score >= 50 ? "bg-warm" : score >= 20 ? "bg-monitor" : "bg-cold";
  return (
    <div className="flex items-center gap-2">
      <div className="h-1.5 w-16 overflow-hidden rounded-full bg-border">
        <div className={`h-full rounded-full ${color}`} style={{ width: `${score}%` }} />
      </div>
      <span className="text-xs font-semibold text-text-primary">{score}</span>
    </div>
  );
}

function Select({
  label, value, options, onChange,
}: {
  label: string;
  value: string;
  options: { value: string; label: string }[];
  onChange: (v: string) => void;
}) {
  return (
    <div className="flex items-center gap-2">
      <label className="text-xs text-text-secondary">{label}</label>
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="rounded-md border border-border bg-background px-2 py-1 text-xs text-text-primary focus:border-primary focus:outline-none"
      >
        {options.map((o) => (
          <option key={o.value} value={o.value}>{o.label}</option>
        ))}
      </select>
    </div>
  );
}
