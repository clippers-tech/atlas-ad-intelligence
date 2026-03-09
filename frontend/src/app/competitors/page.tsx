"use client";

import { useState } from "react";
import {
  useCompetitors,
  useCompetitorAds,
  useAddCompetitor,
  useDeleteCompetitor,
} from "@/hooks/useCompetitors";
import type { Competitor } from "@/lib/types";
import CompetitorCard from "@/components/competitors/CompetitorCard";
import CompetitorAdGallery from "@/components/competitors/CompetitorAdGallery";
import CompetitorAlerts from "@/components/competitors/CompetitorAlerts";
import AddCompetitorForm from "@/components/competitors/AddCompetitorForm";
import { ConfirmDialog } from "@/components/common/ConfirmDialog";
import { LoadingSpinner } from "@/components/common/LoadingSpinner";
import { EmptyState } from "@/components/common/EmptyState";

export default function CompetitorsPage() {
  const { data: competitors = [], isLoading } = useCompetitors();
  const addCompetitor = useAddCompetitor();
  const deleteCompetitor = useDeleteCompetitor();

  const [selected, setSelected] = useState<Competitor | null>(null);
  const [showAddForm, setShowAddForm] = useState(false);
  const [deleteTarget, setDeleteTarget] = useState<Competitor | null>(null);

  const { data: ads = [], isLoading: adsLoading } = useCompetitorAds(
    selected?.id ?? null
  );

  const handleAdd = (data: {
    competitor_name: string;
    meta_page_id?: string;
    website_url?: string;
  }) => {
    addCompetitor.mutate(data, {
      onSuccess: () => setShowAddForm(false),
    });
  };

  const handleDelete = () => {
    if (!deleteTarget) return;
    deleteCompetitor.mutate(deleteTarget.id, {
      onSuccess: () => {
        setDeleteTarget(null);
        if (selected?.id === deleteTarget.id) setSelected(null);
      },
    });
  };

  // Mock alerts (would come from dedicated endpoint)
  const mockAlerts: { type: string; message: string; timestamp: string }[] = [];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-100">Competitor Intelligence</h1>
          <p className="text-sm text-gray-400 mt-0.5">
            Track competitor ad activity and creative strategies.
          </p>
        </div>
        <button
          onClick={() => setShowAddForm(true)}
          className="px-4 py-2 bg-violet-600 hover:bg-violet-500 text-white text-sm font-medium rounded-lg transition-colors"
        >
          + Add Competitor
        </button>
      </div>

      {/* Alerts */}
      <CompetitorAlerts alerts={mockAlerts} />

      {/* Add Form Modal */}
      {showAddForm && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4">
          <div className="bg-gray-900 border border-gray-700 rounded-xl p-6 w-full max-w-md shadow-xl">
            <h2 className="text-base font-semibold text-gray-200 mb-5">
              Add Competitor
            </h2>
            <AddCompetitorForm
              onSubmit={handleAdd}
              onCancel={() => setShowAddForm(false)}
            />
          </div>
        </div>
      )}

      {/* Main content */}
      {isLoading ? (
        <div className="flex justify-center py-16">
          <LoadingSpinner />
        </div>
      ) : competitors.length === 0 ? (
        <EmptyState
          title="No competitors tracked"
          description="Add a competitor to start monitoring their ad activity."
          action={
            <button
              onClick={() => setShowAddForm(true)}
              className="px-4 py-2 bg-violet-600 hover:bg-violet-500 text-white text-sm font-medium rounded-lg transition-colors"
            >
              + Add First Competitor
            </button>
          }
        />
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Competitor list */}
          <div className="lg:col-span-1 space-y-3">
            {competitors.map((c) => (
              <CompetitorCard
                key={c.id}
                competitor={c}
                onSelect={setSelected}
                onDelete={(id) => setDeleteTarget(competitors.find((x) => x.id === id) ?? null)}
                isSelected={selected?.id === c.id}
              />
            ))}
          </div>

          {/* Ad gallery */}
          <div className="lg:col-span-2">
            {selected ? (
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <h2 className="text-base font-semibold text-gray-200">
                    {selected.competitor_name} — Ads
                  </h2>
                  <span className="text-sm text-gray-500">{ads.length} ads</span>
                </div>
                {adsLoading ? (
                  <div className="flex justify-center py-12">
                    <LoadingSpinner />
                  </div>
                ) : (
                  <CompetitorAdGallery ads={ads} />
                )}
              </div>
            ) : (
              <div className="flex items-center justify-center h-48 border border-dashed border-gray-800 rounded-xl text-gray-600 text-sm">
                Select a competitor to view their ads
              </div>
            )}
          </div>
        </div>
      )}

      {/* Delete confirm */}
      <ConfirmDialog
        open={!!deleteTarget}
        title="Remove Competitor"
        description={`Remove "${deleteTarget?.competitor_name}" from tracking? This will also delete all tracked ads.`}
        confirmLabel="Remove"
        variant="danger"
        onConfirm={handleDelete}
        onCancel={() => setDeleteTarget(null)}
      />
    </div>
  );
}
