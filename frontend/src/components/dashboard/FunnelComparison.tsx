"use client";

import { formatNumber, formatPercent } from "@/lib/utils";
import type { FunnelStage } from "@/lib/types";

interface CampaignFunnel {
  name: string;
  funnel: FunnelStage[];
}

interface FunnelComparisonProps {
  campaigns: CampaignFunnel[];
}

const COLUMN_COLORS = [
  "border-blue-500/40 bg-blue-500/10",
  "border-violet-500/40 bg-violet-500/10",
  "border-emerald-500/40 bg-emerald-500/10",
];

const HEADER_COLORS = [
  "text-blue-400",
  "text-violet-400",
  "text-emerald-400",
];

// For each stage index, find which campaign has the best (highest) percent_of_top
function getBestAtStage(campaigns: CampaignFunnel[], stageIdx: number): number {
  let best = -1;
  let bestVal = -Infinity;
  campaigns.forEach((c, i) => {
    const val = c.funnel[stageIdx]?.percent_of_top ?? -1;
    if (val > bestVal) {
      bestVal = val;
      best = i;
    }
  });
  return best;
}

export function FunnelComparison({ campaigns }: FunnelComparisonProps) {
  if (campaigns.length === 0) {
    return (
      <div className="bg-[#141414] border border-[#262626] rounded-xl p-6 text-center text-gray-500 text-sm">
        No campaigns to compare
      </div>
    );
  }

  const maxStages = Math.max(...campaigns.map((c) => c.funnel.length));

  return (
    <div className="bg-[#141414] border border-[#262626] rounded-xl p-6">
      <h3 className="text-sm font-semibold text-white mb-5">Campaign Funnel Comparison</h3>
      <div
        className="grid gap-4"
        style={{ gridTemplateColumns: `120px repeat(${campaigns.length}, 1fr)` }}
      >
        {/* Stage label column */}
        <div className="flex flex-col gap-2">
          <div className="h-10" />
          {Array.from({ length: maxStages }).map((_, stageIdx) => {
            const label = campaigns[0]?.funnel[stageIdx]?.name ?? `Stage ${stageIdx + 1}`;
            return (
              <div
                key={stageIdx}
                className="h-12 flex items-center text-xs text-gray-500 font-medium"
              >
                {label}
              </div>
            );
          })}
        </div>

        {/* One column per campaign */}
        {campaigns.map((campaign, cIdx) => (
          <div
            key={campaign.name}
            className={`flex flex-col gap-2 rounded-lg border p-2 ${COLUMN_COLORS[cIdx % COLUMN_COLORS.length]}`}
          >
            {/* Header */}
            <div
              className={`h-10 flex items-center justify-center text-xs font-semibold text-center px-1 ${HEADER_COLORS[cIdx % HEADER_COLORS.length]}`}
            >
              {campaign.name}
            </div>

            {Array.from({ length: maxStages }).map((_, stageIdx) => {
              const stage = campaign.funnel[stageIdx];
              const isBest = getBestAtStage(campaigns, stageIdx) === cIdx && campaigns.length > 1;

              return (
                <div
                  key={stageIdx}
                  className={`h-12 rounded flex flex-col items-center justify-center gap-0.5 transition-colors ${
                    isBest ? "bg-emerald-500/10 ring-1 ring-emerald-500/30" : "bg-[#1a1a1a]"
                  }`}
                >
                  {stage ? (
                    <>
                      <span className="text-sm font-bold text-white tabular-nums">
                        {formatNumber(stage.count)}
                      </span>
                      <span className={`text-xs tabular-nums ${isBest ? "text-emerald-400" : "text-gray-500"}`}>
                        {formatPercent(stage.percent_of_top)}
                        {isBest && " ✓"}
                      </span>
                    </>
                  ) : (
                    <span className="text-gray-600 text-xs">—</span>
                  )}
                </div>
              );
            })}
          </div>
        ))}
      </div>
    </div>
  );
}
