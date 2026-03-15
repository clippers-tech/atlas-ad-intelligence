"use client";

import { StatusBadge } from "@/components/common/StatusBadge";
import { formatRelative } from "@/lib/utils";
import type { TaskStats } from "@/hooks/useSchedules";

/** Static config for the 5 automations managed by ATLAS Scheduler */
const AUTOMATIONS = [
  {
    key: "meta_sync",
    label: "Meta Data Sync",
    description: "Pull campaigns, ad sets, ads & metrics from Meta API for all accounts",
    frequency: "Every 4 hours",
    icon: "🔄",
  },
  {
    key: "rules_evaluation",
    label: "Rules Evaluation",
    description: "Evaluate kill, scale, bid & launch rules against latest metrics",
    frequency: "Every 4 hours (1hr after sync)",
    icon: "⚙️",
  },
  {
    key: "competitor_fetch",
    label: "Competitor Ad Fetch",
    description: "Fetch competitor ads via Apify for all accounts",
    frequency: "Daily at 6:12 AM UTC",
    icon: "🔍",
  },
  {
    key: "health_check",
    label: "Health Check",
    description: "Verify backend is alive, DB connected, and data is fresh",
    frequency: "Every 2 hours",
    icon: "💚",
  },
  {
    key: "insight_generation",
    label: "AI Insights",
    description: "Generate AI-powered insights using Claude to analyze ad performance and competitor data",
    frequency: "Every 4 hours",
    icon: "🧠",
  },
] as const;

interface AutomationCardsProps {
  stats: TaskStats[];
}

function getStatusColor(status: string | null): string {
  if (!status) return "bg-[var(--surface-3)]";
  if (status === "completed") return "bg-emerald-500/15";
  if (status === "running") return "bg-blue-500/15";
  return "bg-red-500/15";
}

function getStatusVariant(s: string | null) {
  if (!s) return "muted" as const;
  if (s === "completed") return "success" as const;
  if (s === "running") return "info" as const;
  return "danger" as const;
}

export function AutomationCards({ stats }: AutomationCardsProps) {
  const statsMap = Object.fromEntries(
    stats.map((s) => [s.task_name, s])
  );

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
      {AUTOMATIONS.map((auto) => {
        const s = statsMap[auto.key];
        const successRate =
          s && s.total_runs > 0
            ? Math.round((s.success_count / s.total_runs) * 100)
            : null;

        return (
          <div
            key={auto.key}
            className={`
              relative overflow-hidden rounded-xl border
              border-[var(--border)]/50 p-4
              ${getStatusColor(s?.last_status ?? null)}
              hover:border-[var(--border-light)] transition-all
            `}
          >
            {/* Header */}
            <div className="flex items-start justify-between mb-2">
              <div className="flex items-center gap-2">
                <span className="text-base">{auto.icon}</span>
                <h3 className="text-[13px] font-semibold text-[var(--text)]">
                  {auto.label}
                </h3>
              </div>
              {s ? (
                <StatusBadge
                  label={s.last_status ?? "unknown"}
                  variant={getStatusVariant(s.last_status)}
                />
              ) : (
                <StatusBadge label="No runs yet" variant="muted" />
              )}
            </div>

            {/* Description */}
            <p className="text-[11px] text-[var(--text-secondary)] mb-3 leading-relaxed">
              {auto.description}
            </p>

            {/* Frequency badge */}
            <div className="flex items-center gap-1.5 mb-3">
              <span className="text-[10px] text-[var(--muted)] bg-[var(--surface-3)] px-2 py-0.5 rounded-md">
                {auto.frequency}
              </span>
            </div>

            {/* Stats row */}
            <div className="flex items-center gap-4 text-[11px]">
              {s ? (
                <>
                  <div>
                    <span className="text-[var(--muted)]">Runs: </span>
                    <span className="text-[var(--text)] font-medium tabular-nums">
                      {s.total_runs}
                    </span>
                  </div>
                  <div>
                    <span className="text-[var(--muted)]">Pass: </span>
                    <span className="text-emerald-400 font-medium tabular-nums">
                      {successRate}%
                    </span>
                  </div>
                  <div>
                    <span className="text-[var(--muted)]">Fail: </span>
                    <span className={`font-medium tabular-nums ${
                      s.fail_count > 0 ? "text-red-400" : "text-[var(--muted)]"
                    }`}>
                      {s.fail_count}
                    </span>
                  </div>
                  {s.last_run_at && (
                    <div className="ml-auto">
                      <span className="text-[var(--muted)]">Last: </span>
                      <span className="text-[var(--text-secondary)]">
                        {formatRelative(s.last_run_at)}
                      </span>
                    </div>
                  )}
                </>
              ) : (
                <span className="text-[var(--muted)] italic">
                  Waiting for first run...
                </span>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
}
