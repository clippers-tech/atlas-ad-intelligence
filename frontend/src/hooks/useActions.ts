import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { fetchData, postData } from "@/lib/api";
import { useAccountContext } from "@/contexts/AccountContext";
import type { ActionLogEntry, PaginatedResponse } from "@/lib/types";

interface ActionsFilters {
  page?: number;
  per_page?: number;
  action_type?: string;
  triggered_by?: string;
}

export function useActions(
  page = 1,
  perPage = 25,
  filters?: Omit<ActionsFilters, "page" | "per_page">
) {
  const { currentAccount } = useAccountContext();

  return useQuery({
    queryKey: ["actions", currentAccount?.id, page, perPage, filters],
    queryFn: () =>
      fetchData<PaginatedResponse<ActionLogEntry>>("/dashboard/actions", {
        page,
        per_page: perPage,
        ...filters,
      }),
    enabled: !!currentAccount,
    staleTime: 30_000,
  });
}

export function useUndoAction() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) =>
      postData<ActionLogEntry>(`/dashboard/actions/${id}/undo`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["actions"] });
    },
  });
}
