"use client";

import { formatCurrency, formatPercent, formatNumber } from "@/lib/utils";
import type { PlacementBreakdown as PlacementBreakdownType } from "@/lib/types";

interface PlacementBreakdownProps {
  placements: PlacementBreakdownType[];
}

function formatPlacementLabel(placement: string): string {
  return placement
    .replace(/_/g, " ")
    .replace(/\b\w/g, (c) => c.toUpperCase());
}

export function PlacementBreakdown({ placements }: PlacementBreakdownProps) {
  if (placements.length === 0) {
    return (
      <div className="px-4 py-3 text-xs text-gray-500">
        No placement data available
      </div>
    );
  }

  return (
    <div className="px-4 py-3 bg-[#0f0f0f] border-t border-[#262626]">
      <p className="text-xs font-medium text-gray-400 mb-2 uppercase tracking-wider">
        Placement Breakdown
      </p>
      <table className="w-full text-xs">
        <thead>
          <tr className="border-b border-[#1e1e1e]">
            <th className="text-left text-gray-500 font-medium pb-1.5 pr-4">
              Placement
            </th>
            <th className="text-right text-gray-500 font-medium pb-1.5 pr-4">
              Spend
            </th>
            <th className="text-right text-gray-500 font-medium pb-1.5 pr-4">
              CTR
            </th>
            <th className="text-right text-gray-500 font-medium pb-1.5 pr-4">
              CPL
            </th>
            <th className="text-right text-gray-500 font-medium pb-1.5">
              Conversions
            </th>
          </tr>
        </thead>
        <tbody className="divide-y divide-[#1a1a1a]">
          {placements.map((p) => (
            <tr key={p.placement}>
              <td className="py-1.5 pr-4 text-gray-300">
                {formatPlacementLabel(p.placement)}
              </td>
              <td className="py-1.5 pr-4 text-right text-gray-400 tabular-nums">
                {formatCurrency(p.spend)}
              </td>
              <td className="py-1.5 pr-4 text-right text-gray-400 tabular-nums">
                {formatPercent(p.ctr * 100)}
              </td>
              <td className="py-1.5 pr-4 text-right tabular-nums">
                <span
                  className={
                    p.cpl < 50
                      ? "text-emerald-400"
                      : p.cpl > 150
                      ? "text-red-400"
                      : "text-gray-300"
                  }
                >
                  {formatCurrency(p.cpl)}
                </span>
              </td>
              <td className="py-1.5 text-right text-gray-400 tabular-nums">
                {formatNumber(p.conversions)}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
