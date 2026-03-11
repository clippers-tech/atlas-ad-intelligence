"use client";

import type { TaskStats, ScheduleLog } from "@/hooks/useSchedules";

interface ScheduleStatsProps {
  stats: TaskStats[];
  logs: ScheduleLog[];
}

export function ScheduleStats({ stats, logs }: ScheduleStatsProps) {
  const totalRuns = stats.reduce((sum, s) => sum + s.total_runs, 0);
  const totalFails = stats.reduce((sum, s) => sum + s.fail_count, 0);
  const overallRate =
    totalRuns > 0
      ? Math.round(((totalRuns - totalFails) / totalRuns) * 100)
      : 0;

  const activeTasks = stats.length;
  const configuredTasks = 4; // We have 4 automations configured

  // Count runs in the last 24h from the log feed
  const now = Date.now();
  const last24h = logs.filter(
    (l) => now - new Date(l.started_at).getTime() < 86_400_000
  ).length;

  const items = [
    {
      label: "Automations",
      value: `${activeTasks}/${configuredTasks}`,
      sub: "active",
      color: activeTasks === configuredTasks ? "text-emerald-400" : "text-amber-400",
    },
    {
      label: "Total Runs",
      value: totalRuns.toString(),
      sub: "all time",
      color: "text-[var(--text)]",
    },
    {
      label: "Last 24h",
      value: last24h.toString(),
      sub: "runs",
      color: "text-[var(--text)]",
    },
    {
      label: "Success Rate",
      value: totalRuns > 0 ? `${overallRate}%` : "—",
      sub: totalFails > 0 ? `${totalFails} failed` : "no failures",
      color: overallRate >= 90 ? "text-emerald-400" : overallRate >= 70 ? "text-amber-400" : "text-red-400",
    },
  ];

  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
      {items.map((item) => (
        <div
          key={item.label}
          className="bg-[var(--surface)] border border-[var(--border)]/50 rounded-xl p-4"
        >
          <p className="text-[11px] text-[var(--muted)] mb-1">
            {item.label}
          </p>
          <p className={`text-xl font-semibold tabular-nums ${item.color}`}>
            {item.value}
          </p>
          <p className="text-[10px] text-[var(--muted)] mt-0.5">
            {item.sub}
          </p>
        </div>
      ))}
    </div>
  );
}
