import { useQuery } from "@tanstack/react-query";
import { fetchData } from "@/lib/api";
import { useAccountContext } from "@/contexts/AccountContext";
import { useDateRange } from "@/contexts/DateRangeContext";
import type { DashboardOverview } from "@/lib/types";

interface DashboardResponse {
  data: DashboardOverview;
}

export function useDashboardOverview() {
  const { currentAccount } = useAccountContext();
  const { dateFrom, dateTo, rangeKey } = useDateRange();

  return useQuery({
    queryKey: ["dashboard", "overview", currentAccount?.id, rangeKey],
    queryFn: async () => {
      const res = await fetchData<DashboardResponse>("/dashboard/overview", {
        date_from: dateFrom,
        date_to: dateTo,
      });
      return res.data;
    },
    enabled: !!currentAccount,
    staleTime: 60_000,
  });
}
