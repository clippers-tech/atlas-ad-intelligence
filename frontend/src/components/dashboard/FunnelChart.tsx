"use client";

import { formatNumber, formatPercent, formatCurrency, formatRoas } from "@/lib/utils";
import type { FunnelData } from "@/lib/types";

interface FunnelChartProps {
  data: FunnelData;
}

// Colors for each funnel stage
const STAGE_COLORS = [
  "bg-blue-500",
  "bg-violet-500",
  "bg-indigo-500",
  "bg-purple-500",
  "bg-emerald-500",
];

const STAGE_TEXT = [
  "text-blue-400",
  "text-violet-400",
  "text-indigo-400",
  "text-purple-400",
  "text-emerald-400",
];

export function FunnelChart({ data }: FunnelChartProps) {
  const { stages, conversion_rates, total_revenue, total_spend, true_roas } =
    data;

  const topCount = stages[0]?.count ?? 1;

  return (
    <div className="bg-[#141414] border border-[#262626] rounded-xl p-6">
      <h3 className="text-sm font-semibold text-white mb-6">Conversion Funnel</h3>

      <div className="flex flex-col items-center gap-0 max-w-lg mx-auto">
        {stages.map((stage, idx) => {
          const widthPct = Math.max(
            15,
            Math.round((stage.count / topCount) * 100)
          );
          const convRate = conversion_rates[idx - 1];
          const color = STAGE_COLORS[idx % STAGE_COLORS.length];
          const textColor = STAGE_TEXT[idx % STAGE_TEXT.length];

          return (
            <div key={stage.name} className="w-full flex flex-col items-center">
              {/* Conversion rate between stages */}
              {convRate && (
                <div className="flex items-center gap-2 py-1">
                  <span className="text-gray-600 text-xs">↓</span>
                  <span className="text-xs text-gray-500">
                    {formatPercent(convRate.rate * 100)} conversion
                  </span>
                </div>
              )}

              {/* Stage bar */}
              <div
                className="relative flex items-center justify-center rounded-md h-11 transition-all"
                style={{ width: `${widthPct}%` }}
              >
                <div className={`absolute inset-0 ${color} opacity-20 rounded-md`} />
                <div className={`absolute inset-0 border ${color.replace("bg-", "border-")} border-opacity-40 rounded-md`} />
                <div className="relative flex items-center justify-between w-full px-4">
                  <span className="text-xs font-medium text-gray-200 truncate">
                    {stage.name}
                  </span>
                  <div className="flex items-center gap-3 flex-shrink-0 ml-2">
                    <span className={`text-sm font-bold tabular-nums ${textColor}`}>
                      {formatNumber(stage.count)}
                    </span>
                    <span className="text-xs text-gray-500">
                      {formatPercent(stage.percent_of_top)}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Summary footer */}
      <div className="mt-6 pt-4 border-t border-[#262626] grid grid-cols-3 gap-4">
        <div className="text-center">
          <p className="text-xs text-gray-500 mb-1">Total Revenue</p>
          <p className="text-base font-bold text-white tabular-nums">
            {formatCurrency(total_revenue)}
          </p>
        </div>
        <div className="text-center">
          <p className="text-xs text-gray-500 mb-1">Total Spend</p>
          <p className="text-base font-bold text-white tabular-nums">
            {formatCurrency(total_spend)}
          </p>
        </div>
        <div className="text-center">
          <p className="text-xs text-gray-500 mb-1">True ROAS</p>
          <p className="text-base font-bold text-emerald-400 tabular-nums">
            {formatRoas(true_roas)}
          </p>
        </div>
      </div>
    </div>
  );
}
