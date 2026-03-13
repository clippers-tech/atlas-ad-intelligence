import { useState, useCallback } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { postData } from "@/lib/api";

type EntityType = "ads" | "ad-sets" | "campaigns";

interface ToggleResult {
  success: boolean;
  id: string;
  new_status: string;
}

/**
 * Hook to toggle pause/active status for ads, ad sets,
 * or campaigns. Updates Meta + DB, then refetches list.
 */
export function useStatusToggle(
  entityType: EntityType,
  invalidateKeys: string[],
) {
  const qc = useQueryClient();
  const [pendingId, setPendingId] = useState<string | null>(null);

  const mutation = useMutation({
    mutationFn: async ({
      id, newStatus,
    }: { id: string; newStatus: string }) => {
      setPendingId(id);
      return postData<ToggleResult>(
        `/actions/${entityType}/${id}/status`,
        { status: newStatus },
      );
    },
    onSuccess: () => {
      invalidateKeys.forEach((key) =>
        qc.invalidateQueries({ queryKey: [key] })
      );
    },
    onSettled: () => setPendingId(null),
  });

  const toggle = useCallback(
    (id: string, currentStatus: string) => {
      const newStatus =
        currentStatus.toUpperCase() === "ACTIVE"
          ? "PAUSED"
          : "ACTIVE";
      mutation.mutate({ id, newStatus });
    },
    [mutation],
  );

  return { toggle, pendingId, isToggling: mutation.isPending };
}
