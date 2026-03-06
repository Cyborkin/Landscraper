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

const TILE_URL = "https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png";

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

  const hasCoords = lead.coordinates?.latitude != null && lead.coordinates?.longitude != null;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <button
          onClick={() => navigate("/dashboard/leads")}
          className="flex h-8 w-8 items-center justify-center rounded-lg border border-border text-text-secondary hover:bg-border hover:text-text-primary"
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
          <p className="text-3xl font-bold text-text-primary">{lead.lead_score}</p>
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
                <PolarGrid stroke="#1e293b" />
                <PolarAngleAxis dataKey="factor" tick={{ fill: "#94a3b8", fontSize: 11 }} />
                <PolarRadiusAxis angle={90} domain={[0, "dataMax"]} tick={false} axisLine={false} />
                <Radar name="Score" dataKey="score" stroke="#10b981" fill="#10b981" fillOpacity={0.2} strokeWidth={2} />
              </RadarChart>
            </ResponsiveContainer>
          </Card>

          <Card title="Source Corroboration">
            <div className="flex items-center gap-2">
              <span className="text-2xl font-bold text-primary">{lead.source_count}</span>
              <span className="text-sm text-text-secondary">sources</span>
            </div>
            <div className="mt-2 flex flex-wrap gap-1.5">
              {lead.sources.map((src) => (
                <span key={src} className="rounded-md border border-border bg-background px-2 py-0.5 text-xs text-text-secondary">
                  {src}
                </span>
              ))}
              {lead.sources.length === 0 && (
                <span className="text-xs text-text-secondary">No source data</span>
              )}
            </div>
            <div className="mt-3">
              <ConfidenceMeter value={lead.confidence_score} />
            </div>
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
                  style={{ background: "#020617" }}
                  zoomControl={false}
                  attributionControl={false}
                >
                  <TileLayer url={TILE_URL} />
                  <CircleMarker
                    center={[lead.coordinates.latitude!, lead.coordinates.longitude!]}
                    radius={8}
                    pathOptions={{ color: "#10b981", fillColor: "#10b981", fillOpacity: 0.6 }}
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
    <div className="rounded-xl border border-border bg-surface p-5">
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
          <p className="text-xs text-text-secondary">{label}</p>
          <p className="text-sm text-text-primary">{value ?? "\u2014"}</p>
        </div>
      ))}
    </div>
  );
}

function ConfidenceMeter({ value }: { value: number }) {
  const pct = Math.round(value * 100);
  const color = value >= 0.7 ? "bg-primary" : value >= 0.4 ? "bg-warm" : "bg-error";
  return (
    <div>
      <div className="flex justify-between text-xs">
        <span className="text-text-secondary">Confidence</span>
        <span className="font-semibold text-text-primary">{pct}%</span>
      </div>
      <div className="mt-1 h-2 overflow-hidden rounded-full bg-border">
        <div className={`h-full rounded-full ${color}`} style={{ width: `${pct}%` }} />
      </div>
    </div>
  );
}
