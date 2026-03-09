"use client";

import { useReports, useGenerateReport } from "@/hooks/useReports";
import { useState } from "react";
import ReportArchive from "@/components/reports/ReportArchive";
import { LoadingSpinner } from "@/components/common/LoadingSpinner";
import { EmptyState } from "@/components/common/EmptyState";

export default function ReportsPage() {
  const { data: reports = [], isLoading } = useReports();
  const generateReport = useGenerateReport();
  const [showGenerator, setShowGenerator] = useState(false);
  const [reportType, setReportType] = useState("weekly");
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");

  const handleGenerate = () => {
    generateReport.mutate(
      {
        type: reportType,
        date_from: dateFrom || undefined,
        date_to: dateTo || undefined,
        name: `${reportType.charAt(0).toUpperCase() + reportType.slice(1)} Report`,
      },
      { onSuccess: () => setShowGenerator(false) }
    );
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-100">Reports</h1>
          <p className="text-sm text-gray-400 mt-0.5">
            Download performance reports for your accounts.
          </p>
        </div>
        <button
          onClick={() => setShowGenerator(!showGenerator)}
          className="px-4 py-2 bg-violet-600 hover:bg-violet-500 text-white text-sm font-medium rounded-lg transition-colors"
        >
          Generate Report
        </button>
      </div>

      {/* Report Generator */}
      {showGenerator && (
        <div className="border border-gray-700 rounded-xl p-5 bg-gray-900/50 space-y-4">
          <h2 className="text-sm font-semibold text-gray-300">Generate New Report</h2>
          <div className="flex flex-wrap items-end gap-4">
            <div>
              <label className="block text-xs text-gray-500 mb-1">Type</label>
              <select
                value={reportType}
                onChange={(e) => setReportType(e.target.value)}
                className="bg-gray-800 border border-gray-700 text-gray-300 text-sm rounded-lg px-3 py-2 focus:outline-none focus:ring-1 focus:ring-violet-500"
              >
                <option value="weekly">Weekly</option>
                <option value="monthly">Monthly</option>
                <option value="performance">Performance</option>
                <option value="custom">Custom</option>
              </select>
            </div>
            <div>
              <label className="block text-xs text-gray-500 mb-1">From</label>
              <input
                type="date"
                value={dateFrom}
                onChange={(e) => setDateFrom(e.target.value)}
                className="bg-gray-800 border border-gray-700 text-gray-300 text-sm rounded-lg px-3 py-2 focus:outline-none focus:ring-1 focus:ring-violet-500"
              />
            </div>
            <div>
              <label className="block text-xs text-gray-500 mb-1">To</label>
              <input
                type="date"
                value={dateTo}
                onChange={(e) => setDateTo(e.target.value)}
                className="bg-gray-800 border border-gray-700 text-gray-300 text-sm rounded-lg px-3 py-2 focus:outline-none focus:ring-1 focus:ring-violet-500"
              />
            </div>
            <div className="flex gap-2">
              <button
                onClick={handleGenerate}
                disabled={generateReport.isPending}
                className="flex items-center gap-2 px-4 py-2 bg-violet-600 hover:bg-violet-500 disabled:opacity-40 text-white text-sm font-medium rounded-lg transition-colors"
              >
                {generateReport.isPending ? <LoadingSpinner size={16} /> : null}
                {generateReport.isPending ? "Generating…" : "Generate"}
              </button>
              <button
                onClick={() => setShowGenerator(false)}
                className="px-3 py-2 bg-gray-700 hover:bg-gray-600 text-gray-300 text-sm rounded-lg transition-colors"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Reports list */}
      {isLoading ? (
        <div className="flex justify-center py-16">
          <LoadingSpinner />
        </div>
      ) : reports.length === 0 ? (
        <EmptyState
          title="No reports yet"
          description="Generate your first report to see performance data in a downloadable format."
          action={
            <button
              onClick={() => setShowGenerator(true)}
              className="px-4 py-2 bg-violet-600 hover:bg-violet-500 text-white text-sm font-medium rounded-lg transition-colors"
            >
              Generate First Report
            </button>
          }
        />
      ) : (
        <ReportArchive reports={reports} />
      )}
    </div>
  );
}
