"use client";

import type { Competitor } from "@/lib/types";
import { formatRelative } from "@/lib/utils";

interface CompetitorCardProps {
  competitor: Competitor;
  onSelect: () => void;
  onDelete: () => void;
  isSelected?: boolean;
}

export default function CompetitorCard({
  competitor,
  onSelect,
  onDelete,
  isSelected,
}: CompetitorCardProps) {
  return (
    <div
      className={`border rounded-xl p-4 cursor-pointer transition-all ${
        isSelected
          ? "border-violet-500 bg-violet-950/20"
          : "border-gray-800 bg-gray-900/40 hover:border-gray-700"
      }`}
      onClick={onSelect}
    >
      <div className="flex items-start justify-between gap-3">
        {/* Name + status */}
        <div className="min-w-0">
          <div className="flex items-center gap-2">
            <div className="w-7 h-7 rounded-md bg-violet-600/20 flex items-center justify-center text-violet-400 text-xs font-bold flex-shrink-0">
              {competitor.competitor_name.charAt(0).toUpperCase()}
            </div>
            <h3 className="font-semibold text-gray-100 truncate text-sm">
              {competitor.competitor_name}
            </h3>
          </div>
          {competitor.website_url && (
            <p className="text-xs text-gray-500 truncate mt-1 ml-9">
              {competitor.website_url}
            </p>
          )}
        </div>

        {/* Delete */}
        <button
          onClick={(e) => {
            e.stopPropagation();
            onDelete();
          }}
          className="flex-shrink-0 text-gray-600 hover:text-red-400 transition-colors text-sm"
          aria-label="Delete competitor"
        >
          ×
        </button>
      </div>

      {/* Stats row */}
      <div className="mt-3 pt-3 border-t border-gray-800 flex items-center gap-4">
        <div className="text-xs text-gray-500">
          Ads:{" "}
          <span className="text-gray-200 font-semibold">
            {competitor.total_ads ?? 0}
          </span>
        </div>
        {competitor.meta_page_id && (
          <div className="text-xs text-gray-600 font-mono">
            PID: {competitor.meta_page_id}
          </div>
        )}
      </div>
    </div>
  );
}
