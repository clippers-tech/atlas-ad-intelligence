"use client";

import { MetricCard } from "@/components/common/MetricCard";
import { SkeletonCard } from "@/components/common/LoadingSpinner";
import type { DashboardOverview } from "@/lib/types";
import { formatCurrency, formatCurrencyDecimal, formatNumber, formatRoas } from "@/lib/utils";

interface MetricCardRowProps {
  data?: DashboardOverview;
  isLoading: boolean;
}

export function MetricCardRow({ data, isLoading }: MetricCardRowProps) {
  if (isLoading) {
    return (
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
        {Array.from({ length: 6 }).map((_, i) => (
          <SkeletonCard key={i} className="h-[100px]" />
        ))}
      </div>
    );
  }

  if (!data) return null;

  const cards = [
    { title: "Total Spend", value: formatCurrency(data.total_spend ?? 0) },
    { title: "Leads", value: formatNumber(data.total_leads ?? 0) },
    { title: "Avg CPL", value: formatCurrencyDecimal(data.avg_cpl ?? 0), inverse: true },
    { title: "Bookings", value: formatNumber(data.total_bookings ?? 0) },
    { title: "ROAS", value: formatRoas(data.true_roas ?? 0) },
    { title: "Active Ads", value: formatNumber(data.active_ads_count ?? 0) },
  ];

  return (
    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
      {cards.map((c) => (
        <MetricCard
          key={c.title}
          title={c.title}
          value={c.value}
          change={c.change}
          subtitle={c.subtitle}
          inverse={c.inverse}
        />
      ))}
    </div>
  );
}
