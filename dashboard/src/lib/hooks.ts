import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  fetchHealth,
  fetchLeads,
  fetchLead,
  fetchCycleStatus,
  triggerCycle,
  fetchTracingStatus,
} from "./api";
import type { LeadFilters } from "./types";

export function useHealth() {
  return useQuery({
    queryKey: ["health"],
    queryFn: fetchHealth,
    refetchInterval: 30_000,
  });
}

export function useLeads(filters: LeadFilters = {}) {
  return useQuery({
    queryKey: ["leads", filters],
    queryFn: () => fetchLeads(filters),
  });
}

export function useLead(leadId: string) {
  return useQuery({
    queryKey: ["lead", leadId],
    queryFn: () => fetchLead(leadId),
    enabled: !!leadId,
  });
}

export function useCycleStatus() {
  return useQuery({
    queryKey: ["cycleStatus"],
    queryFn: fetchCycleStatus,
    refetchInterval: (query) => {
      const status = query.state.data?.status;
      return status === "triggered" || status === "in_progress" ? 5_000 : 30_000;
    },
  });
}

export function useTriggerCycle() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: triggerCycle,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["cycleStatus"] });
    },
  });
}

export function useTracingStatus() {
  return useQuery({
    queryKey: ["tracingStatus"],
    queryFn: fetchTracingStatus,
  });
}
