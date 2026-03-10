"use client";

import { useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { fetchData, postData } from "@/lib/api";
import { useAccountContext } from "@/contexts/AccountContext";
import { PageHeader } from "@/components/common/PageHeader";
import { Card } from "@/components/common/Card";
import { EmptyState } from "@/components/common/EmptyState";
import { PageLoader } from "@/components/common/LoadingSpinner";
import { formatRelative } from "@/lib/utils";
import AddCompetitorForm from "@/components/competitors/AddCompetitorForm";
import type { Competitor } from "@/lib/types";

export default function CompetitorsPage() {
  const { currentAccount, isLoading: accountLoading } = useAccountContext();
  const [showForm, setShowForm] = useState(false);
  const queryClient = useQueryClient();

  const { data, isLoading } = useQuery({
    queryKey: ["competitors", currentAccount?.id],
    queryFn: () => fetchData<{ data: Competitor[] }>("/competitors"),
    enabled: !!currentAccount,
  });

  if (accountLoading) return <PageLoader />;
  if (!currentAccount) {
    return <EmptyState title="No account selected" description="Select an account to view competitor intel." />;
  }

  if (isLoading) return <PageLoader />;
  const competitors = data?.data ?? [];

  return (
    <div className="flex flex-col gap-5">
      <PageHeader
        title="Competitor Intel"
        subtitle="Track competitor ad strategies on Meta"
        actions={
          <button
            onClick={() => setShowForm(!showForm)}
            className="px-3 py-1.5 rounded-lg bg-amber-500/15 text-amber-400 text-[12px] font-medium hover:bg-amber-500/25 transition-colors"
          >
            + Add Competitor
          </button>
        }
      />
      {showForm && (
        <Card title="Add Competitor" subtitle="Track a competitor's Meta ad activity">
          <AddCompetitorForm
            onSubmit={async (formData) => {
              await postData("/competitors", {
                account_id: currentAccount.id,
                name: formData.competitor_name,
                meta_page_id: formData.meta_page_id || null,
                domain: formData.website_url || null,
              });
              queryClient.invalidateQueries({ queryKey: ["competitors"] });
              setShowForm(false);
            }}
            onCancel={() => setShowForm(false)}
          />
        </Card>
      )}
      {competitors.length === 0 && !showForm ? (
        <EmptyState
          title="No competitors tracked"
          description="Add competitors to monitor their Meta ad activity and creative strategies."
        />
      ) : competitors.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {competitors.map((comp) => (
            <Card key={comp.id} className="hover:border-[var(--border-light)] transition-colors">
              <div className="flex items-center gap-3 mb-3">
                <div className="w-10 h-10 rounded-lg bg-[var(--surface-2)] flex items-center justify-center text-[var(--muted)] text-sm font-bold">
                  {comp.name.charAt(0)}
                </div>
                <div>
                  <h4 className="text-[13px] font-semibold text-[var(--text)]">{comp.name}</h4>
                  {comp.domain && (
                    <p className="text-[11px] text-[var(--muted)]">{comp.domain}</p>
                  )}
                </div>
              </div>
              <div className="flex items-center gap-4 pt-3 border-t border-[var(--border)]/50">
                <div className="text-[11px] text-[var(--muted)]">
                  Ads tracked: <span className="text-[var(--text)] font-medium">{comp.ad_count ?? 0}</span>
                </div>
                {comp.last_scraped_at && (
                  <div className="text-[11px] text-[var(--muted)]">
                    Updated {formatRelative(comp.last_scraped_at)}
                  </div>
                )}
              </div>
            </Card>
          ))}
        </div>
      ) : null}
    </div>
  );
}
