"use client";

import { useState } from "react";
import { useActions, useUndoAction } from "@/hooks/useActions";
import { ActionFeed } from "@/components/dashboard/ActionFeed";
import { ConfirmDialog } from "@/components/common/ConfirmDialog";
import { LoadingSpinner } from "@/components/common/LoadingSpinner";
import { EmptyState } from "@/components/common/EmptyState";

interface Filters {
  action_type?: string;
  triggered_by?: string;
}

export default function ActionsPage() {
  const [page, setPage] = useState(1);
  const [filters, setFilters] = useState<Filters>({});
  const [pendingUndoId, setPendingUndoId] = useState<string | null>(null);

  const { data, isLoading, isError, isFetching } = useActions(
    page,
    25,
    filters
  );
  const undoMutation = useUndoAction();

  const actions = data?.data ?? [];
  const total = data?.meta?.total ?? 0;
  const hasMore = actions.length < total;

  function handleUndo(id: string) {
    setPendingUndoId(id);
  }

  function confirmUndo() {
    if (!pendingUndoId) return;
    undoMutation.mutate(pendingUndoId, {
      onSettled: () => setPendingUndoId(null),
    });
  }

  function handleLoadMore() {
    setPage((p) => p + 1);
  }

  if (isLoading && page === 1) {
    return <LoadingSpinner fullHeight label="Loading actions..." />;
  }

  if (isError) {
    return (
      <EmptyState
        title="Failed to load actions"
        description="There was an error fetching action log data."
        icon="⚠️"
      />
    );
  }

  return (
    <div className="flex flex-col gap-6 p-6">
      {/* Page header */}
      <div>
        <h1 className="text-xl font-bold text-white">Action Feed</h1>
        <p className="text-sm text-gray-500 mt-0.5">
          Automated and manual actions log · {total} total
        </p>
      </div>

      {actions.length === 0 ? (
        <EmptyState
          title="No actions yet"
          description="Automated rule actions and manual changes will appear here."
          icon="⚡"
        />
      ) : (
        <ActionFeed
          actions={actions}
          onUndo={handleUndo}
          filters={filters}
          onFilterChange={setFilters}
        />
      )}

      {/* Load more */}
      {hasMore && (
        <div className="flex justify-center pt-2">
          <button
            onClick={handleLoadMore}
            disabled={isFetching}
            className="px-5 py-2 text-sm font-medium text-gray-300 border border-[#262626] rounded-lg hover:bg-[#1a1a1a] hover:text-white transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isFetching ? "Loading…" : `Load more (${total - actions.length} remaining)`}
          </button>
        </div>
      )}

      {/* Confirm undo dialog */}
      <ConfirmDialog
        open={!!pendingUndoId}
        title="Undo this action?"
        description="This will attempt to reverse the action. Some changes may not be fully reversible depending on the current state."
        confirmLabel="Undo"
        variant="danger"
        onConfirm={confirmUndo}
        onCancel={() => setPendingUndoId(null)}
      />
    </div>
  );
}
