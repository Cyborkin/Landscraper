import { useParams, useNavigate } from "react-router-dom";
import { useLead } from "@/lib/hooks";
import TierBadge from "@/components/TierBadge";
import { ArrowLeft } from "lucide-react";
import {
  Radar,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  ResponsiveContainer,
} from "recharts";
import { MapContainer, TileLayer, CircleMarker } from "react-leaflet";
import "leaflet/dist/leaflet.css";

const TILE_URL = "https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png";

const FACTOR_MAX: Record<string, number> = {
  project_scale: 20,
  permit_status: 15,
  unit_count: 10,
  property_type_fit: 10,
  location_demand: 10,
  owner_entity_type: 8,
  contact_completeness: 10,
  recency: 7,
  confidence: 5,
  source_corroboration: 5,
};

const FACTOR_LABELS: Record<string, string> = {
  project_scale: "Scale",
  permit_status: "Permit",
  unit_count: "Units",
  property_type_fit: "Type Fit",
  location_demand: "Location",
  owner_entity_type: "Owner",
  contact_completeness: "Contacts",
  recency: "Recency",
  confidence: "Confidence",
  source_corroboration: "Sources",
};

export default function LeadDetail() {
  const { leadId } = useParams<{ leadId: string }>();
  const navigate = useNavigate();
  const { data: lead, isLoading, error } = useLead(leadId ?? "");

  if (isLoading) return <div className="text-text-secondary">Loading...</div>;
  if (error || !lead) return <div className="text-error">Lead not found.</div>;

  const radarData = Object.entries(FACTOR_MAX).map(([key, max]) => ({
    factor: FACTOR_LABELS[key] ?? key,
    score: lead.score_breakdown?.[key] ?? 0,
    fullMark: max,
  }));

  const hasCoords =
    lead.coordinates?.latitude != null &&
    lead.coordinates?.longitude != null &&
    Math.abs(lead.coordinates.latitude) <= 90 &&
    Math.abs(lead.coordinates.longitude) <= 180;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <button
          onClick={() => navigate("/dashboard/leads")}
          className="flex h-8 w-8 items-center justify-center rounded-lg border border-border text-text-secondary hover:bg-surface-raised hover:text-text-primary transition-colors"
        >
          <ArrowLeft size={16} />
        </button>
        <div className="flex-1">
          <h2 className="text-lg font-semibold text-text-primary">
            {lead.project_name ?? lead.permit_number ?? lead.lead_id.slice(0, 12)}
          </h2>
          <p className="text-xs text-text-secondary">
            {lead.address?.city}{lead.address?.county ? `, ${lead.address.county} County` : ""}
          </p>
        </div>
        <TierBadge tier={lead.tier} />
        <div className="text-right">
          <p className="text-3xl font-bold data-mono text-text-primary">{lead.lead_score}</p>
          <p className="text-xs text-text-secondary">/ 100</p>
        </div>
      </div>

      {/* Two-column layout */}
      <div className="grid grid-cols-2 gap-6">
        {/* Left: Radar + Sources */}
        <div className="space-y-4">
          <Card title="Scoring Breakdown">
            <ResponsiveContainer width="100%" height={300}>
              <RadarChart data={radarData}>
                <PolarGrid stroke="#CBD5E1" />
                <PolarAngleAxis dataKey="factor" tick={{ fill: "#475569", fontSize: 11 }} />
                <PolarRadiusAxis angle={90} domain={[0, "dataMax"]} tick={false} axisLine={false} />
                <Radar name="Score" dataKey="score" stroke="#0D9488" fill="#0D9488" fillOpacity={0.25} strokeWidth={2} />
              </RadarChart>
            </ResponsiveContainer>
          </Card>

          <Card title="Source Corroboration">
            <div className="flex items-center gap-2">
              <span className="text-2xl font-bold data-mono text-secondary">{lead.source_count}</span>
              <span className="text-sm text-text-secondary">sources</span>
            </div>
            <div className="mt-2 flex flex-wrap gap-1.5">
              {lead.sources.map((src, i) => {
                const colors = [
                  "bg-teal-100 text-teal-700 border-teal-200",
                  "bg-violet-100 text-violet-700 border-violet-200",
                  "bg-amber-100 text-amber-700 border-amber-200",
                  "bg-sky-100 text-sky-700 border-sky-200",
                  "bg-rose-100 text-rose-700 border-rose-200",
                  "bg-emerald-100 text-emerald-700 border-emerald-200",
                  "bg-indigo-100 text-indigo-700 border-indigo-200",
                ];
                return (
                  <span key={src} className={`rounded-md border px-2 py-0.5 text-xs font-medium ${colors[i % colors.length]}`}>
                    {src}
                  </span>
                );
              })}
              {lead.sources.length === 0 && (
                <span className="text-xs text-text-secondary">No source data</span>
              )}
            </div>
            <div className="mt-3">
              <ConfidenceMeter value={lead.confidence_score} />
            </div>
            <p className="mt-3 text-[11px] leading-relaxed text-text-secondary">
              Confidence is a weighted composite of source corroboration (40%), field
              completeness across 12 tracked data points (40%), and a data consistency
              audit that penalizes conflicting or invalid records (20%). Higher scores
              indicate the lead is well-documented across multiple authoritative sources.
            </p>
          </Card>
        </div>

        {/* Right: Location + Info cards */}
        <div className="space-y-4">
          {hasCoords && (
            <Card title="Location">
              <div className="h-40 overflow-hidden rounded-lg">
                <MapContainer
                  center={[lead.coordinates.latitude!, lead.coordinates.longitude!]}
                  zoom={13}
                  className="h-full w-full"
                  style={{ background: "#F9FAFB" }}
                  zoomControl={false}
                  attributionControl={false}
                >
                  <TileLayer url={TILE_URL} />
                  <CircleMarker
                    center={[lead.coordinates.latitude!, lead.coordinates.longitude!]}
                    radius={10}
                    pathOptions={{
                      color: "#FFFFFF",
                      fillColor: lead.lead_score >= 70 ? "#16A34A" : lead.lead_score >= 55 ? "#4F7C59" : lead.lead_score >= 45 ? "#E67E22" : lead.lead_score >= 30 ? "#DC2626" : "#9CA3AF",
                      fillOpacity: 0.85,
                      weight: 2,
                    }}
                  />
                </MapContainer>
              </div>
              <p className="mt-2 text-sm text-text-secondary">
                {[lead.address?.street, lead.address?.city, lead.address?.state, lead.address?.zip]
                  .filter(Boolean)
                  .join(", ")}
              </p>
            </Card>
          )}

          <Card title="Permit Info">
            <InfoGrid items={[
              ["Number", lead.permit_number],
              ["Type", lead.permit_type],
              ["Status", lead.permit_status],
              ["Jurisdiction", lead.jurisdiction],
              ["Filing Date", lead.filing_date ? new Date(lead.filing_date).toLocaleDateString() : null],
            ]} />
          </Card>

          <Card title="Project Details">
            <InfoGrid items={[
              ["Property Type", lead.property_type],
              ["Units", lead.unit_count?.toString()],
              ["Total SqFt", lead.total_sqft?.toLocaleString()],
              ["Valuation", lead.valuation_usd ? `$${(lead.valuation_usd / 1_000_000).toFixed(2)}M` : null],
            ]} />
            {lead.description && (
              <p className="mt-2 text-xs text-text-secondary">{lead.description}</p>
            )}
          </Card>

          <Card title="Stakeholders">
            <InfoGrid items={[
              ["Owner", lead.owner_name],
              ["Validation", lead.validation_status],
            ]} />
          </Card>
        </div>
      </div>
    </div>
  );
}

