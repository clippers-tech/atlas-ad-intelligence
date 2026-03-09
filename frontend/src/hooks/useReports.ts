import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { fetchData, postData } from "@/lib/api";
import { useAccountContext } from "@/contexts/AccountContext";

export interface Report {
  id: string;
  account_id: string;
  name: string;
  type: string;
  status: "pending" | "ready" | "failed";
  download_url: string | null;
  date_from: string | null;
  date_to: string | null;
  created_at: string;
}

export function useReports() {
  const { currentAccount } = useAccountContext();

  return useQuery({
    queryKey: ["reports", currentAccount?.id],
    queryFn: () => fetchData<Report[]>("/reports"),
    enabled: !!currentAccount,
    staleTime: 30_000,
  });
}

interface GenerateReportPayload {
  type: string;
  date_from?: string;
  date_to?: string;
  name?: string;
}

export function useGenerateReport() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: GenerateReportPayload) =>
      postData<Report>("/reports/generate", data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["reports"] });
    },
  });
}
