"use client";

import type { CompetitorAd } from "@/lib/types";
import { formatDate, truncate } from "@/lib/utils";

interface CompetitorAdGalleryProps {
  ads: CompetitorAd[];
}

export default function CompetitorAdGallery({ ads }: CompetitorAdGalleryProps) {
  if (ads.length === 0) {
    return (
      <div className="text-center py-12 text-gray-500 text-sm border border-dashed border-gray-800 rounded-xl">
        No ads found for this competitor yet.
        <br />
        <span className="text-xs text-gray-600 mt-1 block">
          Ads will appear here once ingested from Meta Ad Library.
        </span>
      </div>
    );
  }

  return (
    <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
      {ads.map((ad) => (
        <AdCard key={ad.id} ad={ad} />
      ))}
    </div>
  );
}

function AdCard({ ad }: { ad: CompetitorAd }) {
  return (
    <div className="border border-gray-800 rounded-xl overflow-hidden bg-gray-900/50 hover:border-gray-700 transition-colors">
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
          <div className="text-gray-700 text-3xl">📷</div>
        )}
        <span
          className={`absolute top-2 right-2 px-2 py-0.5 rounded-full text-[10px] font-semibold ${
            ad.is_active
              ? "bg-emerald-500/20 text-emerald-400 border border-emerald-500/30"
              : "bg-gray-700/60 text-gray-400 border border-gray-600/30"
          }`}
        >
          {ad.is_active ? "Active" : "Inactive"}
        </span>
      </div>

      {/* Content */}
      <div className="p-3 space-y-2">
        {ad.ad_text && (
          <p className="text-sm text-gray-300 leading-snug">
            {truncate(ad.ad_text, 120)}
          </p>
        )}

        {ad.hook_text && (
          <p className="text-xs text-gray-500 italic">
            &quot;{truncate(ad.hook_text, 80)}&quot;
          </p>
        )}

        {ad.offer_text && (
          <p className="text-xs text-amber-400/80">
            Offer: {truncate(ad.offer_text, 60)}
          </p>
        )}

        {/* Badges */}
        <div className="flex flex-wrap gap-1.5">
          {ad.hook_type && (
            <span className="px-2 py-0.5 rounded-full text-[10px] bg-blue-900/40 text-blue-400 border border-blue-800/40">
              {ad.hook_type}
            </span>
          )}
          {ad.cta_type && (
            <span className="px-2 py-0.5 rounded-full text-[10px] bg-violet-900/40 text-violet-400 border border-violet-800/40">
              {ad.cta_type}
            </span>
          )}
          {ad.estimated_spend_range && (
            <span className="px-2 py-0.5 rounded-full text-[10px] bg-amber-900/40 text-amber-400 border border-amber-800/40">
              ${ad.estimated_spend_range}
            </span>
          )}
        </div>

        {/* Dates */}
        <div className="flex items-center justify-between text-[10px] text-gray-600 pt-1.5 border-t border-gray-800">
          <span>
            First: {ad.first_seen ? formatDate(ad.first_seen) : "—"}
          </span>
          <span>
            Last: {ad.last_seen ? formatDate(ad.last_seen) : "—"}
          </span>
        </div>
      </div>
    </div>
  );
}