function Card({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="rounded-xl border border-border bg-gradient-to-br from-surface to-surface-raised p-5 shadow-sm">
      <h3 className="mb-3 text-sm font-medium text-text-secondary">{title}</h3>
      {children}
    </div>
  );
}

function InfoGrid({ items }: { items: [string, string | null | undefined][] }) {
  return (
    <div className="grid grid-cols-2 gap-2">
      {items.map(([label, value]) => (
        <div key={label}>
          <p className="text-[11px] font-medium text-slate-400 uppercase tracking-wide">{label}</p>
          <p className="text-sm text-text-primary">{value ?? "\u2014"}</p>
        </div>
      ))}
    </div>
  );
}

function ConfidenceMeter({ value }: { value: number }) {
  const pct = Math.round(value * 100);
  const color = value >= 0.7 ? "bg-emerald-500" : value >= 0.4 ? "bg-amber-500" : "bg-rose-500";
  const textColor = value >= 0.7 ? "text-emerald-700" : value >= 0.4 ? "text-amber-700" : "text-rose-700";
  return (
    <div>
      <div className="flex justify-between text-xs">
        <span className="text-text-secondary">Confidence</span>
        <span className={`font-semibold data-mono ${textColor}`}>{pct}%</span>
      </div>
      <div className="mt-1 h-2.5 overflow-hidden rounded-full bg-slate-200">
        <div className={`h-full rounded-full ${color}`} style={{ width: `${pct}%` }} />
      </div>
    </div>
  );
}
