"use client";

import { formatRelative } from "@/lib/utils";
import { ACTION_TYPES } from "@/lib/constants";
import type { ActionLogEntry } from "@/lib/types";

interface ActionFeedItemProps {
  action: ActionLogEntry;
  onUndo: (id: string) => void;
}

function getActionIcon(actionType: string): string {
  const found = ACTION_TYPES.find((a) => a.value === actionType);
  return found?.icon ?? "⚡";
}

function getActionLabel(actionType: string): string {
  const found = ACTION_TYPES.find((a) => a.value === actionType);
  return found?.label ?? actionType;
}

function buildDescription(action: ActionLogEntry): string {
  const details = action.details_json ?? {};
  const adName = action.ad_name ?? (details.ad_name as string) ?? "an ad";
  const label = getActionLabel(action.action_type);

  switch (action.action_type) {
    case "pause":
      return `Paused "${adName}"`;
    case "resume":
      return `Resumed "${adName}"`;
    case "increase_budget": {
      const pct = details.percent as number | undefined;
      return `Increased budget of "${adName}"${pct ? ` by ${pct}%` : ""}`;
    }
    case "decrease_budget": {
      const pct = details.percent as number | undefined;
      return `Decreased budget of "${adName}"${pct ? ` by ${pct}%` : ""}`;
    }
    case "duplicate":
      return `Duplicated "${adName}"`;
    case "bid_adjust": {
      const bid = details.bid as number | undefined;
      return `Adjusted bid for "${adName}"${bid ? ` to £${bid}` : ""}`;
    }
    default:
      return `${label}: ${adName}`;
  }
}

function triggeredByLabel(by: string): string {
  return by === "rule" ? "Automated" : by === "manual" ? "Manual" : by;
}

export function ActionFeedItem({ action, onUndo }: ActionFeedItemProps) {
  const canUndo =
    action.is_reversible && !action.reversed_at;
  const isReversed = !!action.reversed_at;

  return (
    <div className="bg-[#141414] border border-[#262626] rounded-lg px-4 py-3 flex items-start gap-3">
      <span className="text-xl flex-shrink-0 mt-0.5" role="img" aria-label={action.action_type}>
        {getActionIcon(action.action_type)}
      </span>
      <div className="flex-1 min-w-0">
        <div className="flex items-center justify-between gap-2 flex-wrap">
          <p className="text-sm text-gray-200 font-medium truncate">
            {buildDescription(action)}
          </p>
          <span className="text-xs text-gray-500 flex-shrink-0">
            {formatRelative(action.created_at)}
          </span>
        </div>
        <div className="flex items-center gap-3 mt-1 flex-wrap">
          {action.rule_name && (
            <span className="text-xs text-gray-500">
              Rule: <span className="text-gray-400">{action.rule_name}</span>
            </span>
          )}
          <span className="text-xs px-1.5 py-0.5 rounded bg-[#1e1e1e] text-gray-500">
            {triggeredByLabel(action.triggered_by)}
          </span>
          {isReversed && (
            <span className="text-xs text-amber-500">↩ Undone</span>
          )}
        </div>
      </div>
      {canUndo && (
        <button
          onClick={() => onUndo(action.id)}
          className="flex-shrink-0 text-xs font-medium text-blue-400 hover:text-blue-300 border border-blue-500/30 hover:border-blue-400/50 rounded px-2.5 py-1 transition-colors"
        >
          Undo
        </button>
      )}
    </div>
  );
}
