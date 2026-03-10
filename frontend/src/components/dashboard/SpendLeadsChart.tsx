"use client";

import { AreaChart } from "@tremor/react";
import type { TimeSeriesPoint } from "@/lib/types";

interface SpendLeadsChartProps {
  spendSeries: TimeSeriesPoint[];
  leadsSeries: TimeSeriesPoint[];
}

function formatSpend(value: number): string {
  if (value >= 1000) return `£${(value / 1000).toFixed(1)}k`;
  return `£${value.toFixed(0)}`;
}

export function SpendLeadsChart({
  spendSeries,
  leadsSeries,
}: SpendLeadsChartProps) {
  // Merge the two series into a single array for Tremor
  const data = spendSeries.map((point, i) => ({
    date: point.date,
    Spend: point.value,
    Leads: leadsSeries[i]?.value ?? 0,
  }));

  if (data.length === 0) {
    return (
      <div className="bg-[#141414] border border-[#262626] rounded-xl p-6 flex items-center justify-center h-64">
        <p className="text-gray-500 text-sm">No chart data available</p>
      </div>
    );
  }

  return (
    <div className="bg-[#141414] border border-[#262626] rounded-xl p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-semibold text-white">Spend & Leads</h3>
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-1.5">
            <span className="w-3 h-3 rounded-full bg-blue-500 inline-block" />
            <span className="text-xs text-gray-400">Spend</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="w-3 h-3 rounded-full bg-emerald-500 inline-block" />
            <span className="text-xs text-gray-400">Leads</span>
          </div>
        </div>
      </div>
      <AreaChart
        data={data}
        index="date"
        categories={["Spend", "Leads"]}
        colors={["blue", "emerald"]}
        valueFormatter={formatSpend}
        className="h-56 mt-2"
        showLegend={false}
        showGridLines={false}
        showAnimation
        curveType="monotone"
      />
    </div>
  );
}
