"use client";

import { useState, useMemo } from "react";
import { useQuery } from "@tanstack/react-query";
import { fetchData } from "@/lib/api";
import { useAccountContext } from "@/contexts/AccountContext";
import { useDateRange } from "@/contexts/DateRangeContext";
import { useStatusToggle } from "@/hooks/useStatusToggle";
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
  spend: number;
  leads: number;
  cpl: number;
  impressions: number;
  link_clicks: number;
  ctr_link: number;
}

type StatusFilter = "ALL" | "ACTIVE" | "PAUSED";
const FILTERS: { label: string; value: StatusFilter }[] = [
  { label: "All", value: "ALL" },
  { label: "Active", value: "ACTIVE" },
  { label: "Paused", value: "PAUSED" },
];

const HEADERS = [
  "Ad Set", "Campaign", "Status", "Budget",
  "Spend", "Leads", "CPL", "Impressions",
] as const;

export default function AdSetsPage() {
  const { currentAccount, isLoading: accountLoading } = useAccountContext();
  const { dateFrom, dateTo, rangeKey } = useDateRange();
  const [statusFilter, setStatusFilter] = useState<StatusFilter>("ALL");
  const { toggle, pendingId } = useStatusToggle(
    "ad-sets", ["adsets", "dashboard"],
  );

  const { data, isLoading } = useQuery({
    queryKey: ["adsets", currentAccount?.id, rangeKey],
    queryFn: () =>
      fetchData<{ data: AdSet[] }>("/ad-sets", {
        date_from: dateFrom,
        date_to: dateTo,
      }),
    enabled: !!currentAccount,
  });

  const adsets = data?.data ?? [];
  const filtered = useMemo(() => {
    const list = statusFilter === "ALL"
      ? adsets
      : adsets.filter((a) => a.status.toUpperCase() === statusFilter);
    return [...list].sort((a, b) => (b.spend ?? 0) - (a.spend ?? 0));
  }, [adsets, statusFilter]);

  if (accountLoading) return <PageLoader />;
  if (!currentAccount) {
    return (
      <EmptyState
        title="No account selected"
        description="Select an account to view ad sets."
      />
    );
  }
  if (isLoading) return <PageLoader />;

  return (
    <div className="flex flex-col gap-5">
      <PageHeader
        title="Ad Sets"
        subtitle={`${filtered.length} of ${adsets.length} ad sets · ${currentAccount.name}`}
      />
      <div className="flex items-center gap-2">
        {FILTERS.map((f) => (
          <button
            key={f.value}
            onClick={() => setStatusFilter(f.value)}
            className={`px-3.5 py-1.5 rounded-lg text-[13px] font-medium transition-colors ${
              statusFilter === f.value
                ? "bg-[var(--accent)] text-white"
                : "bg-[var(--surface-2)] text-[var(--muted)] hover:text-[var(--text)]"
            }`}
          >
            {f.label}
          </button>
        ))}
      </div>
      {filtered.length === 0 ? (
        <EmptyState
          title="No ad sets"
          description={
            statusFilter === "ALL"
              ? "No ad sets found for this account."
              : `No ${statusFilter.toLowerCase()} ad sets found.`
          }
        />
      ) : (
        <Card noPadding>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-[var(--border)]">
                  {HEADERS.map((h) => (
                    <th
                      key={h}
                      className="px-4 py-2.5 text-[11px] font-semibold text-[var(--muted)] uppercase tracking-wider text-left first:pl-5 last:pr-5"
                    >
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {filtered.map((a) => (
                  <tr
                    key={a.id}
                    className="border-b border-[var(--border)]/50 hover:bg-[var(--surface-2)] transition-colors"
                  >
                    <td className="px-4 py-3 pl-5">
                      <span className="text-[13px] font-medium text-[var(--text)]">
                        {a.name}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-[12px] text-[var(--text-secondary)]">
                      {a.campaign_name || "—"}
                    </td>
                    <td className="px-4 py-3">
                      <StatusBadge
                        label={a.status}
                        variant={getStatusVariant(a.status)}
                        dot
                        onClick={() => toggle(a.id, a.status)}
                        loading={pendingId === a.id}
                      />
                    </td>
                    <td className="px-4 py-3 text-[13px] tabular-nums text-[var(--text)]">
                      {a.daily_budget ? `${formatCurrency(a.daily_budget)}/d` : "—"}
                    </td>
                    <td className="px-4 py-3 text-[13px] tabular-nums text-[var(--text)]">
                      {formatCurrency(a.spend ?? 0)}
                    </td>
                    <td className="px-4 py-3 text-[13px] tabular-nums text-[var(--text)]">
                      {formatNumber(a.leads ?? 0)}
                    </td>
                    <td className="px-4 py-3 text-[13px] tabular-nums text-[var(--text)]">
                      {a.cpl ? formatCurrencyDecimal(a.cpl) : "—"}
                    </td>
                    <td className="px-4 py-3 pr-5 text-[13px] tabular-nums text-[var(--text)]">
                      {formatNumber(a.impressions ?? 0)}
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
