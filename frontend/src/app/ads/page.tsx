"use client";

import { useQuery } from "@tanstack/react-query";
import { fetchData } from "@/lib/api";
import { useAccountContext } from "@/contexts/AccountContext";
import { PageHeader } from "@/components/common/PageHeader";
import { Card } from "@/components/common/Card";
import { StatusBadge, getStatusVariant } from "@/components/common/StatusBadge";
import { EmptyState } from "@/components/common/EmptyState";
import { PageLoader } from "@/components/common/LoadingSpinner";
import type { Ad } from "@/lib/types";

export default function AdsPage() {
  const { currentAccount } = useAccountContext();

  const { data, isLoading } = useQuery({
    queryKey: ["ads", currentAccount?.id],
    queryFn: () => fetchData<{ data: Ad[] }>("/ads"),
    enabled: !!currentAccount,
  });

  if (!currentAccount) {
    return <EmptyState title="No account selected" description="Select an account to view ads." />;
  }

  if (isLoading) return <PageLoader />;
  const ads = data?.data ?? [];

  return (
    <div className="flex flex-col gap-5">
      <PageHeader title="Ads" subtitle={`${ads.length} ads · ${currentAccount.name}`} />
      {ads.length === 0 ? (
        <EmptyState title="No ads" description="No ads found. Ads will appear after Meta sync." />
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {ads.map((ad) => (
            <Card key={ad.id} className="hover:border-[var(--border-light)] transition-colors">
              {/* Thumbnail */}
              {ad.thumbnail_url ? (
                <div className="w-full h-40 rounded-lg bg-[var(--surface-2)] mb-3 overflow-hidden">
                  <img src={ad.thumbnail_url} alt={ad.name}
                    className="w-full h-full object-cover" />
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
              <h4 className="text-[13px] font-medium text-[var(--text)] truncate">{ad.name}</h4>
              <div className="flex items-center gap-2 mt-2">
                <StatusBadge label={ad.status} variant={getStatusVariant(ad.status)} dot />
                <span className="text-[11px] text-[var(--muted)]">{ad.ad_type}</span>
              </div>
              <p className="text-[11px] text-[var(--muted)] mt-1.5">
                ID: {ad.meta_ad_id}
              </p>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
