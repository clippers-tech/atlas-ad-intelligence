"use client";

import { useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { fetchData, postData } from "@/lib/api";
import { PageLoader } from "@/components/common/LoadingSpinner";
import CompetitorAdGallery from "@/components/competitors/CompetitorAdGallery";
import type { Competitor, CompetitorAd } from "@/lib/types";

interface Props {
  competitor: Competitor;
}

export default function CompetitorDetail({ competitor }: Props) {
  const [page, setPage] = useState(1);
  const [fetching, setFetching] = useState(false);
  const [fetchMsg, setFetchMsg] = useState<string | null>(null);
  const queryClient = useQueryClient();
  const perPage = 12;

  const { data, isLoading } = useQuery({
    queryKey: ["competitor-ads", competitor.id, page],
    queryFn: () =>
      fetchData<{ data: CompetitorAd[]; meta: { total: number } }>(
        `/competitors/${competitor.id}/ads`,
        { page, per_page: perPage }
      ),
  });

  const ads = data?.data ?? [];
  const total = data?.meta?.total ?? 0;
  const totalPages = Math.ceil(total / perPage);

  const handleFetch = async () => {
    if (!competitor.meta_page_id) {
      setFetchMsg("No Meta Page ID — add one to fetch ads.");
      return;
    }
    setFetching(true);
    setFetchMsg(null);
    try {
      const res = await postData<{
        status: string;
        new_ads_found?: number;
        updated?: number;
        detail?: string;
      }>(`/competitors/${competitor.id}/fetch`);
      const newCount = res.new_ads_found ?? 0;
      const updated = res.updated ?? 0;
      setFetchMsg(
        newCount > 0
          ? `Found ${newCount} new ads, updated ${updated}.`
          : res.detail || "No new ads found."
      );
      queryClient.invalidateQueries({ queryKey: ["competitor-ads"] });
      queryClient.invalidateQueries({ queryKey: ["competitors"] });
    } catch (err: any) {
      const detail =
        err?.response?.data?.detail || "Failed to fetch from Ad Library.";
      setFetchMsg(detail);
    } finally {
      setFetching(false);
    }
  };

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div>
          <h3 className="text-lg font-semibold text-[var(--text)]">
            {competitor.competitor_name}
          </h3>
          <p className="text-xs text-[var(--muted)] mt-0.5">
            {total} ads tracked
            {competitor.website_url && ` · ${competitor.website_url}`}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={handleFetch}
            disabled={fetching}
            className="px-3 py-1.5 rounded-lg bg-emerald-500/15 text-emerald-400 text-[11px] font-medium hover:bg-emerald-500/25 transition-colors disabled:opacity-40"
          >
            {fetching ? "Fetching..." : "Fetch Ads from Ad Library"}
          </button>
          {competitor.meta_page_id && (
            <a
              href={`https://www.facebook.com/ads/library/?active_status=active&ad_type=all&country=ALL&view_all_page_id=${competitor.meta_page_id}`}
              target="_blank"
              rel="noopener noreferrer"
              className="px-3 py-1.5 rounded-lg bg-blue-500/15 text-blue-400 text-[11px] font-medium hover:bg-blue-500/25 transition-colors"
            >
              View in Ad Library
            </a>
          )}
        </div>
      </div>

      {/* Fetch feedback */}
      {fetchMsg && (
        <div className="px-3 py-2 rounded-lg bg-[var(--surface-2)] border border-[var(--border)] text-xs text-[var(--muted)]">
          {fetchMsg}
        </div>
      )}

      {/* Ad Gallery */}
      {isLoading ? <PageLoader /> : <CompetitorAdGallery ads={ads} />}

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-center gap-3 pt-2">
          <button
            onClick={() => setPage((p) => Math.max(1, p - 1))}
            disabled={page === 1}
            className="px-3 py-1 rounded bg-[var(--surface-2)] text-[var(--muted)] text-xs disabled:opacity-30 hover:bg-[var(--surface-3)] transition-colors"
          >
            Previous
          </button>
          <span className="text-xs text-[var(--muted)]">
            {page} / {totalPages}
          </span>
          <button
            onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
            disabled={page === totalPages}
            className="px-3 py-1 rounded bg-[var(--surface-2)] text-[var(--muted)] text-xs disabled:opacity-30 hover:bg-[var(--surface-3)] transition-colors"
          >
            Next
          </button>
        </div>
      )}
    </div>
  );
}
