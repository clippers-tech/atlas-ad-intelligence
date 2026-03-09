import { useQuery } from "@tanstack/react-query";
import { fetchData } from "@/lib/api";
import { useAccountContext } from "@/contexts/AccountContext";
import type { CreativePerformance } from "@/lib/types";

export function useCreatives(sortBy?: string, order?: "asc" | "desc") {
  const { currentAccount } = useAccountContext();

  return useQuery({
    queryKey: ["creatives", currentAccount?.id, sortBy, order],
    queryFn: () =>
      fetchData<CreativePerformance[]>("/dashboard/creatives", {
        sort_by: sortBy,
        order,
      }),
    enabled: !!currentAccount,
    staleTime: 60_000,
  });
}
