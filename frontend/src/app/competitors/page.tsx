"use client";

import { useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { fetchData, postData, deleteData } from "@/lib/api";
import { useAccountContext } from "@/contexts/AccountContext";
import { PageHeader } from "@/components/common/PageHeader";
import { Card } from "@/components/common/Card";
import { EmptyState } from "@/components/common/EmptyState";
import { PageLoader } from "@/components/common/LoadingSpinner";
import AddCompetitorForm from "@/components/competitors/AddCompetitorForm";
import CompetitorCard from "@/components/competitors/CompetitorCard";
import CompetitorDetail from "@/components/competitors/CompetitorDetail";
import type { Competitor } from "@/lib/types";

export default function CompetitorsPage() {
  const { currentAccount, isLoading: accountLoading } = useAccountContext();
  const [showForm, setShowForm] = useState(false);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const queryClient = useQueryClient();

  const { data, isLoading } = useQuery({
    queryKey: ["competitors", currentAccount?.id],
    queryFn: () => fetchData<{ data: Competitor[] }>("/competitors"),
    enabled: !!currentAccount,
  });

  if (accountLoading) return <PageLoader />;
  if (!currentAccount) {
    return (
      <EmptyState
        title="No account selected"
        description="Select an account to view competitor intel."
      />
    );
  }
  if (isLoading) return <PageLoader />;

  const competitors = data?.data ?? [];
  const selected = competitors.find((c) => c.id === selectedId);

  const handleAdd = async (formData: {
    competitor_name: string;
    meta_page_id?: string;
    website_url?: string;
  }) => {
    await postData("/competitors", {
      competitor_name: formData.competitor_name,
      meta_page_id: formData.meta_page_id || null,
      website_url: formData.website_url || null,
    });
    queryClient.invalidateQueries({ queryKey: ["competitors"] });
    setShowForm(false);
  };

  const handleDelete = async (id: string) => {
    await deleteData(`/competitors/${id}`);
    if (selectedId === id) setSelectedId(null);
    queryClient.invalidateQueries({ queryKey: ["competitors"] });
  };

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
          <AddCompetitorForm onSubmit={handleAdd} onCancel={() => setShowForm(false)} />
        </Card>
      )}

      {competitors.length === 0 && !showForm ? (
        <EmptyState
          title="No competitors tracked"
          description="Add competitors to monitor their Meta ad activity and creative strategies."
        />
      ) : (
        <div className="flex flex-col lg:flex-row gap-5">
          {/* Left panel: competitor cards */}
          <div className="w-full lg:w-80 flex-shrink-0 space-y-3">
            {competitors.map((comp) => (
              <CompetitorCard
                key={comp.id}
                competitor={comp}
                isSelected={selectedId === comp.id}
                onSelect={() => setSelectedId(comp.id)}
                onDelete={() => handleDelete(comp.id)}
              />
            ))}
          </div>

          {/* Right panel: selected competitor details */}
          <div className="flex-1 min-w-0">
            {selected ? (
              <CompetitorDetail competitor={selected} />
            ) : (
              <Card className="flex items-center justify-center min-h-[300px]">
                <p className="text-[var(--muted)] text-sm">
                  Select a competitor to view their ads
                </p>
              </Card>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
