"use client";

import type { Competitor } from "@/lib/types";

interface CompetitorCardProps {
  competitor: Competitor;
  onSelect: (competitor: Competitor) => void;
  onDelete: (id: string) => void;
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
      onClick={() => onSelect(competitor)}
    >
      <div className="flex items-start justify-between gap-3">
        {/* Name + status */}
        <div className="min-w-0">
          <div className="flex items-center gap-2">
            <h3 className="font-semibold text-gray-100 truncate">
              {competitor.competitor_name}
            </h3>
            <span
              className={`flex-shrink-0 w-2 h-2 rounded-full ${
                competitor.is_active ? "bg-emerald-400" : "bg-gray-600"
              }`}
              title={competitor.is_active ? "Active" : "Inactive"}
            />
          </div>
          {competitor.website_url && (
            <p className="text-xs text-gray-500 truncate mt-0.5">
              {competitor.website_url}
            </p>
          )}
        </div>

        {/* Delete */}
        <button
          onClick={(e) => {
            e.stopPropagation();
            onDelete(competitor.id);
          }}
          className="flex-shrink-0 text-gray-600 hover:text-red-400 transition-colors text-sm"
          aria-label="Delete competitor"
        >
          ×
        </button>
      </div>

      {/* Stats */}
      <div className="mt-3 grid grid-cols-3 gap-3">
        <div className="text-center">
          <p className="text-lg font-bold text-gray-100">
            {competitor.active_ads_count ?? 0}
          </p>
          <p className="text-xs text-gray-500">Active Ads</p>
        </div>
        <div className="text-center">
          <p className="text-lg font-bold text-emerald-400">
            +{competitor.new_this_week ?? 0}
          </p>
          <p className="text-xs text-gray-500">New This Week</p>
        </div>
        <div className="text-center">
          <p className="text-sm font-semibold text-amber-400">
            {competitor.est_monthly_spend ?? "—"}
          </p>
          <p className="text-xs text-gray-500">Est. Monthly</p>
        </div>
      </div>

      {/* Meta ID if present */}
      {competitor.meta_page_id && (
        <div className="mt-3 pt-3 border-t border-gray-800">
          <p className="text-xs text-gray-600 font-mono">
            Page ID: {competitor.meta_page_id}
          </p>
        </div>
      )}
    </div>
  );
}
