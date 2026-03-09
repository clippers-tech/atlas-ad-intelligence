"use client";

import { useState } from "react";
import { useCreatives } from "@/hooks/useCreatives";
import { CreativeTable } from "@/components/creatives/CreativeTable";
import { VelocityAlert } from "@/components/creatives/VelocityAlert";
import { LoadingSpinner } from "@/components/common/LoadingSpinner";
import { EmptyState } from "@/components/common/EmptyState";

type SortKey = "spend" | "ctr" | "cpl" | "video_view_3s_rate" | "age_days";
type SortOrder = "asc" | "desc";

const SORT_OPTIONS: { value: SortKey; label: string }[] = [
  { value: "spend", label: "Spend" },
  { value: "ctr", label: "CTR" },
  { value: "cpl", label: "CPL" },
  { value: "video_view_3s_rate", label: "3s View Rate" },
  { value: "age_days", label: "Age" },
];

export default function CreativesPage() {
  const [sortBy, setSortBy] = useState<SortKey>("spend");
  const [order, setOrder] = useState<SortOrder>("desc");

  const { data: creatives, isLoading, isError } = useCreatives(sortBy, order);

  if (isLoading) {
    return <LoadingSpinner fullHeight label="Loading creatives..." />;
  }

  if (isError) {
    return (
      <EmptyState
        title="Failed to load creatives"
        description="There was an error fetching creative performance data."
        icon="⚠️"
      />
    );
  }

  const allCreatives = creatives ?? [];

  // Compute velocity metrics
  const burnedOrDeclined = allCreatives.filter(
    (c) => c.fatigue_level === "burned" || c.fatigue_level === "declining"
  );

  // Approximate "days without new": oldest fresh creative vs today
  const freshCreatives = allCreatives.filter((c) => c.fatigue_level === "fresh");
  const minAgeFresh = freshCreatives.length > 0
    ? Math.min(...freshCreatives.map((c) => c.age_days))
    : 99;
  const daysWithoutNew = freshCreatives.length === 0 ? 99 : minAgeFresh;

  function toggleOrder() {
    setOrder((o) => (o === "asc" ? "desc" : "asc"));
  }

  return (
    <div className="flex flex-col gap-6 p-6">
      {/* Page header */}
      <div>
        <h1 className="text-xl font-bold text-white">Creative Leaderboard</h1>
        <p className="text-sm text-gray-500 mt-0.5">
          {allCreatives.length} active creatives · sorted by {sortBy}
        </p>
      </div>

      {/* Velocity alert */}
      <VelocityAlert
        daysWithoutNew={daysWithoutNew}
        fatiguedCount={burnedOrDeclined.length}
        totalActive={allCreatives.length}
      />

      {/* Sort controls */}
      <div className="flex items-center gap-3 flex-wrap">
        <span className="text-xs text-gray-400">Sort by:</span>
        {SORT_OPTIONS.map((opt) => (
          <button
            key={opt.value}
            onClick={() => {
              if (sortBy === opt.value) {
                toggleOrder();
              } else {
                setSortBy(opt.value);
                setOrder("desc");
              }
            }}
            className={[
              "px-3 py-1 text-xs rounded-lg border transition-colors",
              sortBy === opt.value
                ? "bg-blue-600/20 border-blue-500/40 text-blue-400"
                : "bg-[#1a1a1a] border-[#262626] text-gray-400 hover:text-gray-200",
            ].join(" ")}
          >
            {opt.label}
            {sortBy === opt.value && (
              <span className="ml-1">{order === "desc" ? "↓" : "↑"}</span>
            )}
          </button>
        ))}
      </div>

      {/* Table */}
      {allCreatives.length === 0 ? (
        <EmptyState
          title="No creatives found"
          description="Creative performance data will appear here once ads are active."
          icon="🎨"
        />
      ) : (
        <CreativeTable creatives={allCreatives} />
      )}
    </div>
  );
}
