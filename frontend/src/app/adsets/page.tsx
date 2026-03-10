"use client";

import { useQuery } from "@tanstack/react-query";
import { fetchData } from "@/lib/api";
import { useAccountContext } from "@/contexts/AccountContext";
import { PageHeader } from "@/components/common/PageHeader";
import { Card } from "@/components/common/Card";
import { StatusBadge, getStatusVariant } from "@/components/common/StatusBadge";
import { EmptyState } from "@/components/common/EmptyState";
import { PageLoader } from "@/components/common/LoadingSpinner";
import { formatCurrency, formatCurrencyDecimal, formatNumber } from "@/lib/utils";

interface AdSet {
  id: string;
  name: string;
  status: string;
  campaign_name?: string;
  daily_budget?: number;
  targeting_summary?: string;
  spend?: number;
  leads?: number;
  cpl?: number;
  impressions?: number;
}

export default function AdSetsPage() {
  const { currentAccount, isLoading: accountLoading } = useAccountContext();

  const { data, isLoading } = useQuery({
    queryKey: ["adsets", currentAccount?.id],
    queryFn: () => fetchData<{ data: AdSet[] }>("/ad-sets"),
    enabled: !!currentAccount,
  });

  if (accountLoading) return <PageLoader />;
  if (!currentAccount) {
    return <EmptyState title="No account selected" description="Select an account to view ad sets." />;
  }

  if (isLoading) return <PageLoader />;
  const adsets = data?.data ?? [];

  return (
    <div className="flex flex-col gap-5">
      <PageHeader title="Ad Sets" subtitle={`${adsets.length} ad sets · ${currentAccount.name}`} />
      {adsets.length === 0 ? (
        <EmptyState title="No ad sets" description="No ad sets found for this account. Ad sets will appear once campaigns are synced from Meta." />
      ) : (
        <Card noPadding>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-[var(--border)]">
                  {["Ad Set", "Campaign", "Status", "Budget", "Spend", "Leads", "CPL", "Impressions"].map((h) => (
                    <th key={h} className="px-4 py-2.5 text-[11px] font-semibold text-[var(--muted)] uppercase tracking-wider text-left first:pl-5 last:pr-5">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {adsets.map((a) => (
                  <tr key={a.id} className="border-b border-[var(--border)]/50 hover:bg-[var(--surface-2)] transition-colors">
                    <td className="px-4 py-3 pl-5">
                      <span className="text-[13px] font-medium text-[var(--text)]">{a.name}</span>
                    </td>
                    <td className="px-4 py-3 text-[12px] text-[var(--text-secondary)]">{a.campaign_name || "—"}</td>
                    <td className="px-4 py-3"><StatusBadge label={a.status} variant={getStatusVariant(a.status)} dot /></td>
                    <td className="px-4 py-3 text-[13px] tabular-nums text-[var(--text)]">{a.daily_budget ? `${formatCurrency(a.daily_budget)}/d` : "—"}</td>
                    <td className="px-4 py-3 text-[13px] tabular-nums text-[var(--text)]">{a.spend !== undefined ? formatCurrency(a.spend) : "—"}</td>
                    <td className="px-4 py-3 text-[13px] tabular-nums text-[var(--text)]">{a.leads !== undefined ? formatNumber(a.leads) : "—"}</td>
                    <td className="px-4 py-3 text-[13px] tabular-nums text-[var(--text)]">{a.cpl !== undefined ? formatCurrencyDecimal(a.cpl) : "—"}</td>
                    <td className="px-4 py-3 pr-5 text-[13px] tabular-nums text-[var(--text)]">{a.impressions !== undefined ? formatNumber(a.impressions) : "—"}</td>
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
