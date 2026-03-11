"use client";

import { useState, useEffect, useRef } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { fetchData, postData } from "@/lib/api";
import { PageLoader, LoadingSpinner } from "@/components/common/LoadingSpinner";
import CompetitorAdGallery from "@/components/competitors/CompetitorAdGallery";
import type { Competitor, CompetitorAd } from "@/lib/types";

interface Props {
  competitor: Competitor;
}

type FetchState =
  | { phase: "idle" }
  | { phase: "starting" }
  | { phase: "polling"; runId: string }
  | { phase: "done"; message: string }
  | { phase: "error"; message: string };

export default function CompetitorDetail({ competitor }: Props) {
  const [page, setPage] = useState(1);
  const [fetchState, setFetchState] = useState<FetchState>({ phase: "idle" });
  const queryClient = useQueryClient();
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const perPage = 12;

  const { data, isLoading } = useQuery({
    queryKey: ["competitor-ads", competitor.id, page],
    queryFn: () =>
      fetchData<{ data: CompetitorAd[]; meta: { total: number } }>(
        `/competitors/${competitor.id}/ads`,
        { page, per_page: perPage }
      ),
  });

  // Clean up polling on unmount or competitor change
  useEffect(() => {
    return () => { if (pollRef.current) clearInterval(pollRef.current); };
  }, [competitor.id]);

  const handleFetch = async () => {
    if (!competitor.meta_page_id) {
      setFetchState({ phase: "error", message: "No Meta Page ID — add one first." });
      return;
    }
    setFetchState({ phase: "starting" });

    try {
      const res = await postData<{ status: string; run_id: string }>(`/competitors/${competitor.id}/fetch`);
      const runId = res.run_id;
      setFetchState({ phase: "polling", runId });

      // Start polling every 10s
      pollRef.current = setInterval(async () => {
        try {
          const status = await fetchData<{
            status: string;
            new_ads_found?: number;
            updated?: number;
            error?: string;
          }>(`/competitors/${competitor.id}/fetch-status`, { run_id: runId });

          if (status.status === "completed") {
            if (pollRef.current) clearInterval(pollRef.current);
            const msg = `Found ${status.new_ads_found ?? 0} new ads, updated ${status.updated ?? 0}.`;
            setFetchState({ phase: "done", message: msg });
            queryClient.invalidateQueries({ queryKey: ["competitor-ads"] });
            queryClient.invalidateQueries({ queryKey: ["competitors"] });
          } else if (status.status === "failed") {
            if (pollRef.current) clearInterval(pollRef.current);
            setFetchState({ phase: "error", message: status.error || "Scraper failed." });
          }
          // else still "running" — keep polling
        } catch {
          // Network error during poll — keep trying
        }
      }, 10000);
    } catch (err: any) {
      const detail = err?.response?.data?.detail || "Failed to start scraper.";
      setFetchState({ phase: "error", message: detail });
    }
  };

  const ads = data?.data ?? [];
  const total = data?.meta?.total ?? 0;
  const totalPages = Math.ceil(total / perPage);
  const isFetching = fetchState.phase === "starting" || fetchState.phase === "polling";

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
            disabled={isFetching}
            className="px-3 py-1.5 rounded-lg bg-emerald-500/15 text-emerald-400 text-[11px] font-medium hover:bg-emerald-500/25 transition-colors disabled:opacity-40 flex items-center gap-1.5"
          >
            {isFetching && <LoadingSpinner size="sm" />}
            {isFetching ? "Fetching..." : "Fetch Ads"}
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

      {/* Fetch status bar */}
      {fetchState.phase !== "idle" && (
        <FetchStatusBar state={fetchState} />
      )}

      {/* Ad Gallery */}
      {isLoading ? <PageLoader /> : <CompetitorAdGallery ads={ads} />}

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-center gap-3 pt-2">
          <button
            onClick={() => setPage((p) => Math.max(1, p - 1))}
            disabled={page === 1}
            className="px-3 py-1 rounded bg-[var(--surface-2)] text-[var(--muted)] text-xs disabled:opacity-30"
          >
            Previous
          </button>
          <span className="text-xs text-[var(--muted)]">{page} / {totalPages}</span>
          <button
            onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
            disabled={page === totalPages}
            className="px-3 py-1 rounded bg-[var(--surface-2)] text-[var(--muted)] text-xs disabled:opacity-30"
          >
            Next
          </button>
        </div>
      )}
    </div>
  );
}

function FetchStatusBar({ state }: { state: FetchState }) {
  const colors = {
    starting: "border-amber-500/30 bg-amber-950/20 text-amber-400",
    polling: "border-blue-500/30 bg-blue-950/20 text-blue-400",
    done: "border-emerald-500/30 bg-emerald-950/20 text-emerald-400",
    error: "border-red-500/30 bg-red-950/20 text-red-400",
    idle: "",
  };

  const messages = {
    starting: "Starting scraper...",
    polling: "Scraper running — checking for results every 10s...",
    done: (state as any).message || "Done.",
    error: (state as any).message || "Error.",
    idle: "",
  };

  return (
    <div className={`px-3 py-2 rounded-lg border text-xs ${colors[state.phase]}`}>
      {state.phase === "polling" && <span className="inline-block mr-1.5 animate-pulse">●</span>}
      {messages[state.phase]}
    </div>
  );
}
