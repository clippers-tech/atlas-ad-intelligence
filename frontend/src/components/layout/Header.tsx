"use client";

import { useQuery } from "@tanstack/react-query";
import AccountSwitcher from "./AccountSwitcher";
import { fetchData } from "@/lib/api";
import { useDateRange } from "@/contexts/DateRangeContext";
import type { HealthStatus } from "@/lib/types";
import { DATE_RANGES } from "@/lib/constants";

export default function Header() {
  const { rangeKey, setRangeKey } = useDateRange();

  const { data: health } = useQuery({
    queryKey: ["health"],
    queryFn: () => fetchData<HealthStatus>("/health"),
    refetchInterval: 60000,
  });

  const statusColor = !health
    ? "bg-amber-500"
    : health.status === "healthy"
      ? "bg-emerald-500"
      : health.status === "degraded"
        ? "bg-amber-500"
        : "bg-red-500";

  const statusText = !health
    ? "Connecting..."
    : health.status === "healthy"
      ? "All systems running"
      : health.status === "degraded"
        ? "Degraded"
        : "Critical";

  return (
    <header className="h-[var(--header-height)] bg-[var(--surface)] border-b border-[var(--border)] flex items-center justify-between px-5">
      {/* Left — status */}
      <div className="flex items-center gap-3">
        <div className="flex items-center gap-2 px-2.5 py-1 rounded-md bg-[var(--surface-2)]">
          <span className={`w-1.5 h-1.5 rounded-full ${statusColor} animate-pulse`} />
          <span className="text-[11px] text-[var(--text-secondary)]">
            {statusText}
          </span>
        </div>
      </div>

      {/* Right — date range + account */}
      <div className="flex items-center gap-3">
        {/* Date range selector */}
        <div className="flex gap-0.5 bg-[var(--surface-2)] rounded-lg p-0.5">
          {DATE_RANGES.map((r) => (
            <button
              key={r.value}
              onClick={() => setRangeKey(r.value as "1d" | "7d" | "14d" | "30d" | "all")}
              className={`px-2.5 py-1 text-[12px] font-medium rounded-md transition-all duration-150 ${
                rangeKey === r.value
                  ? "bg-amber-500/15 text-amber-400"
                  : "text-[var(--muted)] hover:text-[var(--text-secondary)]"
              }`}
            >
              {r.label}
            </button>
          ))}
        </div>

        <div className="w-px h-5 bg-[var(--border)]" />

        <AccountSwitcher />
      </div>
    </header>
  );
}
