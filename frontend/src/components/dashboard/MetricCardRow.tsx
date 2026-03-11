"use client";

import { MetricCard } from "@/components/common/MetricCard";
import { SkeletonCard } from "@/components/common/LoadingSpinner";
import type { DashboardOverview } from "@/lib/types";
import {
  formatCurrency,
  formatCurrencyDecimal,
  formatNumber,
  formatPercent,
} from "@/lib/utils";

interface MetricCardRowProps {
  data?: DashboardOverview;
  isLoading: boolean;
}

export function MetricCardRow({ data, isLoading }: MetricCardRowProps) {
  if (isLoading) {
    return (
      <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-8 gap-3">
        {Array.from({ length: 8 }).map((_, i) => (
          <SkeletonCard key={i} className="h-[100px]" />
        ))}
      </div>
    );
  }

  if (!data) return null;

  const cards = [
    { title: "Spend", value: formatCurrency(data.total_spend ?? 0) },
    { title: "Impressions", value: formatNumber(data.total_impressions ?? 0) },
    { title: "Reach", value: formatNumber(data.total_reach ?? 0) },
    { title: "Link Clicks", value: formatNumber(data.total_link_clicks ?? 0) },
    { title: "CPM", value: formatCurrencyDecimal(data.avg_cpm ?? 0), inverse: true },
    { title: "CTR (Link)", value: formatPercent(data.ctr_link ?? 0) },
    { title: "CPC (Link)", value: formatCurrencyDecimal(data.avg_cpc_link ?? 0), inverse: true },
    { title: "LPV", value: formatNumber(data.total_landing_page_views ?? 0) },
  ];

  return (
    <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-8 gap-3">
      {cards.map((c) => (
        <MetricCard
          key={c.title}
          title={c.title}
          value={c.value}
          inverse={c.inverse}
        />
      ))}
    </div>
  );
}
