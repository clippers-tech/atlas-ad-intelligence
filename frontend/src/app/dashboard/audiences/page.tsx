"use client";

import { useAudiences } from "@/hooks/useAudiences";
import { AudienceTable } from "@/components/audiences/AudienceTable";
import { AudienceHeatmap } from "@/components/audiences/AudienceHeatmap";
import { TypeComparison } from "@/components/audiences/TypeComparison";
import { TestQueueList } from "@/components/audiences/TestQueueList";
import { SaturationAlert } from "@/components/audiences/SaturationAlert";
import { LoadingSpinner } from "@/components/common/LoadingSpinner";
import { EmptyState } from "@/components/common/EmptyState";

// Type shapes for the API response sub-fields
interface HeatmapData {
  audienceLabels: string[];
  creativeLabels: string[];
  values: number[][];
}

interface TypeComparisonItem {
  type: string;
  avg_cpl: number;
  close_rate: number;
}

interface TestEntry {
  id: string;
  name: string;
  audience_type: string;
  status: "queued" | "active" | "killed" | "graduated";
  created_at: string;
  notes?: string;
}

interface SaturationItem {
  audience: string;
  frequency: number;
  level: string;
}

export default function AudiencesPage() {
  const { data, isLoading, isError } = useAudiences();

  if (isLoading) {
    return <LoadingSpinner fullHeight label="Loading audience data..." />;
  }

  if (isError) {
    return (
      <EmptyState
        title="Failed to load audiences"
        description="There was an error fetching audience performance data."
        icon="⚠️"
      />
    );
  }

  const audiences = data?.audiences ?? [];
  const heatmapData = (data?.heatmap_data as HeatmapData | null) ?? {
    audienceLabels: [],
    creativeLabels: [],
    values: [],
  };
  const typeComparison = (data?.type_comparison as TypeComparisonItem[] | null) ?? [];
  const testQueue = (data?.test_queue as TestEntry[] | null) ?? [];
  const alerts = (data?.alerts as SaturationItem[] | null) ?? [];

  return (
    <div className="flex flex-col gap-6 p-6">
      {/* Page header */}
      <div>
        <h1 className="text-xl font-bold text-white">Audiences</h1>
        <p className="text-sm text-gray-500 mt-0.5">
          {audiences.length} audiences · performance and test queue
        </p>
      </div>

      {/* Saturation alerts at top */}
      {alerts.length > 0 && <SaturationAlert alerts={alerts} />}

      {/* Audience performance table */}
      {audiences.length === 0 ? (
        <EmptyState
          title="No audience data"
          description="Audience performance data will appear here once campaigns are active."
          icon="👥"
        />
      ) : (
        <AudienceTable audiences={audiences} />
      )}

      {/* Two columns: heatmap + type comparison */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <AudienceHeatmap data={heatmapData} />
        <TypeComparison data={typeComparison} />
      </div>

      {/* Test queue */}
      <TestQueueList tests={testQueue} />
    </div>
  );
}
