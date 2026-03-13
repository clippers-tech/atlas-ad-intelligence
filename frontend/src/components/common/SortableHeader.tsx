"use client";

import type { SortDir } from "@/hooks/useTableSort";

interface SortableHeaderProps {
  label: string;
  sortKey: string;
  activeKey: string;
  activeDir: SortDir;
  onSort: (key: string) => void;
  className?: string;
}

/** Clickable table header cell with sort arrow indicator. */
export function SortableHeader({
  label,
  sortKey,
  activeKey,
  activeDir,
  onSort,
  className = "",
}: SortableHeaderProps) {
  const isActive = activeKey === sortKey;

  return (
    <th
      onClick={() => onSort(sortKey)}
      className={`px-3 py-2.5 text-[11px] font-semibold uppercase tracking-wider text-left whitespace-nowrap select-none cursor-pointer group transition-colors ${
        isActive
          ? "text-amber-400"
          : "text-[var(--muted)] hover:text-[var(--text-secondary)]"
      } ${className}`}
    >
      <span className="inline-flex items-center gap-1">
        {label}
        {isActive ? (
          <Arrow dir={activeDir} />
        ) : (
          <span className="opacity-0 group-hover:opacity-40 transition-opacity">
            <Arrow dir="desc" />
          </span>
        )}
      </span>
    </th>
  );
}

function Arrow({ dir }: { dir: SortDir }) {
  return (
    <svg
      width="10"
      height="10"
      viewBox="0 0 10 10"
      fill="currentColor"
      className={`transition-transform ${dir === "asc" ? "rotate-180" : ""}`}
    >
      <path d="M5 7L1.5 3h7L5 7z" />
    </svg>
  );
}
