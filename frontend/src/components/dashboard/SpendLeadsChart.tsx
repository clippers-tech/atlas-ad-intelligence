"use client";

import { AreaChart } from "@tremor/react";
import { Card } from "@/components/common/Card";
import type { TimeSeriesPoint } from "@/lib/types";

interface SpendLeadsChartProps {
  spendSeries: TimeSeriesPoint[];
  leadsSeries: TimeSeriesPoint[];
}

export function SpendLeadsChart({ spendSeries, leadsSeries }: SpendLeadsChartProps) {
  const merged = spendSeries.map((s, i) => ({
    date: s.date,
    Spend: s.value,
    Leads: leadsSeries[i]?.value ?? 0,
  }));

  return (
    <Card title="Spend & Leads" subtitle="Daily trend">
      <AreaChart
        className="h-64"
        data={merged}
        index="date"
        categories={["Spend", "Leads"]}
        colors={["amber", "emerald"]}
        valueFormatter={(val: number) => `$${val.toLocaleString()}`}
        showAnimation
        showLegend
        showGridLines={false}
        curveType="monotone"
      />
    </Card>
  );
}
