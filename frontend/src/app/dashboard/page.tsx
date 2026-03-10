"use client";

import { useDashboardOverview } from "@/hooks/useDashboardOverview";
import { MetricCardRow } from "@/components/dashboard/MetricCardRow";
import { SpendLeadsChart } from "@/components/dashboard/SpendLeadsChart";
import { CampaignTable } from "@/components/dashboard/CampaignTable";
import { EmptyState } from "@/components/common/EmptyState";
import { PageHeader } from "@/components/common/PageHeader";
import { PageLoader } from "@/components/common/LoadingSpinner";
import { useAccountContext } from "@/contexts/AccountContext";

export default function DashboardPage() {
  const { currentAccount } = useAccountContext();
  const { data, isLoading, isError } = useDashboardOverview();

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
  const spendSeries = data?.spend_series ?? [];
  const leadsSeries = data?.leads_series ?? [];

  return (
    <div className="flex flex-col gap-5">
      <PageHeader
        title="Overview"
        subtitle={`${currentAccount.name} · Real-time performance`}
      />
      <MetricCardRow data={data} isLoading={isLoading} />
      {spendSeries.length > 0 && (
        <SpendLeadsChart spendSeries={spendSeries} leadsSeries={leadsSeries} />
      )}
      {campaigns.length === 0 && !isLoading ? (
        <EmptyState
          title="No campaigns"
          description="No campaign data found for the current date range."
        />
      ) : (
        <CampaignTable campaigns={campaigns} targetCpl={currentAccount.target_cpl} />
      )}
    </div>
  );
}
