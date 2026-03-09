import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { fetchData, postData, patchData, deleteData } from "@/lib/api";
import { useAccountContext } from "@/contexts/AccountContext";
import type { Rule } from "@/lib/types";

export function useRules() {
  const { currentAccount } = useAccountContext();

  return useQuery({
    queryKey: ["rules", currentAccount?.id],
    queryFn: () => fetchData<Rule[]>("/rules"),
    enabled: !!currentAccount,
    staleTime: 60_000,
  });
}

type RulePayload = Omit<Rule, "id" | "trigger_count" | "estimated_savings" | "last_triggered">;

export function useCreateRule() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: Partial<RulePayload>) => postData<Rule>("/rules", data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["rules"] });
    },
  });
}

export function useUpdateRule() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<RulePayload> }) =>
      patchData<Rule>(`/rules/${id}`, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["rules"] });
    },
  });
}

export function useDeleteRule() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => deleteData<void>(`/rules/${id}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["rules"] });
    },
  });
}
