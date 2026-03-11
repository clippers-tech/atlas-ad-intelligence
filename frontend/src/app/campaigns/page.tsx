"use client";

import { useQuery } from "@tanstack/react-query";
import { fetchData } from "@/lib/api";
import { useAccountContext } from "@/contexts/AccountContext";
import { PageHeader } from "@/components/common/PageHeader";
import { Card } from "@/components/common/Card";
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

const COLUMNS = [
  "Campaign",
  "Status",
  "Spend",
  "Impressions",
  "Reach",
  "CPM",
  "Link Clicks",
  "CPC (Link)",
  "CTR (Link)",
  "Clicks (All)",
  "LPV",
  "Cost / LPV",
  "Results",
  "CPL",
] as const;

export default function CampaignsPage() {
  const { currentAccount, isLoading: accountLoading } = useAccountContext();

  const { data, isLoading } = useQuery({
    queryKey: ["campaigns", currentAccount?.id],
    queryFn: () => fetchData<{ data: Campaign[] }>("/campaigns"),
    enabled: !!currentAccount,
  });

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
  const campaigns = data?.data ?? [];

  return (
    <div className="flex flex-col gap-5">
      <PageHeader
        title="Campaigns"
        subtitle={`${campaigns.length} campaigns · ${currentAccount.name}`}
      />
      {campaigns.length === 0 ? (
        <EmptyState
          title="No campaigns"
          description="No campaigns found for this account."
        />
      ) : (
        <Card noPadding>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-[var(--border)]">
                  {COLUMNS.map((h) => (
                    <th
                      key={h}
                      className="px-3 py-2.5 text-[11px] font-semibold text-[var(--muted)] uppercase tracking-wider text-left first:pl-5 last:pr-5 whitespace-nowrap"
                    >
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {campaigns.map((c) => (
                  <CampaignRow key={c.id} c={c} />
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      )}
    </div>
  );
}

function CampaignRow({ c }: { c: Campaign }) {
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
