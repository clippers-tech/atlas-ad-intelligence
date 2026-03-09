"use client";

import { formatCurrency, formatPercent, formatNumber } from "@/lib/utils";
import { AUDIENCE_TYPES } from "@/lib/constants";
import type { AudiencePerformance } from "@/lib/types";

interface AudienceTableProps {
  audiences: AudiencePerformance[];
}

function QualityBadge({ score }: { score: AudiencePerformance["quality_score"] }) {
  const config = {
    high: { label: "High", className: "bg-emerald-500/20 text-emerald-400 border-emerald-500/30", emoji: "🟢" },
    medium: { label: "Medium", className: "bg-amber-500/20 text-amber-400 border-amber-500/30", emoji: "🟡" },
    low: { label: "Low", className: "bg-red-500/20 text-red-400 border-red-500/30", emoji: "🔴" },
  }[score];

  return (
    <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full border text-xs font-medium ${config.className}`}>
      {config.emoji} {config.label}
    </span>
  );
}

function AudienceTypeBadge({ type }: { type: string }) {
  const found = AUDIENCE_TYPES.find((t) => t.value === type);
  const label = found?.label ?? type;
  const colorMap: Record<string, string> = {
    blue: "bg-blue-500/20 text-blue-400",
    violet: "bg-violet-500/20 text-violet-400",
    slate: "bg-slate-500/20 text-slate-400",
    emerald: "bg-emerald-500/20 text-emerald-400",
    amber: "bg-amber-500/20 text-amber-400",
  };
  const colorClass = found ? colorMap[found.color] ?? "bg-gray-500/20 text-gray-400" : "bg-gray-500/20 text-gray-400";

  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${colorClass}`}>
      {label}
    </span>
  );
}

export function AudienceTable({ audiences }: AudienceTableProps) {
  return (
    <div className="bg-[#141414] border border-[#262626] rounded-xl overflow-hidden">
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="bg-[#1a1a1a] border-b border-[#262626]">
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">Audience</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">Type</th>
              <th className="px-4 py-3 text-right text-xs font-medium text-gray-400 uppercase tracking-wider">Spend</th>
              <th className="px-4 py-3 text-right text-xs font-medium text-gray-400 uppercase tracking-wider">Leads</th>
              <th className="px-4 py-3 text-right text-xs font-medium text-gray-400 uppercase tracking-wider">CPL</th>
              <th className="px-4 py-3 text-right text-xs font-medium text-gray-400 uppercase tracking-wider">Frequency</th>
              <th className="px-4 py-3 text-right text-xs font-medium text-gray-400 uppercase tracking-wider">Close Rate</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">Quality</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-[#262626]">
            {audiences.length === 0 ? (
              <tr>
                <td colSpan={8} className="px-4 py-8 text-center text-gray-500">
                  No audience data
                </td>
              </tr>
            ) : (
              audiences.map((a) => (
                <tr key={a.id} className="hover:bg-[#1a1a1a] transition-colors">
                  <td className="px-4 py-3 text-gray-200 font-medium max-w-[200px] truncate">
                    {a.name}
                  </td>
                  <td className="px-4 py-3">
                    <AudienceTypeBadge type={a.audience_type} />
                  </td>
                  <td className="px-4 py-3 text-right text-gray-300 tabular-nums">
                    {formatCurrency(a.spend)}
                  </td>
                  <td className="px-4 py-3 text-right text-gray-300 tabular-nums">
                    {formatNumber(a.leads)}
                  </td>
                  <td className="px-4 py-3 text-right tabular-nums">
                    <span className={a.cpl < 80 ? "text-emerald-400" : a.cpl > 200 ? "text-red-400" : "text-gray-300"}>
                      {formatCurrency(a.cpl)}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-right tabular-nums">
                    <span className={a.frequency > 3 ? "text-amber-400" : "text-gray-300"}>
                      {a.frequency.toFixed(1)}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-right text-gray-300 tabular-nums">
                    {formatPercent(a.close_rate * 100)}
                  </td>
                  <td className="px-4 py-3">
                    <QualityBadge score={a.quality_score} />
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
