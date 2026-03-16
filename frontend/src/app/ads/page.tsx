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
import { StatusBadge, getStatusVariant } from "@/components/common/StatusBadge";
import { EmptyState } from "@/components/common/EmptyState";
import { PageLoader } from "@/components/common/LoadingSpinner";
import { formatCurrency, formatNumber, formatPercent } from "@/lib/utils";
import { ConversionTooltip } from "@/components/common/ConversionTooltip";
import type { Ad } from "@/lib/types";

type StatusFilter = "ALL" | "ACTIVE" | "PAUSED";
const FILTERS: { label: string; value: StatusFilter }[] = [
  { label: "All", value: "ALL" },
  { label: "Active", value: "ACTIVE" },
  { label: "Paused", value: "PAUSED" },
];

const SORT_OPTIONS: { label: string; key: string }[] = [
  { label: "Spend", key: "spend" },
  { label: "Results", key: "conversions" },
  { label: "Cost / Result", key: "cost_per_result" },
  { label: "Impressions", key: "impressions" },
  { label: "CTR", key: "ctr_link" },
  { label: "Clicks", key: "link_clicks" },
];

export default function AdsPage() {
  const { currentAccount, isLoading: accountLoading } = useAccountContext();
  const { dateFrom, dateTo, rangeKey } = useDateRange();
  const [statusFilter, setStatusFilter] = useState<StatusFilter>("ALL");
  const { toggle, pendingId } = useStatusToggle(
    "ads", ["ads", "dashboard"],
  );

  const { data, isLoading } = useQuery({
    queryKey: ["ads", currentAccount?.id, rangeKey],
    queryFn: () =>
      fetchData<{ data: Ad[] }>("/ads", {
        date_from: dateFrom,
        date_to: dateTo,
      }),
    enabled: !!currentAccount,
  });

  const ads = data?.data ?? [];
  const filtered = useMemo(() => {
    if (statusFilter === "ALL") return ads;
    return ads.filter((a) => a.status.toUpperCase() === statusFilter);
  }, [ads, statusFilter]);

  const { sorted, sort, toggle: toggleSort } = useTableSort(
    filtered, "spend", "desc"
  );

  if (accountLoading) return <PageLoader />;
  if (!currentAccount) {
    return (
      <EmptyState
        title="No account selected"
        description="Select an account to view ads."
      />
    );
  }
  if (isLoading) return <PageLoader />;

  return (
    <div className="flex flex-col gap-5">
      <PageHeader
        title="Ads"
        subtitle={`${filtered.length} of ${ads.length} ads · ${currentAccount.name}`}
      />
      <div className="flex items-center justify-between">
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

        {/* Sort dropdown for card grid */}
        <div className="flex items-center gap-2">
          <span className="text-[11px] text-[var(--muted)] uppercase tracking-wide">
            Sort by
          </span>
          <div className="flex gap-0.5 bg-[var(--surface-2)] rounded-lg p-0.5">
            {SORT_OPTIONS.map((opt) => (
              <button
                key={opt.key}
                onClick={() => toggleSort(opt.key)}
                className={`px-2.5 py-1 text-[11px] font-medium rounded-md transition-all duration-150 ${
                  sort.key === opt.key
                    ? "bg-amber-500/15 text-amber-400"
                    : "text-[var(--muted)] hover:text-[var(--text-secondary)]"
                }`}
              >
                {opt.label}
                {sort.key === opt.key && (
                  <span className="ml-0.5">
                    {sort.dir === "desc" ? "↓" : "↑"}
                  </span>
                )}
              </button>
            ))}
          </div>
        </div>
      </div>
      {filtered.length === 0 ? (
        <EmptyState
          title="No ads"
          description={
            statusFilter === "ALL"
              ? "No ads found. Ads will appear after Meta sync."
              : `No ${statusFilter.toLowerCase()} ads found.`
          }
        />
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {sorted.map((ad) => (
            <AdCard
              key={ad.id}
              ad={ad}
              onToggle={() => toggle(ad.id, ad.status)}
              isPending={pendingId === ad.id}
            />
          ))}
        </div>
      )}
    </div>
  );
}

function AdCard({
  ad, onToggle, isPending,
}: {
  ad: Ad;
  onToggle: () => void;
  isPending: boolean;
}) {
  return (
    <Card className="hover:border-[var(--border-light)] transition-colors">
      {ad.thumbnail_url ? (
        <div className="w-full h-40 rounded-lg bg-[var(--surface-2)] mb-3 overflow-hidden">
          <img
            src={ad.thumbnail_url}
            alt={ad.name}
            className="w-full h-full object-cover"
          />
        </div>
      ) : (
        <div className="w-full h-40 rounded-lg bg-[var(--surface-2)] mb-3 flex items-center justify-center">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="var(--muted)" strokeWidth="1.5">
            <rect x="3" y="3" width="18" height="18" rx="2" />
            <circle cx="8.5" cy="8.5" r="1.5" />
            <path d="M21 15l-5-5L5 21" />
          </svg>
        </div>
      )}
      <h4 className="text-[13px] font-medium text-[var(--text)] truncate">
        {ad.name}
      </h4>
      {ad.adset_name && (
        <p className="text-[11px] text-[var(--text-secondary)] truncate mt-0.5">
          {ad.adset_name}
        </p>
      )}
      <div className="flex items-center gap-2 mt-2">
        <StatusBadge
          label={ad.status}
          variant={getStatusVariant(ad.status)}
          dot
          onClick={onToggle}
          loading={isPending}
        />
        <span className="text-[11px] text-[var(--muted)]">{ad.ad_type}</span>
      </div>
      <div className="grid grid-cols-3 gap-3 mt-3 pt-3 border-t border-[var(--border)]/50">
        <Stat label="Spend" value={formatCurrency(ad.spend ?? 0)} />
        <div>
          <p className="text-[10px] text-[var(--muted)] uppercase tracking-wide">Results</p>
          <ConversionTooltip
            result={ad.conversions ?? 0}
            breakdown={ad.conversion_breakdown}
          />
        </div>
        <Stat label="Cost / Result" value={ad.cost_per_result ? formatCurrency(ad.cost_per_result) : "—"} />
        <Stat label="Impr." value={formatNumber(ad.impressions ?? 0)} />
        <Stat label="CTR" value={formatPercent(ad.ctr_link ?? 0)} />
        <Stat label="Clicks" value={formatNumber(ad.link_clicks ?? 0)} />
      </div>
    </Card>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <p className="text-[10px] text-[var(--muted)] uppercase tracking-wide">{label}</p>
      <p className="text-[13px] font-medium text-[var(--text)] tabular-nums">{value}</p>
    </div>
  );
}
