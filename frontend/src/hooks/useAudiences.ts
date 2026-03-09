import { useQuery } from "@tanstack/react-query";
import { fetchData } from "@/lib/api";
import { useAccountContext } from "@/contexts/AccountContext";
import type { AudiencePerformance } from "@/lib/types";

interface AudiencesResponse {
  audiences: AudiencePerformance[];
  heatmap_data: unknown;
  type_comparison: unknown;
  test_queue: unknown;
  alerts: unknown;
}

export function useAudiences() {
  const { currentAccount } = useAccountContext();

  return useQuery({
    queryKey: ["audiences", currentAccount?.id],
    queryFn: () => fetchData<AudiencesResponse>("/dashboard/audiences"),
    enabled: !!currentAccount,
    staleTime: 60_000,
  });
}
