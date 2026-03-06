import { MapContainer, TileLayer, CircleMarker, Popup } from "react-leaflet";
import "leaflet/dist/leaflet.css";
import type { Lead } from "@/lib/types";

const TIER_COLORS: Record<string, string> = {
  hot: "#fbbf24",
  warm: "#38bdf8",
  monitor: "#94a3b8",
  cold: "#475569",
};

const CENTER: [number, number] = [39.95, -104.9];
const ZOOM = 9;

const TILE_URL = "https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png";
const TILE_ATTR = '&copy; <a href="https://www.openstreetmap.org/copyright">OSM</a> &copy; <a href="https://carto.com/">CARTO</a>';

interface LeadMapProps {
  leads: Lead[];
  selectedId?: string;
  onSelect?: (leadId: string) => void;
}

export default function LeadMap({ leads, selectedId, onSelect }: LeadMapProps) {
  const mappable = leads.filter(
    (l) => l.coordinates?.latitude != null && l.coordinates?.longitude != null,
  );

  return (
    <MapContainer
      center={CENTER}
      zoom={ZOOM}
      className="h-full w-full rounded-xl"
      style={{ background: "#020617" }}
    >
      <TileLayer url={TILE_URL} attribution={TILE_ATTR} />
      {mappable.map((lead) => (
        <CircleMarker
          key={lead.lead_id}
          center={[lead.coordinates.latitude!, lead.coordinates.longitude!]}
          radius={lead.lead_id === selectedId ? 10 : 6}
          pathOptions={{
            color: TIER_COLORS[lead.tier] ?? TIER_COLORS.cold,
            fillColor: TIER_COLORS[lead.tier] ?? TIER_COLORS.cold,
            fillOpacity: lead.lead_id === selectedId ? 0.9 : 0.6,
            weight: lead.lead_id === selectedId ? 3 : 1,
          }}
          eventHandlers={{
            click: () => onSelect?.(lead.lead_id),
          }}
        >
          <Popup>
            <div className="text-sm">
              <div className="font-semibold">
                {lead.project_name ?? lead.permit_number ?? lead.lead_id.slice(0, 8)}
              </div>
              <div>Score: {lead.lead_score} | {lead.tier.toUpperCase()}</div>
              <div>{lead.address?.city}{lead.address?.county ? `, ${lead.address.county}` : ""}</div>
            </div>
          </Popup>
        </CircleMarker>
      ))}
    </MapContainer>
  );
}
