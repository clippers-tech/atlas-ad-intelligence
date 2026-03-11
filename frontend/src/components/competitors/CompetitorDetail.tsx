"use client";

import { useState, useEffect, useRef } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { fetchData, postData } from "@/lib/api";
import { PageLoader } from "@/components/common/LoadingSpinner";
import CompetitorAdGallery from "@/components/competitors/CompetitorAdGallery";
import {
  ScraperConfigBadges,
  FetchControls,
  FetchStatusBar,
  Pagination,
  type FetchState,
} from "@/components/competitors/CompetitorFetchUI";
import type { Competitor, CompetitorAd } from "@/lib/types";

interface Props {
  competitor: Competitor;
}

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
    if (!competitor.meta_page_id && !competitor.facebook_url) {
      setFetchState({ phase: "error", message: "No Page ID or Facebook URL configured." });
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
        phase: "polling", runId,
        limit: res.results_limit, cost: res.estimated_cost,
      });

      pollRef.current = setInterval(async () => {
        try {
          const status = await fetchData<{
            status: string;
            new_ads_found?: number;
            updated?: number;
            error?: string;
          }>(`/competitors/${competitor.id}/fetch-status`, {
            run_id: runId, max_ads: fetchLimit,
          });

          if (status.status === "completed") {
            if (pollRef.current) clearInterval(pollRef.current);
            const msg = `Done — ${status.new_ads_found ?? 0} new, ${status.updated ?? 0} updated.`;
            setFetchState({ phase: "done", message: msg });
            queryClient.invalidateQueries({ queryKey: ["competitor-ads"] });
            queryClient.invalidateQueries({ queryKey: ["competitors"] });
          } else if (status.status === "failed") {
            if (pollRef.current) clearInterval(pollRef.current);
            setFetchState({ phase: "error", message: status.error || "Scraper failed." });
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
          <ScraperConfigBadges competitor={competitor} />
        </div>
        <FetchControls
          fetchLimit={fetchLimit}
          setFetchLimit={setFetchLimit}
          isFetching={isFetching}
          onFetch={handleFetch}
          pageId={competitor.meta_page_id}
        />
      </div>

      {fetchState.phase !== "idle" && <FetchStatusBar state={fetchState} />}

      {isLoading ? <PageLoader /> : <CompetitorAdGallery ads={ads} />}

      {totalPages > 1 && (
        <Pagination page={page} totalPages={totalPages} setPage={setPage} />
      )}
    </div>
  );
}
