"use client";

import { useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import api from "@/lib/api";

export function RefreshButton() {
  const [status, setStatus] = useState<
    "idle" | "syncing" | "evaluating" | "done" | "error"
  >("idle");
  const queryClient = useQueryClient();

  const handleRefresh = async () => {
    if (status === "syncing" || status === "evaluating") return;

    try {
      setStatus("syncing");
      await api.post("/sync/trigger", null, {
        timeout: 300_000,
      });

      setStatus("evaluating");
      await api.post("/rules/evaluate", null, {
        timeout: 120_000,
      });

      setStatus("done");
      queryClient.invalidateQueries();
      setTimeout(() => setStatus("idle"), 3000);
    } catch {
      setStatus("error");
      setTimeout(() => setStatus("idle"), 4000);
    }
  };

  const label =
    status === "syncing"
      ? "Syncing..."
      : status === "evaluating"
        ? "Evaluating..."
        : status === "done"
          ? "Done"
          : status === "error"
            ? "Failed"
            : "Refresh";

  const isActive =
    status === "syncing" || status === "evaluating";

  return (
    <button
      onClick={handleRefresh}
      disabled={isActive}
      className={`
        flex items-center gap-1.5 px-3 py-1.5
        rounded-lg text-[12px] font-semibold
        transition-all duration-200
        ${
          isActive
            ? "bg-amber-500/20 text-amber-400 cursor-wait"
            : status === "done"
              ? "bg-emerald-500/20 text-emerald-400"
              : status === "error"
                ? "bg-red-500/20 text-red-400"
                : "bg-[var(--accent)]/15 text-[var(--accent)] hover:bg-[var(--accent)]/25"
        }
      `}
    >
      {isActive && (
        <svg
          className="w-3.5 h-3.5 animate-spin"
          viewBox="0 0 24 24"
          fill="none"
        >
          <circle
            cx="12" cy="12" r="10"
            stroke="currentColor"
            strokeWidth="3"
            strokeDasharray="50 20"
          />
        </svg>
      )}
      {!isActive && (
        <svg
          className="w-3.5 h-3.5"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
        >
          <path d="M1 4v6h6" />
          <path d="M23 20v-6h-6" />
          <path d="M20.49 9A9 9 0 0 0 5.64 5.64L1 10m22 4l-4.64 4.36A9 9 0 0 1 3.51 15" />
        </svg>
      )}
      {label}
    </button>
  );
}
