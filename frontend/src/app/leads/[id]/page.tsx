"use client";

import { use } from "react";
import Link from "next/link";
import { useLeadJourney, useUpdateLead } from "@/hooks/useLeads";
import { formatCurrency, formatCurrencyDecimal, formatRelative } from "@/lib/utils";
import LeadJourneyTimeline from "@/components/leads/LeadJourneyTimeline";
import LeadStageDropdown from "@/components/leads/LeadStageDropdown";
import { LoadingSpinner } from "@/components/common/LoadingSpinner";

interface PageProps {
  params: Promise<{ id: string }>;
}

export default function LeadDetailPage({ params }: PageProps) {
  const { id } = use(params);
  const { data, isLoading, isError } = useLeadJourney(id);
  const updateLead = useUpdateLead();

  const handleStageUpdate = (stage: string, revenue?: number) => {
    updateLead.mutate({ id, data: { stage, revenue: revenue ?? null } });
  };

  if (isLoading) {
    return (
      <div className="flex justify-center py-24">
        <LoadingSpinner />
      </div>
    );
  }

  if (isError || !data) {
    return (
      <div className="text-center py-24 text-gray-400">
        <p className="text-lg">Lead not found</p>
        <Link href="/leads" className="text-violet-400 hover:text-violet-300 text-sm mt-2 inline-block">
          ← Back to Pipeline
        </Link>
      </div>
    );
  }

  const { lead, events, attribution } = data;

  return (
    <div className="space-y-6 max-w-4xl">
      {/* Back */}
      <Link
        href="/leads"
        className="inline-flex items-center gap-1.5 text-sm text-gray-400 hover:text-gray-200 transition-colors"
      >
        ← Back to Lead Pipeline
      </Link>

      {/* Lead Header */}
      <div className="bg-gray-900 border border-gray-800 rounded-xl p-6">
        <div className="flex items-start justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold text-gray-100">{lead.name ?? "Unknown Lead"}</h1>
            <div className="flex items-center gap-4 mt-2 text-sm text-gray-400">
              {lead.email && <span>📧 {lead.email}</span>}
              {lead.phone && <span>📞 {lead.phone}</span>}
              <span>Created {formatRelative(lead.created_at)}</span>
            </div>
          </div>
          <div className="text-right text-sm text-gray-500">
            <div>ID: {lead.id.slice(0, 8)}…</div>
          </div>
        </div>
      </div>

      {/* Attribution Card */}
      <div className="bg-gray-900 border border-gray-800 rounded-xl p-6">
        <h2 className="text-sm font-semibold text-gray-300 uppercase tracking-wide mb-4">
          Attribution
        </h2>
        <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
          <div>
            <p className="text-xs text-gray-500">Campaign</p>
            <p className="text-sm text-gray-200 mt-0.5">{attribution.campaign_name ?? "—"}</p>
          </div>
          <div>
            <p className="text-xs text-gray-500">Ad Set</p>
            <p className="text-sm text-gray-200 mt-0.5">{attribution.ad_set_name ?? "—"}</p>
          </div>
          <div>
            <p className="text-xs text-gray-500">Ad</p>
            <p className="text-sm text-gray-200 mt-0.5">{attribution.ad_name ?? "—"}</p>
          </div>
          <div>
            <p className="text-xs text-gray-500">UTM Campaign</p>
            <p className="text-sm text-gray-200 mt-0.5 font-mono">{attribution.utm_campaign ?? "—"}</p>
          </div>
          <div>
            <p className="text-xs text-gray-500">UTM Source</p>
            <p className="text-sm text-gray-200 mt-0.5 font-mono">{attribution.utm_source ?? "—"}</p>
          </div>
          <div>
            <p className="text-xs text-gray-500">UTM Medium</p>
            <p className="text-sm text-gray-200 mt-0.5 font-mono">{attribution.utm_medium ?? "—"}</p>
          </div>
          <div>
            <p className="text-xs text-gray-500">Cost to Acquire</p>
            <p className="text-sm text-red-400 font-semibold mt-0.5">
              {attribution.cost_to_acquire != null
                ? formatCurrencyDecimal(attribution.cost_to_acquire)
                : "—"}
            </p>
          </div>
          <div>
            <p className="text-xs text-gray-500">Revenue</p>
            <p className="text-sm text-emerald-400 font-semibold mt-0.5">
              {attribution.revenue != null ? formatCurrency(attribution.revenue) : "—"}
            </p>
          </div>
          <div>
            <p className="text-xs text-gray-500">Individual ROAS</p>
            <p className="text-sm text-violet-400 font-semibold mt-0.5">
              {attribution.individual_roas != null
                ? `${attribution.individual_roas.toFixed(2)}x`
                : "—"}
            </p>
          </div>
        </div>
      </div>

      {/* Stage Update */}
      <div className="bg-gray-900 border border-gray-800 rounded-xl p-6">
        <h2 className="text-sm font-semibold text-gray-300 uppercase tracking-wide mb-4">
          Update Stage
        </h2>
        <div className="flex items-center gap-4">
          <LeadStageDropdown
            currentStage={lead.stage}
            onChange={(stage) => handleStageUpdate(stage)}
            onRevenueChange={(rev) => handleStageUpdate(lead.stage, rev)}
          />
          <button
            onClick={() => handleStageUpdate(lead.stage)}
            disabled={updateLead.isPending}
            className="px-4 py-1.5 bg-violet-600 hover:bg-violet-500 text-white text-sm rounded-lg transition-colors disabled:opacity-40"
          >
            {updateLead.isPending ? "Saving…" : "Save"}
          </button>
        </div>
      </div>

      {/* Journey Timeline */}
      <div className="bg-gray-900 border border-gray-800 rounded-xl p-6">
        <h2 className="text-sm font-semibold text-gray-300 uppercase tracking-wide mb-6">
          Journey Timeline
        </h2>
        <LeadJourneyTimeline events={events} />
      </div>
    </div>
  );
}
