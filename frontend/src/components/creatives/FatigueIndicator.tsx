"use client";

import { FATIGUE_LEVELS } from "@/lib/constants";

interface FatigueIndicatorProps {
  level: "fresh" | "declining" | "burned";
}

export function FatigueIndicator({ level }: FatigueIndicatorProps) {
  const config = FATIGUE_LEVELS[level];

  const bgColors = {
    fresh: "bg-emerald-500/20 text-emerald-400 border-emerald-500/30",
    declining: "bg-amber-500/20 text-amber-400 border-amber-500/30",
    burned: "bg-red-500/20 text-red-400 border-red-500/30",
  };

  return (
    <span
      className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full border text-xs font-medium ${bgColors[level]}`}
    >
      <span role="img" aria-label={config.label}>
        {config.emoji}
      </span>
      {config.label}
    </span>
  );
}
