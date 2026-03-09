"use client";

import { ActionFeedItem } from "./ActionFeedItem";
import { ACTION_TYPES } from "@/lib/constants";
import type { ActionLogEntry } from "@/lib/types";

interface ActionFeedFilters {
  action_type?: string;
  triggered_by?: string;
}

interface ActionFeedProps {
  actions: ActionLogEntry[];
  onUndo: (id: string) => void;
  filters: ActionFeedFilters;
  onFilterChange: (filters: ActionFeedFilters) => void;
}

const TRIGGERED_BY_OPTIONS = [
  { value: "", label: "All Triggers" },
  { value: "rule", label: "Automated" },
  { value: "manual", label: "Manual" },
];

export function ActionFeed({
  actions,
  onUndo,
  filters,
  onFilterChange,
}: ActionFeedProps) {
  const filteredActions = actions.filter((a) => {
    if (filters.action_type && a.action_type !== filters.action_type)
      return false;
    if (filters.triggered_by && a.triggered_by !== filters.triggered_by)
      return false;
    return true;
  });

  return (
    <div className="flex flex-col gap-4">
      {/* Filter bar */}
      <div className="flex flex-wrap gap-3 items-center">
        <div className="flex items-center gap-2">
          <label className="text-xs text-gray-400 font-medium whitespace-nowrap">
            Action type
          </label>
          <select
            value={filters.action_type ?? ""}
            onChange={(e) =>
              onFilterChange({
                ...filters,
                action_type: e.target.value || undefined,
              })
            }
            className="bg-[#1a1a1a] border border-[#262626] text-gray-300 text-xs rounded-lg px-3 py-1.5 focus:outline-none focus:ring-1 focus:ring-blue-500"
          >
            <option value="">All Actions</option>
            {ACTION_TYPES.map((t) => (
              <option key={t.value} value={t.value}>
                {t.icon} {t.label}
              </option>
            ))}
          </select>
        </div>

        <div className="flex items-center gap-2">
          <label className="text-xs text-gray-400 font-medium whitespace-nowrap">
            Triggered by
          </label>
          <select
            value={filters.triggered_by ?? ""}
            onChange={(e) =>
              onFilterChange({
                ...filters,
                triggered_by: e.target.value || undefined,
              })
            }
            className="bg-[#1a1a1a] border border-[#262626] text-gray-300 text-xs rounded-lg px-3 py-1.5 focus:outline-none focus:ring-1 focus:ring-blue-500"
          >
            {TRIGGERED_BY_OPTIONS.map((o) => (
              <option key={o.value} value={o.value}>
                {o.label}
              </option>
            ))}
          </select>
        </div>

        {(filters.action_type || filters.triggered_by) && (
          <button
            onClick={() => onFilterChange({})}
            className="text-xs text-gray-500 hover:text-gray-300 transition-colors"
          >
            Clear filters
          </button>
        )}

        <span className="ml-auto text-xs text-gray-500">
          {filteredActions.length} action{filteredActions.length !== 1 ? "s" : ""}
        </span>
      </div>

      {/* Feed list */}
      {filteredActions.length === 0 ? (
        <div className="flex items-center justify-center py-12 text-gray-500 text-sm">
          No actions match your filters
        </div>
      ) : (
        <div className="flex flex-col gap-2">
          {filteredActions.map((action) => (
            <ActionFeedItem
              key={action.id}
              action={action}
              onUndo={onUndo}
            />
          ))}
        </div>
      )}
    </div>
  );
}
