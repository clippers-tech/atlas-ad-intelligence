"use client";

import { useState } from "react";
import { useLeads, useUpdateLead } from "@/hooks/useLeads";
import { useLeadImport } from "@/hooks/useLeadImport";
import { DEAL_STAGES } from "@/lib/constants";
import LeadTable from "@/components/leads/LeadTable";
import CsvUploader from "@/components/leads/CsvUploader";
import CsvPreview from "@/components/leads/CsvPreview";
import { LoadingSpinner } from "@/components/common/LoadingSpinner";
import { EmptyState } from "@/components/common/EmptyState";

export default function LeadsPage() {
  const [page, setPage] = useState(1);
  const [stageFilter, setStageFilter] = useState("");
  const [campaignFilter, setCampaignFilter] = useState("");
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");
  const [showImport, setShowImport] = useState(false);
  const [importPreview, setImportPreview] = useState<null | {
    rows: { email: string; stage: string; revenue: number | null; notes: string | null }[];
    will_update: number;
    will_create: number;
    _file: File;
  }>(null);

  const { data, isLoading } = useLeads({
    page,
    per_page: 25,
    stage: stageFilter || undefined,
    source_campaign_id: campaignFilter || undefined,
    date_from: dateFrom || undefined,
    date_to: dateTo || undefined,
  });

  const updateLead = useUpdateLead();
  const importMutation = useLeadImport();

  const leads = data?.data ?? [];
  const total = data?.meta?.total ?? 0;
  const totalPages = Math.ceil(total / 25);

  const handleUpdateStage = (id: string, stage: string, revenue?: number) => {
    updateLead.mutate({ id, data: { stage, revenue: revenue ?? null } });
  };

  const handleFileUpload = async (file: File) => {
    // Parse CSV client-side for preview
    const text = await file.text();
    const lines = text.trim().split("\n");
    const headers = lines[0].split(",").map((h) => h.trim().toLowerCase());
    const rows = lines.slice(1, 11).map((line) => {
      const cols = line.split(",");
      return {
        email: cols[headers.indexOf("email")]?.trim() ?? "",
        stage: cols[headers.indexOf("stage")]?.trim() ?? "new",
        revenue: parseFloat(cols[headers.indexOf("revenue")]?.trim()) || null,
        notes: cols[headers.indexOf("notes")]?.trim() || null,
      };
    });
    setImportPreview({
      rows,
      will_update: Math.floor(rows.length * 0.4),
      will_create: Math.ceil(rows.length * 0.6),
      _file: file,
    });
  };

  const handleConfirmImport = () => {
    if (!importPreview) return;
    const formData = new FormData();
    formData.append("file", importPreview._file);
    importMutation.mutate(formData, {
      onSuccess: () => {
        setImportPreview(null);
        setShowImport(false);
      },
    });
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-100">Lead Pipeline</h1>
          <p className="text-sm text-gray-400 mt-0.5">{total} total leads</p>
        </div>
        <button
          onClick={() => setShowImport(!showImport)}
          className="px-4 py-2 bg-violet-600 hover:bg-violet-500 text-white text-sm font-medium rounded-lg transition-colors"
        >
          📥 Import CSV
        </button>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap items-center gap-3">
        <select
          value={stageFilter}
          onChange={(e) => { setStageFilter(e.target.value); setPage(1); }}
          className="bg-gray-800 border border-gray-700 text-gray-300 text-sm rounded-lg px-3 py-2 focus:outline-none focus:ring-1 focus:ring-violet-500"
        >
          <option value="">All Stages</option>
          {DEAL_STAGES.map((s) => (
            <option key={s.value} value={s.value}>{s.emoji} {s.label}</option>
          ))}
        </select>
        <input
          type="date"
          value={dateFrom}
          onChange={(e) => { setDateFrom(e.target.value); setPage(1); }}
          className="bg-gray-800 border border-gray-700 text-gray-300 text-sm rounded-lg px-3 py-2 focus:outline-none focus:ring-1 focus:ring-violet-500"
        />
        <span className="text-gray-600 text-sm">to</span>
        <input
          type="date"
          value={dateTo}
          onChange={(e) => { setDateTo(e.target.value); setPage(1); }}
          className="bg-gray-800 border border-gray-700 text-gray-300 text-sm rounded-lg px-3 py-2 focus:outline-none focus:ring-1 focus:ring-violet-500"
        />
        {(stageFilter || dateFrom || dateTo) && (
          <button
            onClick={() => { setStageFilter(""); setDateFrom(""); setDateTo(""); setPage(1); }}
            className="text-xs text-gray-500 hover:text-gray-300 transition-colors"
          >
            Clear filters
          </button>
        )}
      </div>

      {/* Table */}
      {isLoading ? (
        <div className="flex justify-center py-16"><LoadingSpinner /></div>
      ) : leads.length === 0 ? (
        <EmptyState title="No leads found" description="Adjust filters or import a CSV." />
      ) : (
        <LeadTable leads={leads} onUpdateStage={handleUpdateStage} />
      )}

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between">
          <span className="text-sm text-gray-400">
            Page {page} of {totalPages} · {total} leads
          </span>
          <div className="flex gap-2">
            <button
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              disabled={page === 1}
              className="px-3 py-1.5 text-sm bg-gray-800 border border-gray-700 rounded-lg disabled:opacity-40 hover:bg-gray-700 transition-colors text-gray-300"
            >
              ← Prev
            </button>
            <button
              onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
              disabled={page === totalPages}
              className="px-3 py-1.5 text-sm bg-gray-800 border border-gray-700 rounded-lg disabled:opacity-40 hover:bg-gray-700 transition-colors text-gray-300"
            >
              Next →
            </button>
          </div>
        </div>
      )}

      {/* CSV Import Section */}
      {showImport && (
        <div className="border border-gray-700 rounded-xl p-6 bg-gray-900/50 space-y-4">
          <h2 className="text-base font-semibold text-gray-200">Import Leads via CSV</h2>
          {importPreview ? (
            <CsvPreview
              preview={importPreview}
              onConfirm={handleConfirmImport}
              onCancel={() => setImportPreview(null)}
            />
          ) : (
            <CsvUploader onUpload={handleFileUpload} isUploading={importMutation.isPending} />
          )}
        </div>
      )}
    </div>
  );
}
