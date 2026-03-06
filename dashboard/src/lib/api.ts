import type {
  CycleHistoryEntry,
  CycleStatus,
  HealthResponse,
  Lead,
  LeadFilters,
  LeadListResponse,
  TracingStatus,
} from "./types";

const API_KEY = "landscraper-poc-key";

const headers: Record<string, string> = {
  Authorization: `Bearer ${API_KEY}`,
  "Content-Type": "application/json",
};

async function fetchApi<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(path, { ...init, headers: { ...headers, ...init?.headers } });
  if (!res.ok) {
    throw new Error(`API error: ${res.status} ${res.statusText}`);
  }
  return res.json();
}

export async function fetchHealth(): Promise<HealthResponse> {
  return fetchApi("/health");
}

export async function fetchLeads(filters: LeadFilters = {}): Promise<LeadListResponse> {
  const params = new URLSearchParams();
  if (filters.tier) params.set("tier", filters.tier);
  if (filters.county) params.set("county", filters.county);
  if (filters.min_score) params.set("min_score", String(filters.min_score));
  if (filters.property_type) params.set("property_type", filters.property_type);
  if (filters.page) params.set("page", String(filters.page));
  if (filters.page_size) params.set("page_size", String(filters.page_size));
  const qs = params.toString();
  return fetchApi(`/api/v1/leads${qs ? `?${qs}` : ""}`);
}

export async function fetchLead(leadId: string): Promise<Lead> {
  return fetchApi(`/api/v1/leads/${leadId}`);
}

export async function fetchCycleStatus(): Promise<CycleStatus> {
  return fetchApi("/api/v1/cycle/status");
}

export async function triggerCycle(): Promise<CycleStatus> {
  return fetchApi("/api/v1/cycle/trigger", {
    method: "POST",
    body: JSON.stringify({ sources: null }),
  });
}

export async function fetchTracingStatus(): Promise<TracingStatus> {
  return fetchApi("/api/v1/tracing/status");
}

export async function fetchCycleHistory(): Promise<CycleHistoryEntry[]> {
  return fetchApi("/api/v1/cycles");
}
