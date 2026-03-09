"use client";

import { useState } from "react";
import { StatusBadge } from "@/components/common/StatusBadge";
import { FatigueIndicator } from "./FatigueIndicator";
import { PlacementBreakdown } from "./PlacementBreakdown";
import {
  formatCurrency,
  formatPercent,
  formatNumber,
} from "@/lib/utils";
import type { CreativePerformance } from "@/lib/types";

interface CreativeTableProps {
  creatives: CreativePerformance[];
}

export function CreativeTable({ creatives }: CreativeTableProps) {
  const [expandedId, setExpandedId] = useState<string | null>(null);

  function toggleExpand(id: string) {
    setExpandedId((prev) => (prev === id ? null : id));
  }

  return (
    <div className="bg-[#141414] border border-[#262626] rounded-xl overflow-hidden">
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="bg-[#1a1a1a] border-b border-[#262626]">
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider w-8">#</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">Creative</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">Status</th>
              <th className="px-4 py-3 text-right text-xs font-medium text-gray-400 uppercase tracking-wider">Spend</th>
              <th className="px-4 py-3 text-right text-xs font-medium text-gray-400 uppercase tracking-wider">CTR</th>
              <th className="px-4 py-3 text-right text-xs font-medium text-gray-400 uppercase tracking-wider">CPL</th>
              <th className="px-4 py-3 text-right text-xs font-medium text-gray-400 uppercase tracking-wider">3s View</th>
              <th className="px-4 py-3 text-right text-xs font-medium text-gray-400 uppercase tracking-wider">Hold p50</th>
              <th className="px-4 py-3 text-right text-xs font-medium text-gray-400 uppercase tracking-wider">Hold p75</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">Fatigue</th>
              <th className="px-4 py-3 text-right text-xs font-medium text-gray-400 uppercase tracking-wider">Age</th>
              <th className="px-4 py-3 w-8" />
            </tr>
          </thead>
          <tbody className="divide-y divide-[#262626]">
            {creatives.length === 0 ? (
              <tr>
                <td colSpan={12} className="px-4 py-8 text-center text-gray-500">
                  No creatives found
                </td>
              </tr>
            ) : (
              creatives.map((c, idx) => (
                <>
                  <tr
                    key={c.id}
                    className="hover:bg-[#1a1a1a] transition-colors cursor-pointer"
                    onClick={() => toggleExpand(c.id)}
                  >
                    <td className="px-4 py-3 text-gray-500 text-xs tabular-nums">
                      {idx + 1}
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-3">
                        {c.thumbnail_url ? (
                          <img
                            src={c.thumbnail_url}
                            alt={c.name}
                            className="w-8 h-8 rounded object-cover bg-[#262626] flex-shrink-0"
                          />
                        ) : (
                          <div className="w-8 h-8 rounded bg-[#262626] flex-shrink-0 flex items-center justify-center text-gray-600 text-xs">
                            🖼
                          </div>
                        )}
                        <span className="text-gray-200 font-medium truncate max-w-[160px]">
                          {c.name}
                        </span>
                      </div>
                    </td>
                    <td className="px-4 py-3">
                      <StatusBadge status={c.status} size="sm" />
                    </td>
                    <td className="px-4 py-3 text-right text-gray-300 tabular-nums">
                      {formatCurrency(c.spend)}
                    </td>
                    <td className="px-4 py-3 text-right text-gray-300 tabular-nums">
                      {formatPercent(c.ctr * 100)}
                    </td>
                    <td className="px-4 py-3 text-right tabular-nums">
                      <span className={c.cpl < 80 ? "text-emerald-400" : c.cpl > 200 ? "text-red-400" : "text-gray-300"}>
                        {formatCurrency(c.cpl)}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-right text-gray-300 tabular-nums">
                      {formatPercent(c.video_view_3s_rate * 100)}
                    </td>
                    <td className="px-4 py-3 text-right text-gray-300 tabular-nums">
                      {formatPercent(c.video_p50 * 100)}
                    </td>
                    <td className="px-4 py-3 text-right text-gray-300 tabular-nums">
                      {formatPercent(c.video_p75 * 100)}
                    </td>
                    <td className="px-4 py-3">
                      <FatigueIndicator level={c.fatigue_level} />
                    </td>
                    <td className="px-4 py-3 text-right text-gray-400 tabular-nums text-xs">
                      {c.age_days}d
                    </td>
                    <td className="px-4 py-3 text-gray-500 text-center">
                      {expandedId === c.id ? "▲" : "▼"}
                    </td>
                  </tr>

                  {expandedId === c.id && (
                    <tr key={`${c.id}-breakdown`}>
                      <td colSpan={12} className="p-0">
                        <PlacementBreakdown placements={c.placements} />
                      </td>
                    </tr>
                  )}
                </>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
