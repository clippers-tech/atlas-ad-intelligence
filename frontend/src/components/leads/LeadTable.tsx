"use client";

import { useState } from "react";
import type { Lead } from "@/lib/types";
import { formatDate, formatCurrency, truncate, stageColor } from "@/lib/utils";
import LeadStageDropdown from "./LeadStageDropdown";

interface LeadTableProps {
  leads: Lead[];
  onUpdateStage: (id: string, stage: string, revenue?: number) => void;
}

export default function LeadTable({ leads, onUpdateStage }: LeadTableProps) {
  const [pendingUpdates, setPendingUpdates] = useState<
    Record<string, { stage: string; revenue?: number }>
  >({});

  const handleStageChange = (id: string, stage: string) => {
    setPendingUpdates((prev) => ({
      ...prev,
      [id]: { ...prev[id], stage },
    }));
  };

  const handleRevenueChange = (id: string, revenue: number) => {
    setPendingUpdates((prev) => ({
      ...prev,
      [id]: { ...prev[id], revenue },
    }));
  };

  const handleUpdate = (id: string) => {
    const update = pendingUpdates[id];
    if (!update?.stage) return;
    onUpdateStage(id, update.stage, update.revenue);
    setPendingUpdates((prev) => {
      const next = { ...prev };
      delete next[id];
      return next;
    });
  };

  if (leads.length === 0) {
    return (
      <div className="text-center py-12 text-gray-500 text-sm">
        No leads found matching the current filters.
      </div>
    );
  }

  return (
    <div className="overflow-x-auto rounded-xl border border-gray-800">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-gray-800 bg-gray-900/50">
            {["Name", "Email", "Source Campaign", "Source Ad", "Stage", "Booked", "Revenue", "Actions"].map(
              (h) => (
                <th
                  key={h}
                  className="px-4 py-3 text-left text-xs font-semibold text-gray-400 uppercase tracking-wide"
                >
                  {h}
                </th>
              )
            )}
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-800">
          {leads.map((lead) => {
            const pending = pendingUpdates[lead.id];
            const displayStage = pending?.stage ?? lead.stage;
            const hasPending = !!pending?.stage && pending.stage !== lead.stage;
            return (
              <tr key={lead.id} className="hover:bg-gray-800/40 transition-colors">
                <td className="px-4 py-3 font-medium text-gray-200">
                  {lead.name ?? "—"}
                </td>
                <td className="px-4 py-3 text-gray-400">
                  {truncate(lead.email ?? "—", 28)}
                </td>
                <td className="px-4 py-3 text-gray-400">
                  {truncate(lead.source_campaign_name ?? "—", 22)}
                </td>
                <td className="px-4 py-3 text-gray-400">
                  {truncate(lead.source_ad_name ?? "—", 22)}
                </td>
                <td className="px-4 py-3">
                  <LeadStageDropdown
                    currentStage={displayStage}
                    onChange={(stage) => handleStageChange(lead.id, stage)}
                    onRevenueChange={(rev) => handleRevenueChange(lead.id, rev)}
                  />
                </td>
                <td className="px-4 py-3 text-gray-400">
                  {lead.booked_at ? formatDate(lead.booked_at) : "—"}
                </td>
                <td className="px-4 py-3 text-gray-300">
                  {lead.revenue != null ? formatCurrency(lead.revenue) : "—"}
                </td>
                <td className="px-4 py-3">
                  <button
                    onClick={() => handleUpdate(lead.id)}
                    disabled={!hasPending}
                    className="px-3 py-1 text-xs rounded-md bg-violet-600 hover:bg-violet-500 disabled:opacity-30 disabled:cursor-not-allowed text-white transition-colors"
                  >
                    Update
                  </button>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
