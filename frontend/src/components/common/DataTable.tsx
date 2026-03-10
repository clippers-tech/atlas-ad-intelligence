"use client";

import clsx from "clsx";

export interface Column<T> {
  key: string;
  label: string;
  align?: "left" | "right" | "center";
  render?: (row: T) => React.ReactNode;
}

interface DataTableProps<T> {
  columns: Column<T>[];
  data: T[];
  keyField: string;
  onRowClick?: (row: T) => void;
  emptyMessage?: string;
}

export function DataTable<T extends Record<string, unknown>>({
  columns, data, keyField, onRowClick, emptyMessage = "No data"
}: DataTableProps<T>) {
  if (!data.length) {
    return (
      <div className="text-center py-8 text-[12px] text-[var(--muted)]">
        {emptyMessage}
      </div>
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full">
        <thead>
          <tr className="border-b border-[var(--border)]">
            {columns.map((col) => (
              <th key={col.key} className={clsx(
                "px-4 py-2.5 text-[11px] font-semibold text-[var(--muted)] uppercase tracking-wider whitespace-nowrap",
                col.align === "right" ? "text-right" : col.align === "center" ? "text-center" : "text-left"
              )}>
                {col.label}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {data.map((row) => (
            <tr
              key={String(row[keyField])}
              onClick={() => onRowClick?.(row)}
              className={clsx(
                "border-b border-[var(--border)]/50 transition-colors",
                onRowClick
                  ? "cursor-pointer hover:bg-[var(--surface-2)]"
                  : "hover:bg-[var(--surface)]/50"
              )}
            >
              {columns.map((col) => (
                <td key={col.key} className={clsx(
                  "px-4 py-3 text-[13px]",
                  col.align === "right" ? "text-right tabular-nums" : col.align === "center" ? "text-center" : "text-left"
                )}>
                  {col.render ? col.render(row) : String(row[col.key] ?? "—")}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
