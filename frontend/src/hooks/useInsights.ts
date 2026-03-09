import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { fetchData, postData } from "@/lib/api";
import { useAccountContext } from "@/contexts/AccountContext";
import type { ClaudeInsight } from "@/lib/types";

export function useInsights(type?: string) {
  const { currentAccount } = useAccountContext();

  return useQuery({
    queryKey: ["insights", currentAccount?.id, type],
    queryFn: () =>
      fetchData<ClaudeInsight[]>("/claude/insights", { type }),
    enabled: !!currentAccount,
    staleTime: 120_000,
  });
}

interface AskClaudePayload {
  question: string;
  account_id: string;
}

export function useAskClaude() {
  const queryClient = useQueryClient();
  const { currentAccount } = useAccountContext();

  return useMutation({
    mutationFn: (question: string) =>
      postData<ClaudeInsight>("/claude/ask", {
        question,
        account_id: currentAccount?.id,
      } satisfies AskClaudePayload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["insights"] });
    },
  });
}
