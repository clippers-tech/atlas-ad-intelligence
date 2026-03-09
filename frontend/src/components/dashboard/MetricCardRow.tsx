"use client";

import { MetricCard } from "./MetricCard";
import {
  formatCurrency,
  formatNumber,
  formatRoas,
} from "@/lib/utils";
import type { DashboardOverview } from "@/lib/types";

interface MetricCardRowProps {
  data: DashboardOverview | undefined;
  isLoading: boolean;
}

function SkeletonCard() {
  return (
    <div className="bg-[#141414] border border-[#262626] rounded-xl p-4 animate-pulse">
      <div className="h-3 w-20 bg-[#262626] rounded mb-3" />
      <div className="h-7 w-24 bg-[#262626] rounded mb-2" />
      <div className="h-3 w-28 bg-[#262626] rounded" />
    </div>
  );
}

export function MetricCardRow({ data, isLoading }: MetricCardRowProps) {
  if (isLoading || !data) {
    return (
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
        {Array.from({ length: 6 }).map((_, i) => (
          <SkeletonCard key={i} />
        ))}
      </div>
    );
  }

  const spendChange = data.spend_vs_yesterday ?? 0;
  const leadsChange = data.leads_vs_yesterday ?? 0;

  // CPL derived change: if spend up and leads up, CPL change depends on ratio
  // Approximate: cpl change = spendChange - leadsChange
  const cplChange =
    leadsChange !== 0
      ? Number((((data.avg_cpl / (data.total_spend / data.total_leads || 1)) - 1) * 100).toFixed(1))
      : 0;

  const metrics = [
    {
      title: "Total Spend",
      value: formatCurrency(data.total_spend),
      comparison: `${data.paused_today} ads paused today`,
      changePercent: spendChange,
      inverse: false,
    },
    {
      title: "Leads",
      value: formatNumber(data.total_leads),
      comparison: `Avg CPL ${formatCurrency(data.avg_cpl)}`,
      changePercent: leadsChange,
      inverse: false,
    },
    {
      title: "CPL",
      value: formatCurrency(data.avg_cpl),
      comparison: "Cost per lead",
      changePercent: cplChange,
      inverse: true,
    },
    {
      title: "Bookings",
      value: formatNumber(data.total_bookings),
      comparison: `${data.campaigns.length} active campaigns`,
      changePercent: 0,
      inverse: false,
    },
    {
      title: "True ROAS",
      value: formatRoas(data.true_roas),
      comparison: "Revenue on ad spend",
      changePercent: 0,
      inverse: false,
    },
    {
      title: "Active Ads",
      value: formatNumber(data.active_ads),
      comparison: `${data.paused_today} paused today`,
      changePercent: 0,
      inverse: false,
    },
  ];

  return (
    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
      {metrics.map((metric) => (
        <MetricCard key={metric.title} {...metric} />
      ))}
    </div>
  );
}
