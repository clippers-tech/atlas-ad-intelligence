"use client";

import { BarChart } from "@tremor/react";
import { formatCurrency, formatPercent } from "@/lib/utils";

interface TypeComparisonItem {
  type: string;
  avg_cpl: number;
  close_rate: number;
}

interface TypeComparisonProps {
  data: TypeComparisonItem[];
}

function formatTypeLabel(type: string): string {
  return type.charAt(0).toUpperCase() + type.slice(1);
}

export function TypeComparison({ data }: TypeComparisonProps) {
  if (!data || data.length === 0) {
    return (
      <div className="bg-[#141414] border border-[#262626] rounded-xl p-6 text-center text-gray-500 text-sm">
        No audience type data available
      </div>
    );
  }

  const chartData = data.map((d) => ({
    Type: formatTypeLabel(d.type),
    "Avg CPL": d.avg_cpl,
    "Close Rate %": parseFloat((d.close_rate * 100).toFixed(1)),
  }));

  return (
    <div className="bg-[#141414] border border-[#262626] rounded-xl p-6">
      <h3 className="text-sm font-semibold text-white mb-4">
        Audience Type Comparison
      </h3>
      <BarChart
        data={chartData}
        index="Type"
        categories={["Avg CPL"]}
        colors={["blue"]}
        valueFormatter={(val: number) => formatCurrency(val)}
        className="h-48 mt-2"
        showLegend={false}
        showGridLines={false}
        showAnimation
      />
      {/* Close rate summary */}
      <div className="mt-4 pt-4 border-t border-[#262626]">
        <p className="text-xs font-medium text-gray-400 mb-3">Close Rate by Type</p>
        <div className="flex flex-wrap gap-3">
          {data.map((d) => (
            <div key={d.type} className="flex flex-col items-center gap-1">
              <span className="text-base font-bold text-white tabular-nums">
                {formatPercent(d.close_rate * 100)}
              </span>
              <span className="text-xs text-gray-500 capitalize">{d.type}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
