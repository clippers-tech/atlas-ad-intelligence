"use client";

import { useFunnel } from "@/hooks/useFunnel";
import { FunnelChart } from "@/components/dashboard/FunnelChart";
import { FunnelComparison } from "@/components/dashboard/FunnelComparison";
import { LoadingSpinner } from "@/components/common/LoadingSpinner";
import { EmptyState } from "@/components/common/EmptyState";
import { useDashboardOverview } from "@/hooks/useDashboardOverview";

export default function FunnelPage() {
  const { data: funnelData, isLoading, isError } = useFunnel();
  const { data: overviewData } = useDashboardOverview();

  if (isLoading) {
    return <LoadingSpinner fullHeight label="Loading funnel data..." />;
  }

  if (isError) {
    return (
      <EmptyState
        title="Failed to load funnel"
        description="There was an error fetching funnel data. Please try refreshing."
        icon="⚠️"
      />
    );
  }

  if (!funnelData || funnelData.stages.length === 0) {
    return (
      <div className="p-6">
        <div className="mb-6">
          <h1 className="text-xl font-bold text-white">Funnel</h1>
          <p className="text-sm text-gray-500 mt-0.5">
            Lead-to-close conversion funnel
          </p>
        </div>
        <EmptyState
          title="No funnel data"
          description="Funnel data will appear here once leads and deals are being tracked."
          icon="📐"
        />
      </div>
    );
  }

  // Build per-campaign funnel comparison from overview campaigns
  // We use the top 3 campaigns by spend to compare their funnel stages
  const topCampaigns = (overviewData?.campaigns ?? [])
    .sort((a, b) => b.spend - a.spend)
    .slice(0, 3);

  const comparisonCampaigns = topCampaigns.map((campaign) => ({
    name: campaign.name.length > 20
      ? campaign.name.slice(0, 20) + "…"
      : campaign.name,
    // Use the overall funnel stages as a proxy; in production each campaign has its own funnel
    funnel: funnelData.stages.map((stage) => ({
      ...stage,
      // Rough scaling by campaign spend ratio
      count: Math.round(
        stage.count *
          (campaign.spend /
            Math.max(
              overviewData?.total_spend ?? 1,
              1
            ))
      ),
    })),
  }));

  return (
    <div className="flex flex-col gap-6 p-6">
      {/* Page header */}
      <div>
        <h1 className="text-xl font-bold text-white">Funnel</h1>
        <p className="text-sm text-gray-500 mt-0.5">
          Lead-to-close conversion funnel · {funnelData.stages.length} stages
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Full funnel chart */}
        <FunnelChart data={funnelData} />

        {/* Campaign comparison */}
        {comparisonCampaigns.length > 1 && (
          <FunnelComparison campaigns={comparisonCampaigns} />
        )}
      </div>
    </div>
  );
}
