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
  | { phase: "polling"; runId: string; limit: number; cost: number }
  | { phase: "done"; message: string }
  | { phase: "error"; message: string };

const FETCH_LIMIT_OPTIONS = [10, 25, 50];

export default function CompetitorDetail({ competitor }: Props) {
  const [page, setPage] = useState(1);
  const [fetchLimit, setFetchLimit] = useState(10);
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

  useEffect(() => {
    return () => { if (pollRef.current) clearInterval(pollRef.current); };
  }, [competitor.id]);

  const handleFetch = async () => {
    if (!competitor.meta_page_id) {
      setFetchState({ phase: "error", message: "No Meta Page ID." });
      return;
    }
    setFetchState({ phase: "starting" });

    try {
      const res = await postData<{
        status: string;
        run_id: string;
        results_limit: number;
        estimated_cost: number;
      }>(`/competitors/${competitor.id}/fetch?max_ads=${fetchLimit}`);

      const runId = res.run_id;
      setFetchState({
        phase: "polling",
        runId,
        limit: res.results_limit,
        cost: res.estimated_cost,
      });

      pollRef.current = setInterval(async () => {
        try {
          const status = await fetchData<{
            status: string;
            new_ads_found?: number;
            updated?: number;
            error?: string;
          }>(`/competitors/${competitor.id}/fetch-status`, {
            run_id: runId,
            max_ads: fetchLimit,
          });

          if (status.status === "completed") {
            if (pollRef.current) clearInterval(pollRef.current);
            const msg = `Done — ${status.new_ads_found ?? 0} new, ${status.updated ?? 0} updated.`;
            setFetchState({ phase: "done", message: msg });
            queryClient.invalidateQueries({ queryKey: ["competitor-ads"] });
            queryClient.invalidateQueries({ queryKey: ["competitors"] });
          } else if (status.status === "failed") {
            if (pollRef.current) clearInterval(pollRef.current);
            setFetchState({
              phase: "error",
              message: status.error || "Scraper failed.",
            });
          }
        } catch {
          // Network error during poll — keep trying
        }
      }, 10000);
    } catch (err: any) {
      const detail = err?.response?.data?.detail || "Failed to start.";
      setFetchState({ phase: "error", message: detail });
    }
  };

  const ads = data?.data ?? [];
  const total = data?.meta?.total ?? 0;
  const totalPages = Math.ceil(total / perPage);
  const isFetching =
    fetchState.phase === "starting" || fetchState.phase === "polling";
  const estCost = (fetchLimit * 0.005).toFixed(3);

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
        <FetchControls
          fetchLimit={fetchLimit}
          setFetchLimit={setFetchLimit}
          estCost={estCost}
          isFetching={isFetching}
          onFetch={handleFetch}
          hasPageId={!!competitor.meta_page_id}
        />
      </div>

      {fetchState.phase !== "idle" && (
        <FetchStatusBar state={fetchState} />
      )}

      {isLoading ? <PageLoader /> : <CompetitorAdGallery ads={ads} />}

      {totalPages > 1 && (
        <Pagination page={page} totalPages={totalPages} setPage={setPage} />
      )}
    </div>
  );
}

/* ---- Sub-components ---- */

function FetchControls(props: {
  fetchLimit: number;
  setFetchLimit: (n: number) => void;
  estCost: string;
  isFetching: boolean;
  onFetch: () => void;
  hasPageId: boolean;
}) {
  return (
    <div className="flex items-center gap-2">
      <select
        value={props.fetchLimit}
        onChange={(e) => props.setFetchLimit(Number(e.target.value))}
        disabled={props.isFetching}
        className="px-2 py-1.5 rounded-lg bg-[var(--surface-2)] text-[var(--text)] text-[11px] border border-[var(--border)]"
      >
        {FETCH_LIMIT_OPTIONS.map((n) => (
          <option key={n} value={n}>
            {n} ads (~${(n * 0.005).toFixed(2)})
          </option>
        ))}
      </select>
      <button
        onClick={props.onFetch}
        disabled={props.isFetching}
        className="px-3 py-1.5 rounded-lg bg-emerald-500/15 text-emerald-400 text-[11px] font-medium hover:bg-emerald-500/25 transition-colors disabled:opacity-40 flex items-center gap-1.5"
      >
        {props.isFetching && <LoadingSpinner size="sm" />}
        {props.isFetching ? "Fetching..." : "Fetch Ads"}
      </button>
      {props.hasPageId && (
        <a
          href={`https://www.facebook.com/ads/library/?active_status=active&ad_type=all&country=ALL&view_all_page_id=`}
          target="_blank"
          rel="noopener noreferrer"
          className="px-3 py-1.5 rounded-lg bg-blue-500/15 text-blue-400 text-[11px] font-medium hover:bg-blue-500/25 transition-colors"
        >
          View in Ad Library
        </a>
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

  let msg = "";
  if (state.phase === "starting") msg = "Starting scraper...";
  else if (state.phase === "polling") {
    msg = `Scraping up to ${state.limit} ads (~$${state.cost.toFixed(3)}) — checking every 10s...`;
  } else if (state.phase === "done") msg = state.message;
  else if (state.phase === "error") msg = state.message;

  return (
    <div className={`px-3 py-2 rounded-lg border text-xs ${colors[state.phase]}`}>
      {state.phase === "polling" && (
        <span className="inline-block mr-1.5 animate-pulse">●</span>
      )}
      {msg}
    </div>
  );
}

function Pagination(props: {
  page: number;
  totalPages: number;
  setPage: (fn: (p: number) => number) => void;
}) {
  return (
    <div className="flex items-center justify-center gap-3 pt-2">
      <button
        onClick={() => props.setPage((p) => Math.max(1, p - 1))}
        disabled={props.page === 1}
        className="px-3 py-1 rounded bg-[var(--surface-2)] text-[var(--muted)] text-xs disabled:opacity-30"
      >
        Previous
      </button>
      <span className="text-xs text-[var(--muted)]">
        {props.page} / {props.totalPages}
      </span>
      <button
        onClick={() => props.setPage((p) => Math.min(props.totalPages, p + 1))}
        disabled={props.page === props.totalPages}
        className="px-3 py-1 rounded bg-[var(--surface-2)] text-[var(--muted)] text-xs disabled:opacity-30"
      >
        Next
      </button>
    </div>
  );
}
