import { useQuery } from "@tanstack/react-query";
import { fetchData } from "@/lib/api";
import { useAccountContext } from "@/contexts/AccountContext";
import type { FunnelData } from "@/lib/types";

export function useFunnel(dateFrom?: string, dateTo?: string) {
  const { currentAccount } = useAccountContext();

  return useQuery({
    queryKey: ["funnel", currentAccount?.id, dateFrom, dateTo],
    queryFn: () =>
      fetchData<FunnelData>("/dashboard/funnel", {
        date_from: dateFrom,
        date_to: dateTo,
      }),
    enabled: !!currentAccount,
    staleTime: 60_000,
  });
}
