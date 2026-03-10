"use client";

import { useDashboardOverview } from "@/hooks/useDashboardOverview";
import { MetricCardRow } from "@/components/dashboard/MetricCardRow";
import { CampaignTable } from "@/components/dashboard/CampaignTable";
import { ActivityWidget } from "@/components/schedules/ActivityWidget";
import { EmptyState } from "@/components/common/EmptyState";
import { PageHeader } from "@/components/common/PageHeader";
import { PageLoader } from "@/components/common/LoadingSpinner";
import { useAccountContext } from "@/contexts/AccountContext";
import { useDateRange } from "@/contexts/DateRangeContext";

export default function DashboardPage() {
  const { currentAccount, isLoading: accountLoading } = useAccountContext();
  const { dateFrom, dateTo } = useDateRange();
  const { data, isLoading, isError } = useDashboardOverview(dateFrom, dateTo);

  if (accountLoading) return <PageLoader />;
  if (!currentAccount) {
    return (
      <EmptyState
        title="No account selected"
        description="Select an account from the header to view dashboard data."
      />
    );
  }

  if (isError) {
    return (
      <EmptyState
        title="Failed to load dashboard"
        description="Error fetching dashboard data. Check your connection and try refreshing."
      />
    );
  }

  if (isLoading && !data) return <PageLoader />;

  const campaigns = data?.campaigns ?? [];

  return (
    <div className="flex flex-col gap-5">
      <PageHeader
        title="Overview"
        subtitle={`${currentAccount.name} · Real-time performance`}
      />
      <MetricCardRow data={data} isLoading={isLoading} />
      {campaigns.length === 0 && !isLoading ? (
        <EmptyState
          title="No campaigns yet"
          description="Connect your Meta token to start pulling campaign data. Perplexity Computer will handle the rest."
        />
      ) : (
        <CampaignTable campaigns={campaigns} targetCpl={currentAccount.target_cpl} />
      )}
      <ActivityWidget />
    </div>
  );
}
