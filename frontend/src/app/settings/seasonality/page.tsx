"use client";

import { useState } from "react";
import { useAccounts, useSeasonality, useUpdateSeasonality } from "@/hooks/useSettings";
import SeasonalityGrid from "@/components/settings/SeasonalityGrid";
import { LoadingSpinner } from "@/components/common/LoadingSpinner";

export default function SeasonalityPage() {
  const { data: accounts = [], isLoading: accountsLoading } = useAccounts();
  const [selectedAccountId, setSelectedAccountId] = useState<string | null>(null);

  const activeAccountId = selectedAccountId ?? accounts[0]?.id ?? null;

  const { data: seasonality = [], isLoading: seasonalityLoading } =
    useSeasonality(activeAccountId);

  const updateSeasonality = useUpdateSeasonality();

  const handleSave = (
    updated: { month: number; multiplier: number; notes?: string | null }[]
  ) => {
    if (!activeAccountId) return;
    // Save each month one by one
    updated.forEach((row) => {
      updateSeasonality.mutate({
        accountId: activeAccountId,
        data: row,
      });
    });
  };

  const isSaving = updateSeasonality.isPending;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-100">Seasonality</h1>
        <p className="text-sm text-gray-400 mt-0.5">
          Configure monthly budget modifiers to account for seasonal demand patterns.
        </p>
      </div>

      {/* Account selector */}
      {accounts.length > 1 && (
        <div className="flex items-center gap-3">
          <label className="text-sm text-gray-400">Account:</label>
          <select
            value={activeAccountId ?? ""}
            onChange={(e) => setSelectedAccountId(e.target.value || null)}
            className="bg-gray-800 border border-gray-700 text-gray-300 text-sm rounded-lg px-3 py-2 focus:outline-none focus:ring-1 focus:ring-violet-500"
          >
            {accounts.map((a) => (
              <option key={a.id} value={a.id}>
                {a.name}
              </option>
            ))}
          </select>
        </div>
      )}

      {/* Explanation card */}
      <div className="flex items-start gap-3 px-4 py-3 bg-violet-950/30 border border-violet-900/40 rounded-xl text-sm">
        <span className="text-xl mt-0.5">📅</span>
        <div>
          <p className="text-violet-300 font-medium">How modifiers work</p>
          <p className="text-violet-400/70 text-xs mt-0.5">
            A +20% modifier in December will increase the base budget by 20% for that
            month. A -30% modifier in August will reduce it by 30%. Set 0% for normal
            months.
          </p>
        </div>
      </div>

      {/* Grid */}
      {accountsLoading || seasonalityLoading ? (
        <div className="flex justify-center py-16">
          <LoadingSpinner />
        </div>
      ) : !activeAccountId ? (
        <div className="text-center py-12 text-gray-500 text-sm">
          No accounts available.
        </div>
      ) : (
        <div className="relative">
          {isSaving && (
            <div className="absolute inset-0 bg-gray-950/50 z-10 flex items-center justify-center rounded-xl">
              <div className="flex items-center gap-3 text-sm text-gray-300">
                <LoadingSpinner />
                <span>Saving…</span>
              </div>
            </div>
          )}
          <SeasonalityGrid
            configs={seasonality.map((s) => ({
              month: s.month,
              multiplier: s.multiplier,
              notes: s.notes,
            }))}
            onSave={handleSave}
          />
        </div>
      )}

      {/* Save success indicator */}
      {updateSeasonality.isSuccess && !isSaving && (
        <p className="text-sm text-emerald-400">✅ Seasonality saved successfully.</p>
      )}
    </div>
  );
}
