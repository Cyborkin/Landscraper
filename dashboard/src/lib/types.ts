export interface Address {
  street: string | null;
  city: string | null;
  state: string | null;
  zip: string | null;
  county: string | null;
}

export interface Coordinates {
  latitude: number | null;
  longitude: number | null;
}

export interface Lead {
  lead_id: string;
  confidence_score: number;
  source_count: number;
  sources: string[];
  lead_score: number;
  tier: "hot" | "warm" | "monitor" | "cold";
  score_breakdown: Record<string, number>;
  permit_number: string | null;
  permit_type: string | null;
  permit_status: string | null;
  jurisdiction: string | null;
  address: Address;
  coordinates: Coordinates;
  property_type: string | null;
  project_name: string | null;
  description: string | null;
  valuation_usd: number | null;
  unit_count: number | null;
  total_sqft: number | null;
  owner_name: string | null;
  filing_date: string | null;
  discovered_at: string | null;
  updated_at: string | null;
  tags: string[];
  validation_status: string | null;
}

export interface PaginationMeta {
  total_count: number;
  page: number;
  page_size: number;
  next_page_url: string | null;
}

export interface LeadListResponse {
  meta: PaginationMeta;
  leads: Lead[];
}

export interface HealthResponse {
  status: string;
  version: string;
  cycle_count: number;
}

export interface CycleStatus {
  cycle_id: string | null;
  status: string;
  metrics: Record<string, unknown>;
}

export interface TracingStatus {
  enabled: boolean;
  project: string | null;
}

export interface LeadFilters {
  tier?: string;
  county?: string;
  min_score?: number;
  property_type?: string;
  page?: number;
  page_size?: number;
}

export interface TierDistribution {
  hot: number;
  warm: number;
  monitor: number;
  cold: number;
}

export interface CycleMetrics {
  total_raw_records: number;
  total_developments: number;
  total_validated_leads: number;
  total_errors: number;
  yield_rate: number;
  conversion_rate: number;
  error_rate: number;
  unique_source_count: number;
  tier_distribution: TierDistribution;
  avg_confidence: number;
  avg_lead_score: number;
}
