"use client";

import { useSchedules } from "@/hooks/useSchedules";
import { PageHeader } from "@/components/common/PageHeader";
import { EmptyState } from "@/components/common/EmptyState";
import { PageLoader } from "@/components/common/LoadingSpinner";
import { ActivityFeed } from "@/components/schedules/ActivityFeed";

export default function SchedulesPage() {
  const { data: logs, isLoading } = useSchedules(100);

  if (isLoading) return <PageLoader />;

  const allLogs = logs ?? [];

  return (
    <div className="flex flex-col gap-5">
      <PageHeader
        title="Computer Activity"
        subtitle="Scheduled tasks run by Perplexity Computer"
        actions={
          <span className="px-3 py-1.5 rounded-lg bg-amber-500/10 text-amber-400 text-[11px] font-medium">
            Auto-refreshes every 60s
          </span>
        }
      />
      {allLogs.length === 0 ? (
        <EmptyState
          title="No scheduled runs yet"
          description="Activity will appear here once Perplexity Computer starts running scheduled tasks like Meta data pulls, rule evaluations, and competitor analysis."
        />
      ) : (
        <ActivityFeed logs={allLogs} />
      )}
    </div>
  );
}
