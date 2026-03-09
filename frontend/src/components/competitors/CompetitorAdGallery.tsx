"use client";

import type { CompetitorAd } from "@/lib/types";
import { formatDate, truncate } from "@/lib/utils";

interface CompetitorAdGalleryProps {
  ads: CompetitorAd[];
}

export default function CompetitorAdGallery({ ads }: CompetitorAdGalleryProps) {
  if (ads.length === 0) {
    return (
      <div className="text-center py-12 text-gray-500 text-sm">
        No ads found for this competitor.
      </div>
    );
  }

  return (
    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
      {ads.map((ad) => (
        <div
          key={ad.id}
          className="border border-gray-800 rounded-xl overflow-hidden bg-gray-900/50 hover:border-gray-700 transition-colors"
        >
          {/* Thumbnail */}
          <div className="relative aspect-video bg-gray-800 flex items-center justify-center overflow-hidden">
            {ad.creative_url ? (
              <img
                src={ad.creative_url}
                alt="Ad creative"
                className="w-full h-full object-cover"
                onError={(e) => {
                  (e.target as HTMLImageElement).style.display = "none";
                }}
              />
            ) : (
              <div className="text-gray-700 text-4xl">🖼️</div>
            )}
            {/* Status badge */}
            <span
              className={`absolute top-2 right-2 px-2 py-0.5 rounded-full text-xs font-semibold ${
                ad.is_active
                  ? "bg-emerald-500/20 text-emerald-400 border border-emerald-500/30"
                  : "bg-gray-700/60 text-gray-400 border border-gray-600/30"
              }`}
            >
              {ad.is_active ? "Active" : "Paused"}
            </span>
          </div>

          {/* Content */}
          <div className="p-3 space-y-2">
            {/* Ad text */}
            {ad.ad_text && (
              <p className="text-sm text-gray-300 leading-snug">
                {truncate(ad.ad_text, 120)}
              </p>
            )}

            {/* Hook text */}
            {ad.hook_text && (
              <p className="text-xs text-gray-500 italic">
                "{truncate(ad.hook_text, 80)}"
              </p>
            )}

            {/* Badges */}
            <div className="flex flex-wrap gap-2">
              {ad.hook_type && (
                <span className="px-2 py-0.5 rounded-full text-xs bg-blue-900/40 text-blue-400 border border-blue-800/40">
                  Hook: {ad.hook_type}
                </span>
              )}
              {ad.cta_type && (
                <span className="px-2 py-0.5 rounded-full text-xs bg-violet-900/40 text-violet-400 border border-violet-800/40">
                  CTA: {ad.cta_type}
                </span>
              )}
            </div>

            {/* Dates */}
            <div className="flex items-center justify-between text-xs text-gray-600 pt-1 border-t border-gray-800">
              <span>First: {ad.first_seen ? formatDate(ad.first_seen) : "—"}</span>
              <span>Last: {ad.last_seen ? formatDate(ad.last_seen) : "—"}</span>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}
