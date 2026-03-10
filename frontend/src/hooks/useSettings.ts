import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { fetchData, patchData } from "@/lib/api";
import type { Account } from "@/lib/types";

export interface SeasonalityConfig {
  id: string;
  account_id: string;
  month: number;
  multiplier: number;
  notes: string | null;
}

// ── Accounts ──────────────────────────────────────────────────────────────

export function useAccounts() {
  return useQuery({
    queryKey: ["accounts"],
    queryFn: () =>
      fetchData<{ data: Account[] }>("/accounts").then((r) => r.data),
    staleTime: 120_000,
  });
}

interface UpdateAccountPayload {
  name?: string;
  target_cpl?: number | null;
  target_cpa?: number | null;
  target_roas?: number | null;
  timezone?: string;
  currency?: string;
  telegram_chat_id?: string | null;
  is_active?: boolean;
}

export function useUpdateAccount() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: UpdateAccountPayload }) =>
      patchData<Account>(`/accounts/${id}`, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["accounts"] });
    },
  });
}

// ── Seasonality ───────────────────────────────────────────────────────────

export function useSeasonality(accountId: string | null) {
  return useQuery({
    queryKey: ["seasonality", accountId],
    queryFn: async () => {
      const res = await fetchData<{ data: SeasonalityConfig[] }>(
        `/accounts/${accountId}/seasonality`
      );
      return res.data;
    },
    enabled: !!accountId,
    staleTime: 120_000,
  });
}

interface UpdateSeasonalityPayload {
  month: number;
  multiplier: number;
  notes?: string | null;
}

export function useUpdateSeasonality() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      accountId,
      data,
    }: {
      accountId: string;
      data: UpdateSeasonalityPayload;
    }) =>
      patchData<SeasonalityConfig>(
        `/accounts/${accountId}/seasonality/${data.month}`,
        data
      ),
    onSuccess: (_result, { accountId }) => {
      queryClient.invalidateQueries({ queryKey: ["seasonality", accountId] });
    },
  });
}
