import { useQuery } from "@tanstack/react-query";
import { fetchData } from "@/lib/api";
import { useAccountContext } from "@/contexts/AccountContext";
import type { Insight } from "@/lib/types";

export function useInsights(type?: string) {
  const { currentAccount } = useAccountContext();

  return useQuery({
    queryKey: ["insights", currentAccount?.id, type],
    queryFn: () =>
      fetchData<{ data: Insight[] }>("/insights", { type }),
    enabled: !!currentAccount,
    staleTime: 120_000,
  });
}
