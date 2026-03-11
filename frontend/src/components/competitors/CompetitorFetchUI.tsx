"use client";

import { LoadingSpinner } from "@/components/common/LoadingSpinner";
import type { Competitor } from "@/lib/types";

type FetchState =
  | { phase: "idle" }
  | { phase: "starting" }
  | { phase: "polling"; runId: string; limit: number; cost: number }
  | { phase: "done"; message: string }
  | { phase: "error"; message: string };

export type { FetchState };

const FETCH_LIMIT_OPTIONS = [10, 25, 50];

export function ScraperConfigBadges({ competitor }: { competitor: Competitor }) {
  const badges: string[] = [];
  if (competitor.scraper_country && competitor.scraper_country !== "ALL") {
    badges.push(competitor.scraper_country);
  }
  if (competitor.scraper_media_type && competitor.scraper_media_type !== "all") {
    badges.push(competitor.scraper_media_type);
  }
  if (competitor.scraper_platforms) {
    badges.push(competitor.scraper_platforms.replace(/,/g, " + "));
  }
  if (competitor.scraper_language) {
    badges.push(competitor.scraper_language.toUpperCase());
  }
  if (competitor.facebook_url) {
    badges.push("FB Page URL");
  }
  if (!badges.length) return null;

  return (
    <div className="flex flex-wrap gap-1 mt-1">
      {badges.map((b) => (
        <span key={b}
          className="px-1.5 py-0.5 rounded text-[10px] bg-[var(--surface-2)] text-[var(--muted)] border border-[var(--border)]">
          {b}
        </span>
      ))}
    </div>
  );
}

export function FetchControls(props: {
  fetchLimit: number;
  setFetchLimit: (n: number) => void;
  isFetching: boolean;
  onFetch: () => void;
  pageId: string | null;
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
      {props.pageId && (
        <a
          href={`https://www.facebook.com/ads/library/?active_status=active&ad_type=all&country=ALL&view_all_page_id=${props.pageId}`}
          target="_blank" rel="noopener noreferrer"
          className="px-3 py-1.5 rounded-lg bg-blue-500/15 text-blue-400 text-[11px] font-medium hover:bg-blue-500/25 transition-colors"
        >
          View in Ad Library
        </a>
      )}
    </div>
  );
}

export function FetchStatusBar({ state }: { state: FetchState }) {
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

export function Pagination(props: {
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
