"use client";

import { useState, useMemo } from "react";
import { useQuery } from "@tanstack/react-query";
import { fetchData } from "@/lib/api";
import { useAccountContext } from "@/contexts/AccountContext";
import { useDateRange } from "@/contexts/DateRangeContext";
import { useStatusToggle } from "@/hooks/useStatusToggle";
import { useTableSort } from "@/hooks/useTableSort";
import { PageHeader } from "@/components/common/PageHeader";
import { Card } from "@/components/common/Card";
import { SortableHeader } from "@/components/common/SortableHeader";
import { StatusBadge, getStatusVariant } from "@/components/common/StatusBadge";
import { EmptyState } from "@/components/common/EmptyState";
import { PageLoader } from "@/components/common/LoadingSpinner";
import {
  formatCurrency,
  formatCurrencyDecimal,
  formatNumber,
  formatPercent,
} from "@/lib/utils";
import type { Campaign } from "@/lib/types";

type StatusFilter = "ALL" | "ACTIVE" | "PAUSED";
const FILTERS: { label: string; value: StatusFilter }[] = [
  { label: "All", value: "ALL" },
  { label: "Active", value: "ACTIVE" },
  { label: "Paused", value: "PAUSED" },
];

const COLUMNS: { label: string; key: string }[] = [
  { label: "Campaign", key: "name" },
  { label: "Status", key: "status" },
  { label: "Spend", key: "spend" },
  { label: "Impressions", key: "impressions" },
  { label: "Reach", key: "reach" },
  { label: "CPM", key: "cpm" },
  { label: "Link Clicks", key: "link_clicks" },
  { label: "CPC (Link)", key: "cpc_link" },
  { label: "CTR (Link)", key: "ctr_link" },
  { label: "Clicks (All)", key: "clicks_all" },
  { label: "LPV", key: "landing_page_views" },
  { label: "Cost / LPV", key: "cost_per_lpv" },
  { label: "Results", key: "leads" },
  { label: "CPL", key: "cpl" },
];

export default function CampaignsPage() {
  const { currentAccount, isLoading: accountLoading } = useAccountContext();
  const { dateFrom, dateTo, rangeKey } = useDateRange();
  const [statusFilter, setStatusFilter] = useState<StatusFilter>("ALL");
  const { toggle, pendingId } = useStatusToggle(
    "campaigns", ["campaigns", "dashboard"],
  );

  const { data, isLoading } = useQuery({
    queryKey: ["campaigns", currentAccount?.id, rangeKey],
    queryFn: () =>
      fetchData<{ data: Campaign[] }>("/campaigns", {
        date_from: dateFrom,
        date_to: dateTo,
      }),
    enabled: !!currentAccount,
  });

  const campaigns = data?.data ?? [];
  const filtered = useMemo(() => {
    if (statusFilter === "ALL") return campaigns;
    return campaigns.filter(
      (c) => c.status.toUpperCase() === statusFilter
    );
  }, [campaigns, statusFilter]);

  const { sorted, sort, toggle: toggleSort } = useTableSort(
    filtered, "spend", "desc"
  );

  if (accountLoading) return <PageLoader />;
  if (!currentAccount) {
    return (
      <EmptyState
        title="No account selected"
        description="Select an account to view campaigns."
      />
    );
  }
  if (isLoading) return <PageLoader />;

  return (
    <div className="flex flex-col gap-5">
      <PageHeader
        title="Campaigns"
        subtitle={`${filtered.length} of ${campaigns.length} campaigns · ${currentAccount.name}`}
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
          title="No campaigns"
          description={
            statusFilter === "ALL"
              ? "No campaigns found for this account."
              : `No ${statusFilter.toLowerCase()} campaigns found.`
          }
        />
      ) : (
        <Card noPadding>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-[var(--border)]">
                  {COLUMNS.map((col, i) => (
                    <SortableHeader
                      key={col.key}
                      label={col.label}
                      sortKey={col.key}
                      activeKey={sort.key}
                      activeDir={sort.dir}
                      onSort={toggleSort}
                      className={
                        i === 0 ? "pl-5" : i === COLUMNS.length - 1 ? "pr-5" : ""
                      }
                    />
                  ))}
                </tr>
              </thead>
              <tbody>
                {sorted.map((c) => (
                  <CampaignRow
                    key={c.id}
                    c={c}
                    onToggle={() => toggle(c.id, c.status)}
                    isPending={pendingId === c.id}
                  />
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      )}
    </div>
  );
}

function CampaignRow({
  c, onToggle, isPending,
}: {
  c: Campaign;
  onToggle: () => void;
  isPending: boolean;
}) {
  const cell =
    "px-3 py-3 text-[13px] tabular-nums text-[var(--text)] whitespace-nowrap";
  return (
    <tr className="border-b border-[var(--border)]/50 hover:bg-[var(--surface-2)] transition-colors">
      <td className="px-3 py-3 pl-5 min-w-[200px]">
        <span className="text-[13px] font-medium text-[var(--text)] line-clamp-1">
          {c.name}
        </span>
        <p className="text-[11px] text-[var(--muted)] mt-0.5">
          {c.objective || "—"}
        </p>
      </td>
      <td className="px-3 py-3">
        <StatusBadge
          label={c.status}
          variant={getStatusVariant(c.status)}
          dot
          onClick={onToggle}
          loading={isPending}
        />
      </td>
      <td className={cell}>{val(c.spend, formatCurrency)}</td>
      <td className={cell}>{val(c.impressions, formatNumber)}</td>
      <td className={cell}>{val(c.reach, formatNumber)}</td>
      <td className={cell}>{val(c.cpm, formatCurrencyDecimal)}</td>
      <td className={cell}>{val(c.link_clicks, formatNumber)}</td>
      <td className={cell}>{val(c.cpc_link, formatCurrencyDecimal)}</td>
      <td className={cell}>{val(c.ctr_link, formatPercent)}</td>
      <td className={cell}>{val(c.clicks_all, formatNumber)}</td>
      <td className={cell}>{val(c.landing_page_views, formatNumber)}</td>
      <td className={cell}>{val(c.cost_per_lpv, formatCurrencyDecimal)}</td>
      <td className={cell}>{val(c.leads, formatNumber)}</td>
      <td className="px-3 py-3 pr-5 text-[13px] tabular-nums text-[var(--text)] whitespace-nowrap">
        {val(c.cpl, formatCurrencyDecimal)}
      </td>
    </tr>
  );
}

/** Render a metric value or "—" if zero/undefined. */
function val(
  v: number | undefined,
  fmt: (n: number) => string
): string {
  if (v === undefined || v === null) return "—";
  if (v === 0) return "—";
  return fmt(v);
}
