import { useQuery } from "@tanstack/react-query";
import { fetchData } from "@/lib/api";
import { useAccountContext } from "@/contexts/AccountContext";
import type { Anomaly } from "@/lib/types";

export function useAnomalies(dateFrom?: string, dateTo?: string) {
  const { currentAccount } = useAccountContext();

  return useQuery({
    queryKey: ["anomalies", currentAccount?.id, dateFrom, dateTo],
    queryFn: () =>
      fetchData<Anomaly[]>("/dashboard/anomalies", {
        date_from: dateFrom,
        date_to: dateTo,
      }),
    enabled: !!currentAccount,
    staleTime: 60_000,
  });
}
