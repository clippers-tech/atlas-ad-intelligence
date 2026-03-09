"use client";

import type { Rule } from "@/lib/types";
import { RULE_TYPES } from "@/lib/constants";
import RuleCard from "./RuleCard";

interface RuleListProps {
  rules: Rule[];
  onToggle: (id: string, enabled: boolean) => void;
  onEdit: (rule: Rule) => void;
  onCreate: () => void;
  onViewHistory: (rule: Rule) => void;
}

const GROUP_LABELS: Record<string, string> = {
  kill: "Kill Rules — Pause poor performers",
  scale: "Scale Rules — Amplify winners",
  launch: "Launch Rules — Auto-launch new tests",
  bid: "Bid Rules — Dynamic bid management",
};

export default function RuleList({
  rules,
  onToggle,
  onEdit,
  onCreate,
  onViewHistory,
}: RuleListProps) {
  return (
    <div className="space-y-8">
      {/* Top bar */}
      <div className="flex items-center justify-between">
        <p className="text-sm text-gray-400">{rules.length} rules configured</p>
        <button
          onClick={onCreate}
          className="flex items-center gap-2 px-4 py-2 bg-violet-600 hover:bg-violet-500 text-white text-sm font-medium rounded-lg transition-colors"
        >
          + Add Rule
        </button>
      </div>

      {/* Grouped sections */}
      {RULE_TYPES.map((typeObj) => {
        const group = rules.filter((r) => r.type === typeObj.value);
        return (
          <section key={typeObj.value}>
            <div className="flex items-center gap-3 mb-3">
              <h2 className="text-sm font-semibold text-gray-300">
                {GROUP_LABELS[typeObj.value] ?? typeObj.label}
              </h2>
              <span className="px-2 py-0.5 rounded-full text-xs bg-gray-800 text-gray-500">
                {group.length}
              </span>
            </div>

            {group.length === 0 ? (
              <div className="border border-dashed border-gray-800 rounded-xl py-6 text-center text-sm text-gray-600">
                No {typeObj.label.toLowerCase()} rules yet.{" "}
                <button
                  onClick={onCreate}
                  className="text-violet-400 hover:text-violet-300 transition-colors"
                >
                  Create one →
                </button>
              </div>
            ) : (
              <div className="grid gap-3 sm:grid-cols-2">
                {group.map((rule) => (
                  <RuleCard
                    key={rule.id}
                    rule={rule}
                    onToggle={onToggle}
                    onEdit={onEdit}
                    onViewHistory={onViewHistory}
                  />
                ))}
              </div>
            )}
          </section>
        );
      })}
    </div>
  );
}
