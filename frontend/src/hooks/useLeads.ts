import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { fetchData, patchData } from "@/lib/api";
import { useAccountContext } from "@/contexts/AccountContext";
import type { Lead, LeadJourney, PaginatedResponse } from "@/lib/types";

interface LeadFilters {
  page?: number;
  per_page?: number;
  stage?: string;
  source_campaign_id?: string;
  search?: string;
  date_from?: string;
  date_to?: string;
}

export function useLeads(filters: LeadFilters = {}) {
  const { currentAccount } = useAccountContext();
  const { page = 1, per_page = 25, ...rest } = filters;

  return useQuery({
    queryKey: ["leads", currentAccount?.id, page, per_page, rest],
    queryFn: () =>
      fetchData<PaginatedResponse<Lead>>("/leads", { page, per_page, ...rest }),
    enabled: !!currentAccount,
    staleTime: 30_000,
  });
}

interface UpdateLeadPayload {
  stage?: string;
  revenue?: number | null;
  booked_at?: string | null;
  notes?: string;
}

export function useUpdateLead() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: UpdateLeadPayload }) =>
      patchData<Lead>(`/leads/${id}`, data),
    onSuccess: (updated) => {
      queryClient.invalidateQueries({ queryKey: ["leads"] });
      queryClient.invalidateQueries({
        queryKey: ["lead-journey", updated.id],
      });
    },
  });
}

export function useLeadJourney(id: string | null) {
  return useQuery({
    queryKey: ["lead-journey", id],
    queryFn: () => fetchData<LeadJourney>(`/leads/${id}/journey`),
    enabled: !!id,
    staleTime: 30_000,
  });
}
