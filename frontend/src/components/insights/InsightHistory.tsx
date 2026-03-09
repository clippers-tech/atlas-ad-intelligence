"use client";

import type { ClaudeInsight } from "@/lib/types";
import { formatDate } from "@/lib/utils";
import DigestCard from "./DigestCard";

interface InsightHistoryProps {
  insights: ClaudeInsight[];
}

function groupByDate(insights: ClaudeInsight[]): Record<string, ClaudeInsight[]> {
  return insights.reduce<Record<string, ClaudeInsight[]>>((acc, insight) => {
    const date = formatDate(insight.created_at);
    if (!acc[date]) acc[date] = [];
    acc[date].push(insight);
    return acc;
  }, {});
}

export default function InsightHistory({ insights }: InsightHistoryProps) {
  if (insights.length === 0) {
    return (
      <div className="text-center py-12 text-gray-500 text-sm">
        No insights available yet.
      </div>
    );
  }

  const grouped = groupByDate(insights);
  const dates = Object.keys(grouped).sort((a, b) =>
    new Date(b).getTime() - new Date(a).getTime()
  );

  return (
    <div className="space-y-8 max-h-[70vh] overflow-y-auto pr-1 scrollbar-thin scrollbar-track-gray-900 scrollbar-thumb-gray-700">
      {dates.map((date) => (
        <div key={date}>
          <div className="sticky top-0 z-10 py-2 bg-gray-950">
            <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-widest">
              {date}
            </h3>
          </div>
          <div className="space-y-3 mt-2">
            {grouped[date].map((insight) => (
              <DigestCard key={insight.id} insight={insight} />
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}
