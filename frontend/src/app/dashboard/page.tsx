"use client";

import { useDashboardOverview } from "@/hooks/useDashboardOverview";
import { MetricCardRow } from "@/components/dashboard/MetricCardRow";
import { SpendLeadsChart } from "@/components/dashboard/SpendLeadsChart";
import { CampaignTable } from "@/components/dashboard/CampaignTable";
import { EmptyState } from "@/components/common/EmptyState";
import { useAccountContext } from "@/contexts/AccountContext";

export default function DashboardPage() {
  const { currentAccount } = useAccountContext();
  const { data, isLoading, isError } = useDashboardOverview();

  if (!currentAccount) {
    return (
      <EmptyState
        title="No account selected"
        description="Select an account from the header to view dashboard data."
        icon="📊"
      />
    );
  }

  if (isError) {
    return (
      <EmptyState
        title="Failed to load dashboard"
        description="There was an error fetching dashboard data. Please try refreshing."
        icon="⚠️"
      />
    );
  }

  const campaigns = data?.campaigns ?? [];
  const spendSeries = data?.spend_series ?? [];
  const leadsSeries = data?.leads_series ?? [];

  return (
    <div className="flex flex-col gap-6 p-6">
      {/* Page header */}
      <div>
        <h1 className="text-xl font-bold text-white">Overview</h1>
        <p className="text-sm text-gray-500 mt-0.5">
          {currentAccount.name} · Real-time performance
        </p>
      </div>

      {/* Metric cards */}
      <MetricCardRow data={data} isLoading={isLoading} />

      {/* Spend & Leads chart */}
      {(isLoading || spendSeries.length > 0) && (
        <div>
          {isLoading ? (
            <div className="bg-[#141414] border border-[#262626] rounded-xl h-72 animate-pulse" />
          ) : (
            <SpendLeadsChart
              spendSeries={spendSeries}
              leadsSeries={leadsSeries}
            />
          )}
        </div>
      )}

      {/* Campaign table */}
      {isLoading ? (
        <div className="bg-[#141414] border border-[#262626] rounded-xl h-48 animate-pulse" />
      ) : campaigns.length === 0 ? (
        <EmptyState
          title="No campaigns"
          description="No campaign data found for the current date range."
          icon="📋"
        />
      ) : (
        <CampaignTable
          campaigns={campaigns}
          targetCpl={currentAccount.target_cpl}
        />
      )}
    </div>
  );
}
