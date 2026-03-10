import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { fetchData, postData, deleteData } from "@/lib/api";
import { useAccountContext } from "@/contexts/AccountContext";
import type { Competitor, CompetitorAd } from "@/lib/types";

interface CompetitorsResponse {
  data: Competitor[];
  meta?: { total: number; page: number; per_page: number };
}

export function useCompetitors() {
  const { currentAccount } = useAccountContext();

  return useQuery({
    queryKey: ["competitors", currentAccount?.id],
    queryFn: async () => {
      const res = await fetchData<CompetitorsResponse>("/competitors");
      return res.data;
    },
    enabled: !!currentAccount,
    staleTime: 120_000,
  });
}

export function useCompetitorAds(id: string | null) {
  return useQuery({
    queryKey: ["competitor-ads", id],
    queryFn: async () => {
      const res = await fetchData<{ data: CompetitorAd[] }>(`/competitors/${id}/ads`);
      return res.data;
    },
    enabled: !!id,
    staleTime: 120_000,
  });
}

interface AddCompetitorPayload {
  competitor_name: string;
  meta_page_id?: string;
  website_url?: string;
}

export function useAddCompetitor() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: AddCompetitorPayload) =>
      postData<Competitor>("/competitors", data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["competitors"] });
    },
  });
}

export function useDeleteCompetitor() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => deleteData<void>(`/competitors/${id}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["competitors"] });
    },
  });
}
