"use client";

import { useAnomalies } from "@/hooks/useAnomalies";
import { AnomalyTimeline } from "@/components/dashboard/AnomalyTimeline";
import { LoadingSpinner } from "@/components/common/LoadingSpinner";
import { EmptyState } from "@/components/common/EmptyState";

function SeveritySummary({
  anomalies,
}: {
  anomalies: { severity: string }[];
}) {
  const high = anomalies.filter((a) => a.severity === "high").length;
  const medium = anomalies.filter((a) => a.severity === "medium").length;
  const low = anomalies.filter((a) => a.severity === "low").length;

  return (
    <div className="flex items-center gap-4">
      {high > 0 && (
        <div className="flex items-center gap-1.5">
          <span className="w-2 h-2 rounded-full bg-red-500 inline-block" />
          <span className="text-xs text-gray-400">
            {high} high
          </span>
        </div>
      )}
      {medium > 0 && (
        <div className="flex items-center gap-1.5">
          <span className="w-2 h-2 rounded-full bg-amber-400 inline-block" />
          <span className="text-xs text-gray-400">
            {medium} medium
          </span>
        </div>
      )}
      {low > 0 && (
        <div className="flex items-center gap-1.5">
          <span className="w-2 h-2 rounded-full bg-gray-500 inline-block" />
          <span className="text-xs text-gray-400">
            {low} low
          </span>
        </div>
      )}
    </div>
  );
}

export default function AnomaliesPage() {
  const { data: anomalies, isLoading, isError } = useAnomalies();

  if (isLoading) {
    return <LoadingSpinner fullHeight label="Loading anomaly data..." />;
  }

  if (isError) {
    return (
      <EmptyState
        title="Failed to load anomalies"
        description="There was an error fetching anomaly data. Please try refreshing."
        icon="⚠️"
      />
    );
  }

  if (!anomalies || anomalies.length === 0) {
    return (
      <div className="p-6">
        <div className="mb-6">
          <h1 className="text-xl font-bold text-white">Anomaly Timeline</h1>
          <p className="text-sm text-gray-500 mt-0.5">
            Detected metric anomalies across all ads
          </p>
        </div>
        <EmptyState
          title="No anomalies detected"
          description="All metrics are within normal bounds. Anomalies will appear here when detected."
          icon="✅"
        />
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-6 p-6">
      {/* Page header */}
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-white">Anomaly Timeline</h1>
          <p className="text-sm text-gray-500 mt-0.5">
            {anomalies.length} anomal{anomalies.length === 1 ? "y" : "ies"} detected
          </p>
        </div>
        <SeveritySummary anomalies={anomalies} />
      </div>

      <AnomalyTimeline anomalies={anomalies} />
    </div>
  );
}
