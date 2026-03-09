import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { fetchData, postData, deleteData } from "@/lib/api";
import { useAccountContext } from "@/contexts/AccountContext";
import type { Competitor, CompetitorAd } from "@/lib/types";

export function useCompetitors() {
  const { currentAccount } = useAccountContext();

  return useQuery({
    queryKey: ["competitors", currentAccount?.id],
    queryFn: () => fetchData<Competitor[]>("/competitors"),
    enabled: !!currentAccount,
    staleTime: 120_000,
  });
}

export function useCompetitorAds(id: string | null) {
  return useQuery({
    queryKey: ["competitor-ads", id],
    queryFn: () => fetchData<CompetitorAd[]>(`/competitors/${id}/ads`),
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
