"use client";

import { AnomalyDot } from "./AnomalyDot";
import { formatNumber, formatPercent, formatDate } from "@/lib/utils";
import type { Anomaly } from "@/lib/types";

interface AnomalyTimelineProps {
  anomalies: Anomaly[];
}

// Group anomalies by date
function groupByDate(anomalies: Anomaly[]): Record<string, Anomaly[]> {
  const groups: Record<string, Anomaly[]> = {};
  for (const a of anomalies) {
    const day = a.timestamp.slice(0, 10);
    if (!groups[day]) groups[day] = [];
    groups[day].push(a);
  }
  return groups;
}

function SeverityIcon({ severity }: { severity: Anomaly["severity"] }) {
  const colors = {
    high: "text-red-400",
    medium: "text-amber-400",
    low: "text-gray-400",
  };
  return <span className={`text-sm ${colors[severity]}`}>●</span>;
}

export function AnomalyTimeline({ anomalies }: AnomalyTimelineProps) {
  const activeAnomalies = anomalies.filter(
    (a) => a.severity === "high" || a.severity === "medium"
  );
  const grouped = groupByDate(anomalies);
  const sortedDays = Object.keys(grouped).sort((a, b) =>
    b.localeCompare(a)
  );

  return (
    <div className="flex flex-col gap-6">
      {/* Current Anomalies Panel */}
      {activeAnomalies.length > 0 && (
        <div className="bg-[#141414] border border-red-500/20 rounded-xl p-5">
          <h3 className="text-sm font-semibold text-white mb-4">
            ⚠️ Active Anomalies ({activeAnomalies.length})
          </h3>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-[#262626]">
                  <th className="text-left text-xs text-gray-400 font-medium pb-2 pr-4">Metric</th>
                  <th className="text-right text-xs text-gray-400 font-medium pb-2 pr-4">Current</th>
                  <th className="text-right text-xs text-gray-400 font-medium pb-2 pr-4">Avg</th>
                  <th className="text-right text-xs text-gray-400 font-medium pb-2">Deviation</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#1e1e1e]">
                {activeAnomalies.map((a) => (
                  <tr key={a.id}>
                    <td className="py-2 pr-4">
                      <div className="flex items-center gap-2">
                        <SeverityIcon severity={a.severity} />
                        <span className="text-gray-300 capitalize">
                          {a.metric.replace(/_/g, " ")}
                        </span>
                        {a.ad_name && (
                          <span className="text-gray-600 text-xs truncate max-w-[120px]">
                            {a.ad_name}
                          </span>
                        )}
                      </div>
                    </td>
                    <td className="py-2 pr-4 text-right text-gray-200 tabular-nums">
                      {formatNumber(a.current_value)}
                    </td>
                    <td className="py-2 pr-4 text-right text-gray-400 tabular-nums">
                      {formatNumber(a.avg_value)}
                    </td>
                    <td className={`py-2 text-right tabular-nums ${
                      a.deviation_percent > 0 ? "text-red-400" : "text-emerald-400"
                    }`}>
                      {a.deviation_percent > 0 ? "+" : ""}
                      {formatPercent(a.deviation_percent)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Timeline */}
      <div className="bg-[#141414] border border-[#262626] rounded-xl p-5">
        <h3 className="text-sm font-semibold text-white mb-5">Timeline</h3>
        {sortedDays.length === 0 ? (
          <p className="text-gray-500 text-sm">No anomaly history</p>
        ) : (
          <div className="flex flex-col gap-4">
            {sortedDays.map((day) => (
              <div key={day} className="flex items-start gap-4">
                <span className="text-xs text-gray-500 w-20 flex-shrink-0 pt-0.5">
                  {formatDate(day)}
                </span>
                <div className="flex-1 relative">
                  <div className="absolute left-0 top-1.5 right-0 h-px bg-[#262626]" />
                  <div className="flex flex-wrap gap-2 relative z-10">
                    {grouped[day].map((anomaly) => (
                      <AnomalyDot key={anomaly.id} anomaly={anomaly} />
                    ))}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
