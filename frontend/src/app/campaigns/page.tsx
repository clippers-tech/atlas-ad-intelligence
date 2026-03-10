"use client";

import { useQuery } from "@tanstack/react-query";
import { fetchData } from "@/lib/api";
import { useAccountContext } from "@/contexts/AccountContext";
import { PageHeader } from "@/components/common/PageHeader";
import { Card } from "@/components/common/Card";
import { StatusBadge, getStatusVariant } from "@/components/common/StatusBadge";
import { EmptyState } from "@/components/common/EmptyState";
import { PageLoader } from "@/components/common/LoadingSpinner";
import { formatCurrency, formatCurrencyDecimal, formatNumber, formatRoas } from "@/lib/utils";
import type { Campaign } from "@/lib/types";

export default function CampaignsPage() {
  const { currentAccount } = useAccountContext();

  const { data, isLoading } = useQuery({
    queryKey: ["campaigns", currentAccount?.id],
    queryFn: () => fetchData<{ data: Campaign[] }>("/campaigns"),
    enabled: !!currentAccount,
  });

  if (!currentAccount) {
    return <EmptyState title="No account selected" description="Select an account to view campaigns." />;
  }

  if (isLoading) return <PageLoader />;
  const campaigns = data?.data ?? [];

  return (
    <div className="flex flex-col gap-5">
      <PageHeader title="Campaigns" subtitle={`${campaigns.length} campaigns · ${currentAccount.name}`} />
      {campaigns.length === 0 ? (
        <EmptyState title="No campaigns" description="No campaigns found for this account." />
      ) : (
        <Card noPadding>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-[var(--border)]">
                  {["Campaign", "Objective", "Status", "Budget", "Spend", "Leads", "CPL", "ROAS"].map((h) => (
                    <th key={h} className="px-4 py-2.5 text-[11px] font-semibold text-[var(--muted)] uppercase tracking-wider text-left first:pl-5 last:pr-5">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {campaigns.map((c) => (
                  <tr key={c.id} className="border-b border-[var(--border)]/50 hover:bg-[var(--surface-2)] transition-colors">
                    <td className="px-4 py-3 pl-5">
                      <span className="text-[13px] font-medium text-[var(--text)]">{c.name}</span>
                      <p className="text-[11px] text-[var(--muted)] mt-0.5">ID: {c.meta_campaign_id}</p>
                    </td>
                    <td className="px-4 py-3 text-[12px] text-[var(--text-secondary)]">{c.objective || "—"}</td>
                    <td className="px-4 py-3"><StatusBadge label={c.status} variant={getStatusVariant(c.status)} dot /></td>
                    <td className="px-4 py-3 text-[13px] tabular-nums text-[var(--text)]">
                      {c.daily_budget ? `${formatCurrency(c.daily_budget)}/d` : c.lifetime_budget ? formatCurrency(c.lifetime_budget) : "—"}
                    </td>
                    <td className="px-4 py-3 text-[13px] tabular-nums text-[var(--text)]">{c.spend !== undefined ? formatCurrency(c.spend) : "—"}</td>
                    <td className="px-4 py-3 text-[13px] tabular-nums text-[var(--text)]">{c.leads !== undefined ? formatNumber(c.leads) : "—"}</td>
                    <td className="px-4 py-3 text-[13px] tabular-nums text-[var(--text)]">{c.cpl !== undefined ? formatCurrencyDecimal(c.cpl) : "—"}</td>
                    <td className="px-4 py-3 pr-5 text-[13px] tabular-nums text-[var(--text)]">{c.roas !== undefined ? formatRoas(c.roas) : "—"}</td>
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
