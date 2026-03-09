"use client";

import { formatRelative } from "@/lib/utils";

interface Alert {
  type: "new_ad" | "paused" | "similar_creative" | string;
  message: string;
  timestamp: string;
}

interface CompetitorAlertsProps {
  alerts: Alert[];
}

const ALERT_CONFIG: Record<
  string,
  { emoji: string; color: string; bg: string }
> = {
  new_ad: { emoji: "🆕", color: "text-emerald-400", bg: "bg-emerald-950/30 border-emerald-900/40" },
  paused: { emoji: "⏸️", color: "text-amber-400", bg: "bg-amber-950/30 border-amber-900/40" },
  similar_creative: { emoji: "⚠️", color: "text-red-400", bg: "bg-red-950/30 border-red-900/40" },
};

const DEFAULT_CONFIG = {
  emoji: "📢",
  color: "text-gray-400",
  bg: "bg-gray-800/40 border-gray-700/40",
};

export default function CompetitorAlerts({ alerts }: CompetitorAlertsProps) {
  if (alerts.length === 0) {
    return (
      <div className="flex items-center gap-3 px-4 py-3 bg-gray-900/50 border border-gray-800 rounded-xl text-sm text-gray-500">
        <span>🔔</span>
        <span>No competitor alerts. We'll notify you when activity is detected.</span>
      </div>
    );
  }

  return (
    <div className="space-y-2">
      <h2 className="text-sm font-semibold text-gray-400 uppercase tracking-wide">
        Alerts
      </h2>
      <div className="space-y-2">
        {alerts.map((alert, idx) => {
          const config = ALERT_CONFIG[alert.type] ?? DEFAULT_CONFIG;
          return (
            <div
              key={idx}
              className={`flex items-start gap-3 px-4 py-3 border rounded-lg text-sm ${config.bg}`}
            >
              <span className="text-base flex-shrink-0 mt-0.5">{config.emoji}</span>
              <div className="flex-1 min-w-0">
                <p className={`font-medium ${config.color}`}>{alert.message}</p>
              </div>
              <span className="text-xs text-gray-600 flex-shrink-0 whitespace-nowrap">
                {formatRelative(alert.timestamp)}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
