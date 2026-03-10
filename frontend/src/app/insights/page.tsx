"use client";

import { useQuery } from "@tanstack/react-query";
import { fetchData } from "@/lib/api";
import { useAccountContext } from "@/contexts/AccountContext";
import { PageHeader } from "@/components/common/PageHeader";
import { Card } from "@/components/common/Card";
import { EmptyState } from "@/components/common/EmptyState";
import { PageLoader } from "@/components/common/LoadingSpinner";
import { StatusBadge } from "@/components/common/StatusBadge";
import { formatRelative } from "@/lib/utils";
import type { Insight } from "@/lib/types";

export default function InsightsPage() {
  const { currentAccount } = useAccountContext();

  const { data, isLoading } = useQuery({
    queryKey: ["insights", currentAccount?.id],
    queryFn: () => fetchData<{ data: Insight[] }>("/insights"),
    enabled: !!currentAccount,
  });

  if (!currentAccount) {
    return <EmptyState title="No account selected" description="Select an account to view insights." />;
  }

  if (isLoading) return <PageLoader />;
  const insights = data?.data ?? [];

  const priorityVariant = (p: string) => {
    if (p === "critical") return "danger";
    if (p === "high") return "warning";
    if (p === "medium") return "info";
    return "muted";
  };

  return (
    <div className="flex flex-col gap-5">
      <PageHeader
        title="Insights"
        subtitle="AI-generated insights from scheduled analysis runs"
        actions={
          <span className="px-3 py-1.5 rounded-lg bg-amber-500/10 text-amber-400 text-[11px] font-medium">
            Powered by Computer
          </span>
        }
      />
      {insights.length === 0 ? (
        <EmptyState
          title="No insights yet"
          description="Insights will appear after Perplexity Computer runs scheduled analysis on your ad data."
        />
      ) : (
        <div className="flex flex-col gap-3">
          {insights.map((insight) => (
            <Card key={insight.id} className="hover:border-[var(--border-light)] transition-colors">
              <div className="flex items-start justify-between mb-2">
                <StatusBadge
                  label={insight.priority || "info"}
                  variant={priorityVariant(insight.priority || "low") as "danger" | "warning" | "info" | "muted"}
                />
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
