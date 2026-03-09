import { useQuery } from "@tanstack/react-query";
import { fetchData } from "@/lib/api";
import { useAccountContext } from "@/contexts/AccountContext";
import type { DashboardOverview } from "@/lib/types";

export function useDashboardOverview(dateFrom?: string, dateTo?: string) {
  const { currentAccount } = useAccountContext();

  return useQuery({
    queryKey: ["dashboard", "overview", currentAccount?.id, dateFrom, dateTo],
    queryFn: () =>
      fetchData<DashboardOverview>("/dashboard/overview", {
        date_from: dateFrom,
        date_to: dateTo,
      }),
    enabled: !!currentAccount,
    staleTime: 60_000,
  });
}
