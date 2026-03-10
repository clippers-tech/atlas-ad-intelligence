"use client";

import { Card } from "@/components/common/Card";
import { StatusBadge } from "@/components/common/StatusBadge";
import { formatRelative } from "@/lib/utils";
import type { ScheduleLog } from "@/hooks/useSchedules";

interface ActivityFeedProps {
  logs: ScheduleLog[];
  compact?: boolean;
}

const statusVariant = (s: string) => {
  if (s === "completed") return "success";
  if (s === "running") return "info";
  return "danger";
};

const taskLabel = (name: string) =>
  name
    .replace(/_/g, " ")
    .replace(/\b\w/g, (c) => c.toUpperCase());

function formatDuration(ms: number | null): string {
  if (!ms) return "—";
  if (ms < 1000) return `${ms}ms`;
  const secs = Math.round(ms / 1000);
  if (secs < 60) return `${secs}s`;
  return `${Math.floor(secs / 60)}m ${secs % 60}s`;
}

export function ActivityFeed({ logs, compact }: ActivityFeedProps) {
  const displayLogs = compact ? logs.slice(0, 5) : logs;

  return (
    <div className="flex flex-col gap-2">
      {displayLogs.map((log) => (
        <div
          key={log.id}
          className="flex items-start gap-3 p-3 rounded-lg
            bg-[var(--surface-2)] border border-[var(--border)]/50
            hover:border-[var(--border-light)] transition-colors"
        >
          {/* Status dot */}
          <div className="mt-1 flex-shrink-0">
            <span
              className={`block w-2 h-2 rounded-full ${
                log.status === "completed"
                  ? "bg-emerald-400"
                  : log.status === "running"
                  ? "bg-blue-400 animate-pulse"
                  : "bg-red-400"
              }`}
            />
          </div>

          {/* Content */}
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-0.5">
              <span className="text-[13px] font-medium text-[var(--text)]">
                {taskLabel(log.task_name)}
              </span>
              <StatusBadge
                label={log.status}
                variant={statusVariant(log.status) as "success" | "info" | "danger"}
              />
            </div>
            {log.summary && (
              <p className="text-[12px] text-[var(--text-secondary)] leading-relaxed line-clamp-2">
                {log.summary}
              </p>
            )}
            {log.error_message && (
              <p className="text-[12px] text-red-400/80 leading-relaxed mt-0.5 line-clamp-1">
                {log.error_message}
              </p>
            )}
          </div>

          {/* Meta */}
          <div className="flex-shrink-0 text-right">
            <p className="text-[11px] text-[var(--muted)]">
              {formatRelative(log.started_at)}
            </p>
            {log.duration_ms && (
              <p className="text-[11px] text-[var(--muted)] mt-0.5">
                {formatDuration(log.duration_ms)}
              </p>
            )}
          </div>
        </div>
      ))}
    </div>
  );
}
