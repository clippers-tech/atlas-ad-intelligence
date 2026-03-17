"use client";

import AccountSwitcher from "./AccountSwitcher";
import { RefreshButton } from "@/components/common/RefreshButton";
import { DATE_RANGES } from "@/lib/constants";
import { useDateRange } from "@/contexts/DateRangeContext";

export default function Header() {
  const { rangeKey: range, setRangeKey: setRange } = useDateRange();

  return (
    <header className="h-[var(--header-height)] bg-[var(--surface)] border-b border-[var(--border)] flex items-center justify-between px-5">
      {/* Left — spacer */}
      <div />

      {/* Right — date range + account */}
      <div className="flex items-center gap-3">
        {/* Date range selector */}
        <div className="flex gap-0.5 bg-[var(--surface-2)] rounded-lg p-0.5">
          {DATE_RANGES.map((r) => (
            <button
              key={r.value}
              onClick={() => setRange(r.value as string)}
              className={`px-2.5 py-1 text-[12px] font-medium rounded-md transition-all duration-150 ${
                range === r.value
                  ? "bg-amber-500/15 text-amber-400"
                  : "text-[var(--muted)] hover:text-[var(--text-secondary)]"
              }`}
            >
              {r.label}
            </button>
          ))}
        </div>

        <div className="w-px h-5 bg-[var(--border)]" />

        <RefreshButton />

        <div className="w-px h-5 bg-[var(--border)]" />

        <AccountSwitcher />
      </div>
    </header>
  );
}
