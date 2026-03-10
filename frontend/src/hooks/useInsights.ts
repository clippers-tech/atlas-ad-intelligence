import { useQuery } from "@tanstack/react-query";
import { fetchData } from "@/lib/api";
import { useAccountContext } from "@/contexts/AccountContext";
import type { Insight } from "@/lib/types";

interface InsightsResponse {
  data: Insight[];
  meta?: { total: number; page: number; per_page: number };
}

export function useInsights(type?: string) {
  const { currentAccount } = useAccountContext();

  return useQuery({
    queryKey: ["insights", currentAccount?.id, type],
    queryFn: async () => {
      const res = await fetchData<InsightsResponse>("/insights", { type });
      return res.data;
    },
    enabled: !!currentAccount,
    staleTime: 120_000,
  });
}
