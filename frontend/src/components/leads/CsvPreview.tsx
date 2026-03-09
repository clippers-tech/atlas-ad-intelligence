"use client";

import { formatCurrency } from "@/lib/utils";
import { stageColor } from "@/lib/utils";

interface PreviewRow {
  email: string;
  stage: string;
  revenue: number | null;
  notes: string | null;
}

interface CsvPreviewProps {
  preview: {
    rows: PreviewRow[];
    will_update: number;
    will_create: number;
  };
  onConfirm: () => void;
  onCancel: () => void;
}

export default function CsvPreview({ preview, onConfirm, onCancel }: CsvPreviewProps) {
  const displayRows = preview.rows.slice(0, 10);

  return (
    <div className="space-y-4">
      {/* Summary Banner */}
      <div className="flex items-center gap-6 px-4 py-3 bg-gray-800/60 border border-gray-700 rounded-lg text-sm">
        <span className="text-gray-400">
          Preview{" "}
          <span className="text-gray-200 font-semibold">
            {Math.min(preview.rows.length, 10)}
          </span>{" "}
          of {preview.rows.length} rows
        </span>
        <span className="text-emerald-400">
          ✅ Will create{" "}
          <strong className="text-emerald-300">{preview.will_create}</strong> new
        </span>
        <span className="text-amber-400">
          ✏️ Will update{" "}
          <strong className="text-amber-300">{preview.will_update}</strong> existing
        </span>
      </div>

      {/* Table */}
      <div className="overflow-x-auto rounded-lg border border-gray-700">
        <table className="w-full text-sm">
          <thead>
            <tr className="bg-gray-900/60 border-b border-gray-700">
              {["Email", "Stage", "Revenue", "Notes"].map((h) => (
                <th
                  key={h}
                  className="px-3 py-2 text-left text-xs font-semibold text-gray-400 uppercase tracking-wide"
                >
                  {h}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-800">
            {displayRows.map((row, idx) => (
              <tr key={idx} className="hover:bg-gray-800/30">
                <td className="px-3 py-2 text-gray-300 font-mono text-xs">
                  {row.email}
                </td>
                <td className="px-3 py-2">
                  <span
                    className={`px-2 py-0.5 rounded-full text-xs font-medium ${stageColor(row.stage)}`}
                  >
                    {row.stage}
                  </span>
                </td>
                <td className="px-3 py-2 text-gray-300">
                  {row.revenue != null ? formatCurrency(row.revenue) : "—"}
                </td>
                <td className="px-3 py-2 text-gray-500 text-xs max-w-[160px] truncate">
                  {row.notes ?? "—"}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Actions */}
      <div className="flex items-center gap-3 pt-1">
        <button
          onClick={onConfirm}
          className="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white text-sm font-medium rounded-lg transition-colors"
        >
          Confirm Import
        </button>
        <button
          onClick={onCancel}
          className="px-4 py-2 bg-gray-700 hover:bg-gray-600 text-gray-300 text-sm rounded-lg transition-colors"
        >
          Cancel
        </button>
      </div>
    </div>
  );
}
