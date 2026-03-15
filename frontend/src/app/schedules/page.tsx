"use client";

import { useSchedules, useScheduleStats } from "@/hooks/useSchedules";
import { PageHeader } from "@/components/common/PageHeader";
import { EmptyState } from "@/components/common/EmptyState";
import { PageLoader } from "@/components/common/LoadingSpinner";
import { AutomationCards } from "@/components/schedules/AutomationCards";
import { ScheduleStats } from "@/components/schedules/ScheduleStats";
import { ActivityFeed } from "@/components/schedules/ActivityFeed";
import { Card } from "@/components/common/Card";

export default function SchedulesPage() {
  const { data: logs, isLoading: logsLoading } = useSchedules(100);
  const { data: stats, isLoading: statsLoading } = useScheduleStats();

  if (logsLoading || statsLoading) return <PageLoader />;

  const allLogs = logs ?? [];
  const allStats = stats ?? [];

  return (
    <div className="flex flex-col gap-5">
      <PageHeader
        title="Automations"
        subtitle="Scheduled automated tasks powered by ATLAS"
        actions={
          <span className="px-3 py-1.5 rounded-lg bg-amber-500/10 text-amber-400 text-[11px] font-medium">
            Auto-refreshes every 60s
          </span>
        }
      />

      {/* Summary stats */}
      <ScheduleStats stats={allStats} logs={allLogs} />

      {/* Automation cards */}
      <div>
        <h2 className="text-[13px] font-semibold text-[var(--text)] mb-3">
          Scheduled Automations
        </h2>
        <AutomationCards stats={allStats} />
      </div>

      {/* Activity log */}
      <Card
        title="Activity Log"
        subtitle="Recent run history across all automations"
      >
        {allLogs.length === 0 ? (
          <EmptyState
            title="No runs recorded yet"
            description="Activity will appear here once the scheduled tasks start running. First runs should occur within a few hours."
          />
        ) : (
          <ActivityFeed logs={allLogs} />
        )}
      </Card>
    </div>
  );
}
