"use client";

import { useQuery } from "@tanstack/react-query";
import { fetchData } from "@/lib/api";
import { useAccountContext } from "@/contexts/AccountContext";
import { PageHeader } from "@/components/common/PageHeader";
import { Card } from "@/components/common/Card";
import { StatusBadge } from "@/components/common/StatusBadge";
import { EmptyState } from "@/components/common/EmptyState";
import { PageLoader } from "@/components/common/LoadingSpinner";
import { formatCurrency, formatNumber, formatPercent } from "@/lib/utils";
import type { CreativePerformance } from "@/lib/types";

export default function CreativesPage() {
  const { currentAccount } = useAccountContext();

  const { data, isLoading } = useQuery({
    queryKey: ["creatives", currentAccount?.id],
    queryFn: () => fetchData<{ data: CreativePerformance[] }>("/creatives/performance"),
    enabled: !!currentAccount,
  });

  if (!currentAccount) {
    return <EmptyState title="No account selected" description="Select an account to view creatives." />;
  }

  if (isLoading) return <PageLoader />;
  const creatives = data?.data ?? [];

  const fatigueColor = (level: string) => {
    if (level === "fresh") return "success";
    if (level === "declining") return "warning";
    return "danger";
  };

  return (
    <div className="flex flex-col gap-5">
      <PageHeader title="Creatives" subtitle={`Creative performance · ${currentAccount.name}`} />
      {creatives.length === 0 ? (
        <EmptyState title="No creatives" description="Creative data will appear after Meta sync." />
      ) : (
        <Card noPadding>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-[var(--border)]">
                  {["Creative", "Type", "Spend", "Impressions", "CTR", "Conversions", "Fatigue"].map((h) => (
                    <th key={h} className="px-4 py-2.5 text-[11px] font-semibold text-[var(--muted)] uppercase tracking-wider text-left first:pl-5 last:pr-5">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {creatives.map((c) => (
                  <tr key={c.ad_id} className="border-b border-[var(--border)]/50 hover:bg-[var(--surface-2)] transition-colors">
                    <td className="px-4 py-3 pl-5">
                      <div className="flex items-center gap-3">
                        {c.thumbnail_url ? (
                          <img src={c.thumbnail_url} alt="" className="w-10 h-10 rounded-lg object-cover" />
                        ) : (
                          <div className="w-10 h-10 rounded-lg bg-[var(--surface-2)]" />
                        )}
                        <span className="text-[13px] font-medium text-[var(--text)] max-w-[200px] truncate">{c.ad_name}</span>
                      </div>
                    </td>
                    <td className="px-4 py-3 text-[12px] text-[var(--text-secondary)]">{c.ad_type || "—"}</td>
                    <td className="px-4 py-3 text-[13px] tabular-nums text-[var(--text)]">{formatCurrency(c.spend)}</td>
                    <td className="px-4 py-3 text-[13px] tabular-nums text-[var(--text)]">{formatNumber(c.impressions)}</td>
                    <td className="px-4 py-3 text-[13px] tabular-nums text-[var(--text)]">{formatPercent(c.ctr)}</td>
                    <td className="px-4 py-3 text-[13px] tabular-nums text-[var(--text)]">{formatNumber(c.conversions)}</td>
                    <td className="px-4 py-3 pr-5">
                      <StatusBadge label={c.fatigue_level || "Unknown"} variant={fatigueColor(c.fatigue_level || "")} dot />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      )}
    </div>
  );
}
