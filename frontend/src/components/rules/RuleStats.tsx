"use client";

import { formatCurrency, formatRelative } from "@/lib/utils";

interface RuleStatsProps {
  triggerCount: number;
  estimatedSavings: number;
  lastTriggered: string | null;
}

export default function RuleStats({
  triggerCount,
  estimatedSavings,
  lastTriggered,
}: RuleStatsProps) {
  return (
    <div className="flex items-center gap-3 text-xs text-gray-500 flex-wrap">
      <span className="flex items-center gap-1">
        <span className="text-gray-400">🔁</span>
        <span>
          Triggered{" "}
          <span className="font-semibold text-gray-300">{triggerCount}</span>{" "}
          {triggerCount === 1 ? "time" : "times"}
        </span>
      </span>
      <span className="text-gray-700">|</span>
      <span className="flex items-center gap-1">
        <span>💷</span>
        <span>
          Saved est.{" "}
          <span className="font-semibold text-emerald-400">
            {formatCurrency(estimatedSavings)}
          </span>
        </span>
      </span>
      <span className="text-gray-700">|</span>
      <span>
        Last:{" "}
        <span className="text-gray-300">
          {lastTriggered ? formatRelative(lastTriggered) : "Never"}
        </span>
      </span>
    </div>
  );
}
