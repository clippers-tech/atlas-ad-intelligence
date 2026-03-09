"use client";

import { useState } from "react";
import { formatNumber, formatPercent, formatRelative } from "@/lib/utils";
import type { Anomaly } from "@/lib/types";

interface AnomalyDotProps {
  anomaly: Anomaly;
}

function getSeverityColor(severity: Anomaly["severity"]): string {
  switch (severity) {
    case "high":
      return "bg-red-500 ring-red-500/30";
    case "medium":
      return "bg-amber-400 ring-amber-400/30";
    case "low":
      return "bg-gray-500 ring-gray-500/30";
    default:
      return "bg-gray-500 ring-gray-500/30";
  }
}

function getSeverityLabel(severity: Anomaly["severity"]): string {
  switch (severity) {
    case "high":
      return "High";
    case "medium":
      return "Medium";
    case "low":
      return "Low";
  }
}

export function AnomalyDot({ anomaly }: AnomalyDotProps) {
  const [showTooltip, setShowTooltip] = useState(false);
  const colorClass = getSeverityColor(anomaly.severity);

  return (
    <div className="relative inline-flex">
      <button
        className={`w-3 h-3 rounded-full ring-2 ring-offset-1 ring-offset-[#141414] cursor-pointer transition-transform hover:scale-125 ${colorClass}`}
        onMouseEnter={() => setShowTooltip(true)}
        onMouseLeave={() => setShowTooltip(false)}
        aria-label={`${anomaly.severity} anomaly on ${anomaly.metric}`}
      />
      {showTooltip && (
        <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 z-50 w-56 pointer-events-none">
          <div className="bg-[#1e1e1e] border border-[#262626] rounded-lg p-3 shadow-xl text-xs">
            <div className="flex items-center justify-between mb-2">
              <span className="font-semibold text-gray-100 capitalize">
                {anomaly.metric.replace(/_/g, " ")}
              </span>
              <span
                className={`px-1.5 py-0.5 rounded text-[10px] font-medium ${
                  anomaly.severity === "high"
                    ? "bg-red-500/20 text-red-400"
                    : anomaly.severity === "medium"
                    ? "bg-amber-500/20 text-amber-400"
                    : "bg-gray-500/20 text-gray-400"
                }`}
              >
                {getSeverityLabel(anomaly.severity)}
              </span>
            </div>
            {anomaly.ad_name && (
              <p className="text-gray-500 mb-1 truncate">{anomaly.ad_name}</p>
            )}
            <div className="grid grid-cols-2 gap-x-3 gap-y-0.5 text-gray-400">
              <span>Current</span>
              <span className="text-gray-200 text-right tabular-nums">
                {formatNumber(anomaly.current_value)}
              </span>
              <span>Average</span>
              <span className="text-gray-200 text-right tabular-nums">
                {formatNumber(anomaly.avg_value)}
              </span>
              <span>Deviation</span>
              <span
                className={`text-right tabular-nums ${
                  anomaly.deviation_percent > 0
                    ? "text-red-400"
                    : "text-emerald-400"
                }`}
              >
                {anomaly.deviation_percent > 0 ? "+" : ""}
                {formatPercent(anomaly.deviation_percent)}
              </span>
            </div>
            <p className="text-gray-600 mt-2">
              {formatRelative(anomaly.timestamp)}
            </p>
          </div>
          {/* Arrow */}
          <div className="absolute top-full left-1/2 -translate-x-1/2 -mt-px border-4 border-transparent border-t-[#262626]" />
        </div>
      )}
    </div>
  );
}
