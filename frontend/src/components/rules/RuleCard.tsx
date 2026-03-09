"use client";

import type { Rule } from "@/lib/types";
import { RULE_TYPES } from "@/lib/constants";
import RuleStats from "./RuleStats";

interface RuleCardProps {
  rule: Rule;
  onToggle: (id: string, enabled: boolean) => void;
  onEdit: (rule: Rule) => void;
  onViewHistory: (rule: Rule) => void;
}

const TYPE_ICONS: Record<string, string> = {
  kill: "🔴",
  scale: "🟢",
  launch: "🔵",
  bid: "🟡",
};

const TYPE_COLORS: Record<string, string> = {
  kill: "border-red-900/60 bg-red-950/20",
  scale: "border-emerald-900/60 bg-emerald-950/20",
  launch: "border-blue-900/60 bg-blue-950/20",
  bid: "border-amber-900/60 bg-amber-950/20",
};

function buildConditionSummary(rule: Rule): string {
  const cond = rule.condition_json;
  const parts = [`IF ${cond.metric} ${cond.operator} ${cond.value}`];
  if (cond.and) {
    cond.and.forEach((c) =>
      parts.push(`AND ${c.metric} ${c.operator} ${c.value}`)
    );
  }
  const action = rule.action_json;
  const actionStr = action.percent
    ? `${action.action.replace(/_/g, " ")} ${action.percent}%`
    : action.action.replace(/_/g, " ").toUpperCase();
  return `${parts.join(" ")} → ${actionStr}`;
}

export default function RuleCard({
  rule,
  onToggle,
  onEdit,
  onViewHistory,
}: RuleCardProps) {
  const typeObj = RULE_TYPES.find((t) => t.value === rule.type);
  const icon = TYPE_ICONS[rule.type] ?? "⚙️";
  const colorClass = TYPE_COLORS[rule.type] ?? "border-gray-800 bg-gray-900/40";

  return (
    <div
      className={`border rounded-xl p-4 space-y-3 transition-all ${colorClass} ${
        !rule.is_enabled ? "opacity-50" : ""
      }`}
    >
      <div className="flex items-start justify-between gap-3">
        {/* Left: icon + name */}
        <div className="flex items-center gap-3 min-w-0">
          <span className="text-xl flex-shrink-0">{icon}</span>
          <div className="min-w-0">
            <div className="flex items-center gap-2">
              <h3 className="font-semibold text-gray-100 truncate">{rule.name}</h3>
              {typeObj && (
                <span className="px-1.5 py-0.5 rounded text-xs font-medium bg-gray-800 text-gray-400">
                  {typeObj.label}
                </span>
              )}
            </div>
            {rule.description && (
              <p className="text-xs text-gray-500 mt-0.5 truncate">{rule.description}</p>
            )}
          </div>
        </div>

        {/* Toggle */}
        <button
          onClick={() => onToggle(rule.id, !rule.is_enabled)}
          className={`flex-shrink-0 w-10 h-5 rounded-full transition-colors ${
            rule.is_enabled ? "bg-violet-600" : "bg-gray-700"
          } relative`}
          aria-label={rule.is_enabled ? "Disable rule" : "Enable rule"}
        >
          <span
            className={`absolute top-0.5 w-4 h-4 bg-white rounded-full shadow transition-transform ${
              rule.is_enabled ? "translate-x-5" : "translate-x-0.5"
            }`}
          />
        </button>
      </div>

      {/* Condition summary */}
      <p className="text-xs font-mono text-gray-400 bg-gray-900/60 rounded px-3 py-2">
        {buildConditionSummary(rule)}
      </p>

      {/* Stats */}
      <RuleStats
        triggerCount={rule.trigger_count ?? 0}
        estimatedSavings={rule.estimated_savings ?? 0}
        lastTriggered={rule.last_triggered ?? null}
      />

      {/* Meta + actions */}
      <div className="flex items-center justify-between pt-1">
        <span className="text-xs text-gray-600">
          Cooldown: {rule.cooldown_minutes}m · Priority: {rule.priority}
        </span>
        <div className="flex gap-2">
          <button
            onClick={() => onViewHistory(rule)}
            className="text-xs px-2 py-1 rounded bg-gray-800 hover:bg-gray-700 text-gray-400 transition-colors"
          >
            History
          </button>
          <button
            onClick={() => onEdit(rule)}
            className="text-xs px-2 py-1 rounded bg-gray-800 hover:bg-gray-700 text-gray-300 transition-colors"
          >
            Edit
          </button>
        </div>
      </div>
    </div>
  );
}
