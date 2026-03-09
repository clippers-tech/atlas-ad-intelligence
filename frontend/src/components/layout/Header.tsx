"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import AccountSwitcher from "./AccountSwitcher";
import { fetchData } from "@/lib/api";
import type { HealthStatus } from "@/lib/types";

const RANGES = ["Today", "7 Days", "30 Days", "Custom"] as const;

export default function Header() {
  const [range, setRange] = useState<string>("7 Days");

  const { data: health } = useQuery({
    queryKey: ["health"],
    queryFn: () => fetchData<HealthStatus>("/health"),
    refetchInterval: 60000,
  });

  const statusDot = !health
    ? "🟡"
    : health.status === "healthy"
      ? "🟢"
      : health.status === "degraded"
        ? "🟡"
        : "🔴";

  const statusText = !health
    ? "Connecting..."
    : health.status === "healthy"
      ? "All systems running"
      : health.status === "degraded"
        ? "Warning"
        : "Critical";

  return (
    <header className="h-14 bg-[#0f0f0f] border-b border-[#262626] flex items-center justify-between px-4 fixed top-0 left-56 right-0 z-20">
      <div className="flex items-center gap-4">
        <div className="flex items-center gap-1.5 text-xs text-gray-400">
          <span>{statusDot}</span>
          <span>{statusText}</span>
        </div>
      </div>
      <div className="flex items-center gap-3">
        <div className="flex gap-1 bg-[#1a1a1a] rounded-md p-0.5">
          {RANGES.map((r) => (
            <button
              key={r}
              onClick={() => setRange(r)}
              className={`px-2.5 py-1 text-xs rounded transition-colors ${
                range === r ? "bg-white/10 text-white" : "text-gray-500 hover:text-gray-300"
              }`}
            >
              {r}
            </button>
          ))}
        </div>
        <AccountSwitcher />
      </div>
    </header>
  );
}
