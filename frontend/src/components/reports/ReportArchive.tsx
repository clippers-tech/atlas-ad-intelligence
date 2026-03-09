"use client";

import { formatDateTime, formatRelative } from "@/lib/utils";
import type { Report } from "@/hooks/useReports";

interface ReportArchiveProps {
  reports: Report[];
}

const STATUS_CONFIG = {
  ready: { label: "Ready", color: "text-emerald-400 bg-emerald-500/10", icon: "✅" },
  pending: { label: "Generating…", color: "text-amber-400 bg-amber-500/10", icon: "⏳" },
  failed: { label: "Failed", color: "text-red-400 bg-red-500/10", icon: "❌" },
};

const TYPE_ICONS: Record<string, string> = {
  weekly: "📅",
  monthly: "📆",
  custom: "📋",
  performance: "📊",
};

export default function ReportArchive({ reports }: ReportArchiveProps) {
  if (reports.length === 0) {
    return null; // EmptyState handled in parent
  }

  return (
    <div className="overflow-x-auto rounded-xl border border-gray-800">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-gray-800 bg-gray-900/50">
            {["Report", "Type", "Period", "Status", "Generated", "Download"].map(
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
          {reports.map((report) => {
            const statusConfig = STATUS_CONFIG[report.status];
            const typeIcon = TYPE_ICONS[report.type] ?? "📄";

            return (
              <tr key={report.id} className="hover:bg-gray-800/30 transition-colors">
                {/* Name */}
                <td className="px-4 py-3 font-medium text-gray-200">
                  <div className="flex items-center gap-2">
                    <span>{typeIcon}</span>
                    <span>{report.name}</span>
                  </div>
                </td>

                {/* Type */}
                <td className="px-4 py-3 text-gray-400 capitalize">{report.type}</td>

                {/* Period */}
                <td className="px-4 py-3 text-gray-400 text-xs font-mono">
                  {report.date_from && report.date_to
                    ? `${report.date_from} → ${report.date_to}`
                    : "—"}
                </td>

                {/* Status */}
                <td className="px-4 py-3">
                  <span
                    className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-xs font-medium ${statusConfig.color}`}
                  >
                    <span>{statusConfig.icon}</span>
                    {statusConfig.label}
                  </span>
                </td>

                {/* Generated */}
                <td className="px-4 py-3 text-gray-500 text-xs">
                  <span title={formatDateTime(report.created_at)}>
                    {formatRelative(report.created_at)}
                  </span>
                </td>

                {/* Download */}
                <td className="px-4 py-3">
                  {report.status === "ready" && report.download_url ? (
                    <a
                      href={report.download_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-gray-800 hover:bg-gray-700 text-gray-300 rounded-lg text-xs font-medium transition-colors"
                    >
                      📥 PDF
                    </a>
                  ) : (
                    <span className="text-gray-600 text-xs">—</span>
                  )}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
