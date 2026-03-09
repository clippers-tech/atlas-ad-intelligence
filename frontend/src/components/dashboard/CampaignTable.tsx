"use client";

import { useState } from "react";
import { StatusBadge } from "@/components/common/StatusBadge";
import {
  formatCurrency,
  formatNumber,
  formatRoas,
} from "@/lib/utils";
import type { CampaignRow } from "@/lib/types";

interface CampaignTableProps {
  campaigns: CampaignRow[];
  targetCpl: number | null;
}

type SortKey = keyof CampaignRow;

function getRowClass(cpl: number, target: number | null): string {
  if (!target) return "";
  if (cpl < target) return "bg-emerald-950/20";
  if (cpl > target * 2) return "bg-red-950/20";
  return "";
}

const COLS: { key: SortKey; label: string }[] = [
  { key: "name", label: "Campaign" },
  { key: "status", label: "Status" },
  { key: "spend", label: "Spend" },
  { key: "leads", label: "Leads" },
  { key: "cpl", label: "CPL" },
  { key: "bookings", label: "Bookings" },
  { key: "calls", label: "Calls" },
  { key: "closes", label: "Closes" },
  { key: "revenue", label: "Revenue" },
  { key: "roas", label: "ROAS" },
];

export function CampaignTable({ campaigns, targetCpl }: CampaignTableProps) {
  const [sortKey, setSortKey] = useState<SortKey>("spend");
  const [sortDir, setSortDir] = useState<"asc" | "desc">("desc");

  function handleSort(key: SortKey) {
    if (key === sortKey) {
      setSortDir((d) => (d === "asc" ? "desc" : "asc"));
    } else {
      setSortKey(key);
      setSortDir("desc");
    }
  }

  const sorted = [...campaigns].sort((a, b) => {
    const av = a[sortKey];
    const bv = b[sortKey];
    if (typeof av === "string" && typeof bv === "string") {
      return sortDir === "asc"
        ? av.localeCompare(bv)
        : bv.localeCompare(av);
    }
    if (typeof av === "number" && typeof bv === "number") {
      return sortDir === "asc" ? av - bv : bv - av;
    }
    return 0;
  });

  return (
    <div className="bg-[#141414] border border-[#262626] rounded-xl overflow-hidden">
      <div className="px-6 py-4 border-b border-[#262626]">
        <h3 className="text-sm font-semibold text-white">Campaigns</h3>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="bg-[#1a1a1a] border-b border-[#262626]">
              {COLS.map((col) => (
                <th
                  key={col.key}
                  onClick={() => handleSort(col.key)}
                  className="px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider cursor-pointer whitespace-nowrap select-none hover:text-gray-200 transition-colors"
                >
                  {col.label}
                  <span className="ml-1 text-gray-600">
                    {sortKey === col.key
                      ? sortDir === "asc"
                        ? "↑"
                        : "↓"
                      : "⇅"}
                  </span>
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-[#262626]">
            {sorted.length === 0 ? (
              <tr>
                <td
                  colSpan={COLS.length}
                  className="px-4 py-8 text-center text-gray-500"
                >
                  No campaigns
                </td>
              </tr>
            ) : (
              sorted.map((row) => (
                <tr
                  key={row.id}
                  className={`hover:bg-[#1e1e1e] transition-colors ${getRowClass(row.cpl, targetCpl)}`}
                >
                  <td className="px-4 py-3 text-gray-200 font-medium max-w-[200px] truncate">
                    {row.name}
                  </td>
                  <td className="px-4 py-3">
                    <StatusBadge status={row.status} size="sm" />
                  </td>
                  <td className="px-4 py-3 text-gray-300 tabular-nums">
                    {formatCurrency(row.spend)}
                  </td>
                  <td className="px-4 py-3 text-gray-300 tabular-nums">
                    {formatNumber(row.leads)}
                  </td>
                  <td className="px-4 py-3 tabular-nums">
                    <span
                      className={
                        targetCpl
                          ? row.cpl < targetCpl
                            ? "text-emerald-400"
                            : row.cpl > targetCpl * 2
                            ? "text-red-400"
                            : "text-amber-400"
                          : "text-gray-300"
                      }
                    >
                      {formatCurrency(row.cpl)}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-gray-300 tabular-nums">
                    {formatNumber(row.bookings)}
                  </td>
                  <td className="px-4 py-3 text-gray-300 tabular-nums">
                    {formatNumber(row.calls)}
                  </td>
                  <td className="px-4 py-3 text-gray-300 tabular-nums">
                    {formatNumber(row.closes)}
                  </td>
                  <td className="px-4 py-3 text-gray-300 tabular-nums">
                    {formatCurrency(row.revenue)}
                  </td>
                  <td className="px-4 py-3 tabular-nums">
                    <span
                      className={
                        row.roas >= 3
                          ? "text-emerald-400"
                          : row.roas < 1
                          ? "text-red-400"
                          : "text-gray-300"
                      }
                    >
                      {formatRoas(row.roas)}
                    </span>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
