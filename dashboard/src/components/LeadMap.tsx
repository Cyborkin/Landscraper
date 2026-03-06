import { MapContainer, TileLayer, CircleMarker, Popup } from "react-leaflet";
import "leaflet/dist/leaflet.css";
import type { Lead } from "@/lib/types";

// Score-based color scale: high value = green, medium = orange, low = red
function scoreColor(score: number): string {
  if (score >= 70) return "#16A34A";   // green-600
  if (score >= 55) return "#4F7C59";   // brand secondary
  if (score >= 45) return "#E67E22";   // brand cta/orange
  if (score >= 30) return "#DC2626";   // red-600
  return "#9CA3AF";                     // gray for very low
}

// Approximate centroids for Front Range counties
const COUNTY_CENTROIDS: Record<string, [number, number]> = {
  Adams: [39.87, -104.82],
  Arapahoe: [39.65, -104.34],
  Boulder: [40.09, -105.36],
  Broomfield: [39.92, -105.05],
  Denver: [39.74, -104.99],
  Douglas: [39.33, -104.93],
  "El Paso": [38.83, -104.76],
  Jefferson: [39.59, -105.25],
  Larimer: [40.66, -105.46],
  Weld: [40.55, -104.39],
};

// City centroids for common Front Range cities
const CITY_CENTROIDS: Record<string, [number, number]> = {
  Denver: [39.7392, -104.9903],
  "Colorado Springs": [38.8339, -104.8214],
  Aurora: [39.7294, -104.8319],
  "Fort Collins": [40.5853, -105.0844],
  Lakewood: [39.7047, -105.0814],
  Thornton: [39.8680, -104.9719],
  Arvada: [39.8028, -105.0875],
  Westminster: [39.8367, -105.0372],
  Centennial: [39.5681, -104.9694],
  Boulder: [40.0150, -105.2705],
  Greeley: [40.4233, -104.7091],
  Longmont: [40.1672, -105.1019],
  Loveland: [40.3978, -105.0750],
  "Castle Rock": [39.3722, -104.8561],
  Brighton: [39.9853, -104.8206],
  Broomfield: [39.9205, -105.0867],
  Parker: [39.5186, -104.7614],
  "Commerce City": [39.8083, -104.9339],
};

const CENTER: [number, number] = [39.75, -104.9];
const ZOOM = 9;

const TILE_URL = "https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png";
const TILE_ATTR = '&copy; <a href="https://www.openstreetmap.org/copyright">OSM</a> &copy; <a href="https://carto.com/">CARTO</a>';

interface LeadMapProps {
  leads: Lead[];
  selectedId?: string;
  onSelect?: (leadId: string) => void;
}

function getLeadPosition(lead: Lead): { coords: [number, number]; precise: boolean } | null {
  if (lead.coordinates?.latitude != null && lead.coordinates?.longitude != null) {
    return { coords: [lead.coordinates.latitude, lead.coordinates.longitude], precise: true };
  }
  const city = lead.address?.city;
  if (city && CITY_CENTROIDS[city]) {
    return { coords: CITY_CENTROIDS[city], precise: false };
  }
  const county = lead.address?.county;
  if (county && COUNTY_CENTROIDS[county]) {
    return { coords: COUNTY_CENTROIDS[county], precise: false };
  }
  return null;
}

// Add small random jitter to prevent centroid markers from stacking on top of each other
function jitter(coords: [number, number], index: number): [number, number] {
  const angle = (index * 137.508) * (Math.PI / 180); // golden angle for even distribution
  const r = 0.008 + (index % 5) * 0.003; // small radius ~0.5-1.5km
  return [coords[0] + r * Math.cos(angle), coords[1] + r * Math.sin(angle)];
}

export default function LeadMap({ leads, selectedId, onSelect }: LeadMapProps) {
  const positioned = leads
    .map((lead, i) => {
      const pos = getLeadPosition(lead);
      if (!pos) return null;
      return {
        lead,
        coords: pos.precise ? pos.coords : jitter(pos.coords, i),
        precise: pos.precise,
      };
    })
    .filter((item): item is { lead: Lead; coords: [number, number]; precise: boolean } => item !== null);

  const preciseCount = positioned.filter((p) => p.precise).length;

  return (
    <div className="relative h-full w-full">
      <MapContainer
        center={CENTER}
        zoom={ZOOM}
        className="h-full w-full rounded-xl"
        style={{ background: "#F9FAFB" }}
      >
        <TileLayer url={TILE_URL} attribution={TILE_ATTR} />
        {positioned.map(({ lead, coords, precise }) => {
          const isSelected = lead.lead_id === selectedId;
          const color = scoreColor(lead.lead_score);
          return (
            <CircleMarker
              key={lead.lead_id}
              center={coords}
              radius={isSelected ? 12 : 7}
              pathOptions={{
                color: "#FFFFFF",
                fillColor: color,
                fillOpacity: isSelected ? 1 : precise ? 0.85 : 0.65,
                weight: isSelected ? 3 : 1.5,
                dashArray: precise ? undefined : "3 3",
              }}
              eventHandlers={{ click: () => onSelect?.(lead.lead_id) }}
            >
              <Popup>
                <div className="text-sm text-gray-800">
                  <div className="font-semibold">
                    {lead.project_name ?? lead.permit_number ?? lead.lead_id.slice(0, 8)}
                  </div>
                  <div>Score: {lead.lead_score} | {lead.tier.toUpperCase()}</div>
                  <div>{lead.address?.city}{lead.address?.county ? `, ${lead.address.county}` : ""}</div>
                  {!precise && <div className="italic text-gray-500">Approximate location</div>}
                </div>
              </Popup>
            </CircleMarker>
          );
        })}
      </MapContainer>
      {/* Legend + precision badge */}
      <div className="absolute bottom-2 left-2 z-[1000] rounded-md bg-surface/95 border border-border px-3 py-2 text-[10px] text-text-secondary backdrop-blur-sm shadow-sm space-y-1">
        <div className="flex items-center gap-3">
          <span className="flex items-center gap-1"><span className="inline-block h-2.5 w-2.5 rounded-full bg-[#16A34A]" /> 70+</span>
          <span className="flex items-center gap-1"><span className="inline-block h-2.5 w-2.5 rounded-full bg-[#4F7C59]" /> 55+</span>
          <span className="flex items-center gap-1"><span className="inline-block h-2.5 w-2.5 rounded-full bg-[#E67E22]" /> 45+</span>
          <span className="flex items-center gap-1"><span className="inline-block h-2.5 w-2.5 rounded-full bg-[#DC2626]" /> 30+</span>
          <span className="flex items-center gap-1"><span className="inline-block h-2.5 w-2.5 rounded-full bg-[#9CA3AF]" /> &lt;30</span>
        </div>
        <div>{preciseCount} precise / {positioned.length} mapped of {leads.length} leads</div>
      </div>
    </div>
  );
}
