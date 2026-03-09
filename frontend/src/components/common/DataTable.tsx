"use client";

import { ReactNode } from "react";

type SortDir = "asc" | "desc";

export interface Column<T> {
  key: string;
  label: string;
  sortable?: boolean;
  render?: (row: T) => ReactNode;
}

interface DataTableProps<T> {
  columns: Column<T>[];
  data: T[];
  onSort?: (key: string) => void;
  sortKey?: string;
  sortDir?: SortDir;
}

function SortIcon({ active, dir }: { active: boolean; dir?: SortDir }) {
  if (!active) {
    return (
      <span className="ml-1 text-gray-600 text-xs">⇅</span>
    );
  }
  return (
    <span className="ml-1 text-gray-300 text-xs">
      {dir === "asc" ? "↑" : "↓"}
    </span>
  );
}

export function DataTable<T extends Record<string, unknown>>({
  columns,
  data,
  onSort,
  sortKey,
  sortDir,
}: DataTableProps<T>) {
  return (
    <div className="w-full overflow-x-auto rounded-lg border border-[#262626]">
      <table className="w-full text-sm">
        <thead>
          <tr className="bg-[#1a1a1a] border-b border-[#262626]">
            {columns.map((col) => (
              <th
                key={col.key}
                className={[
                  "px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider whitespace-nowrap select-none",
                  col.sortable && onSort
                    ? "cursor-pointer hover:text-gray-200 transition-colors"
                    : "",
                ].join(" ")}
                onClick={() => col.sortable && onSort?.(col.key)}
              >
                <span className="inline-flex items-center">
                  {col.label}
                  {col.sortable && (
                    <SortIcon
                      active={sortKey === col.key}
                      dir={sortKey === col.key ? sortDir : undefined}
                    />
                  )}
                </span>
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-[#262626] bg-[#141414]">
          {data.length === 0 ? (
            <tr>
              <td
                colSpan={columns.length}
                className="px-4 py-8 text-center text-gray-500"
              >
                No data available
              </td>
            </tr>
          ) : (
            data.map((row, rowIdx) => (
              <tr
                key={rowIdx}
                className="hover:bg-[#1a1a1a] transition-colors"
              >
                {columns.map((col) => (
                  <td
                    key={col.key}
                    className="px-4 py-3 text-gray-300 whitespace-nowrap"
                  >
                    {col.render
                      ? col.render(row)
                      : (row[col.key] as ReactNode) ?? "—"}
                  </td>
                ))}
              </tr>
            ))
          )}
        </tbody>
      </table>
    </div>
  );
}
