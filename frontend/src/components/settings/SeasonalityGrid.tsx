"use client";

import { useState } from "react";

interface SeasonalityConfig {
  month: number;
  budget_modifier_percent?: number;
  multiplier?: number;
  notes?: string | null;
}

interface SeasonalityGridProps {
  configs: SeasonalityConfig[];
  onSave: (updated: { month: number; multiplier: number; notes?: string | null }[]) => void;
}

const MONTHS = [
  "January", "February", "March", "April", "May", "June",
  "July", "August", "September", "October", "November", "December",
];

function toPercent(multiplier: number): string {
  // multiplier 1.0 = 0%, 1.2 = +20%, 0.8 = -20%
  return String(Math.round((multiplier - 1) * 100));
}

function toMultiplier(percent: string): number {
  const p = parseFloat(percent);
  if (isNaN(p)) return 1;
  return 1 + p / 100;
}

type RowData = { percent: string; notes: string };

export default function SeasonalityGrid({ configs, onSave }: SeasonalityGridProps) {
  const [rows, setRows] = useState<RowData[]>(() =>
    MONTHS.map((_, idx) => {
      const month = idx + 1;
      const cfg = configs.find((c) => c.month === month);
      const mult = cfg?.multiplier ?? cfg?.budget_modifier_percent
        ? (cfg?.budget_modifier_percent ?? 0) / 100 + 1
        : 1;
      return {
        percent: toPercent(typeof mult === "number" ? mult : 1),
        notes: cfg?.notes ?? "",
      };
    })
  );

  const updateRow = (idx: number, field: keyof RowData, value: string) => {
    setRows((prev) => prev.map((r, i) => (i === idx ? { ...r, [field]: value } : r)));
  };

  const handleSave = () => {
    const updated = rows.map((row, idx) => ({
      month: idx + 1,
      multiplier: toMultiplier(row.percent),
      notes: row.notes || null,
    }));
    onSave(updated);
  };

  const getRowColor = (percent: string): string => {
    const p = parseFloat(percent);
    if (isNaN(p) || p === 0) return "";
    if (p > 0) return "text-emerald-400";
    return "text-red-400";
  };

  return (
    <div className="space-y-4">
      <div className="overflow-x-auto rounded-xl border border-gray-800">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-gray-800 bg-gray-900/50">
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-400 uppercase tracking-wide">Month</th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-400 uppercase tracking-wide">Budget Modifier %</th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-400 uppercase tracking-wide">Notes</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-800">
            {MONTHS.map((month, idx) => (
              <tr key={month} className="hover:bg-gray-800/20 transition-colors">
                <td className="px-4 py-2.5 text-gray-300 font-medium w-32">{month}</td>
                <td className="px-4 py-2.5 w-40">
                  <div className="flex items-center gap-2">
                    <input
                      type="number"
                      value={rows[idx].percent}
                      onChange={(e) => updateRow(idx, "percent", e.target.value)}
                      step={5}
                      min={-90}
                      max={500}
                      className={`w-20 bg-gray-800 border border-gray-700 rounded-md px-2 py-1 text-sm text-center focus:outline-none focus:ring-1 focus:ring-violet-500 ${getRowColor(rows[idx].percent)}`}
                    />
                    <span className={`text-sm ${getRowColor(rows[idx].percent)}`}>%</span>
                  </div>
                </td>
                <td className="px-4 py-2.5">
                  <input
                    type="text"
                    value={rows[idx].notes}
                    onChange={(e) => updateRow(idx, "notes", e.target.value)}
                    placeholder="e.g. Peak season, school holidays…"
                    className="w-full bg-gray-800 border border-gray-700 text-gray-400 rounded-md px-2 py-1 text-sm focus:outline-none focus:ring-1 focus:ring-violet-500 placeholder-gray-700"
                  />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="flex items-center gap-4">
        <button
          onClick={handleSave}
          className="px-5 py-2 bg-violet-600 hover:bg-violet-500 text-white text-sm font-medium rounded-lg transition-colors"
        >
          Save All
        </button>
        <p className="text-xs text-gray-600">
          Positive % increases budget allocation, negative decreases it.
        </p>
      </div>
    </div>
  );
}
