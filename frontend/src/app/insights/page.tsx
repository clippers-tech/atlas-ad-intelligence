"use client";

import { useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { fetchData, postData } from "@/lib/api";
import { useAccountContext } from "@/contexts/AccountContext";
import { PageHeader } from "@/components/common/PageHeader";
import { Card } from "@/components/common/Card";
import { EmptyState } from "@/components/common/EmptyState";
import { PageLoader } from "@/components/common/LoadingSpinner";
import { StatusBadge } from "@/components/common/StatusBadge";
import { formatRelative } from "@/lib/utils";
import type { Insight } from "@/lib/types";

type InsightFilter = "all" | "performance" | "competitor" | "creative" | "budget";
const FILTERS: { label: string; value: InsightFilter }[] = [
  { label: "All", value: "all" },
  { label: "Performance", value: "performance" },
  { label: "Competitor", value: "competitor" },
  { label: "Creative", value: "creative" },
  { label: "Budget", value: "budget" },
];

const priorityVariant = (p: string) => {
  if (p === "critical") return "danger" as const;
  if (p === "high") return "warning" as const;
  if (p === "medium") return "info" as const;
  return "muted" as const;
};

const typeIcon = (t: string) => {
  if (t === "performance") return "📊";
  if (t === "competitor") return "🔍";
  if (t === "creative") return "🎨";
  if (t === "budget") return "💰";
  if (t === "kill") return "🔴";
  if (t === "scale") return "🟢";
  return "💡";
};

export default function InsightsPage() {
  const { currentAccount, isLoading: accountLoading } = useAccountContext();
  const [filter, setFilter] = useState<InsightFilter>("all");
  const [generating, setGenerating] = useState(false);
  const queryClient = useQueryClient();

  const { data, isLoading } = useQuery({
    queryKey: ["insights", currentAccount?.id],
    queryFn: () => fetchData<{ data: Insight[] }>("/insights"),
    enabled: !!currentAccount,
    refetchInterval: 30_000,
  });

  if (accountLoading) return <PageLoader />;
  if (!currentAccount) {
    return <EmptyState title="No account selected" description="Select an account to view insights." />;
  }
  if (isLoading) return <PageLoader />;

  const insights = data?.data ?? [];
  const filtered = filter === "all"
    ? insights
    : insights.filter((i) => i.type === filter);

  const handleGenerate = async () => {
    setGenerating(true);
    try {
      await postData("/insights/trigger", {
        account_id: currentAccount.id,
      });
      // Refresh after a short delay to allow generation
      setTimeout(() => {
        queryClient.invalidateQueries({ queryKey: ["insights"] });
        setGenerating(false);
      }, 3000);
    } catch {
      setGenerating(false);
    }
  };

  return (
    <div className="flex flex-col gap-5">
      <PageHeader
        title="Insights"
        subtitle="AI-powered analysis of your ads and competitors"
        actions={
          <button
            onClick={handleGenerate}
            disabled={generating}
            className={`px-3 py-1.5 rounded-lg text-[12px] font-medium transition-colors ${
              generating
                ? "bg-amber-500/10 text-amber-400/50 cursor-wait"
                : "bg-amber-500/15 text-amber-400 hover:bg-amber-500/25"
            }`}
          >
            {generating ? "Generating..." : "Generate Insights"}
          </button>
        }
      />

      {/* Filter tabs */}
      <div className="flex items-center gap-2">
        {FILTERS.map((f) => (
          <button
            key={f.value}
            onClick={() => setFilter(f.value)}
            className={`px-3.5 py-1.5 rounded-lg text-[13px] font-medium transition-colors ${
              filter === f.value
                ? "bg-[var(--accent)] text-white"
                : "bg-[var(--surface-2)] text-[var(--muted)] hover:text-[var(--text)]"
            }`}
          >
            {f.label}
          </button>
        ))}
      </div>

      {filtered.length === 0 ? (
        <EmptyState
          title="No insights yet"
          description={
            filter === "all"
              ? "Click 'Generate Insights' to run AI analysis on your ad performance and competitor data."
              : `No ${filter} insights found. Try generating fresh insights.`
          }
        />
      ) : (
        <div className="flex flex-col gap-3">
          {filtered.map((insight) => (
            <Card key={insight.id} className="hover:border-[var(--border-light)] transition-colors">
              <div className="flex items-start justify-between mb-2">
                <div className="flex items-center gap-2">
                  <span className="text-sm">{typeIcon(insight.type)}</span>
                  <StatusBadge
                    label={insight.priority || "info"}
                    variant={priorityVariant(insight.priority || "low")}
                  />
                  <span className="text-[11px] text-[var(--muted)] bg-[var(--surface-2)] px-2 py-0.5 rounded-md">
                    {insight.type}
                  </span>
                </div>
                <span className="text-[11px] text-[var(--muted)]">
                  {insight.created_at ? formatRelative(insight.created_at) : ""}
                </span>
              </div>
              <h4 className="text-[13px] font-semibold text-[var(--text)] mb-1">
                {insight.title}
              </h4>
              <p className="text-[12px] text-[var(--text-secondary)] leading-relaxed">
                {insight.summary}
              </p>
              {insight.recommendation && (
                <div className="mt-3 p-3 rounded-lg bg-amber-500/8 border border-amber-500/15">
                  <p className="text-[11px] font-medium text-amber-400 mb-0.5">Recommendation</p>
                  <p className="text-[12px] text-[var(--text-secondary)]">{insight.recommendation}</p>
                </div>
              )}
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
