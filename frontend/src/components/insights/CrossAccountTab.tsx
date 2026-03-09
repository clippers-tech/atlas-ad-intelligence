"use client";

import type { ClaudeInsight } from "@/lib/types";
import DigestCard from "./DigestCard";

interface CrossAccountTabProps {
  insights: ClaudeInsight[];
}

export default function CrossAccountTab({ insights }: CrossAccountTabProps) {
  const crossAccount = insights.filter(
    (i) => i.type === "cross_account" || i.account_id === null
  );

  if (crossAccount.length === 0) {
    return (
      <div className="text-center py-16 space-y-2">
        <p className="text-4xl">🌐</p>
        <p className="text-gray-400 font-medium">No cross-account insights yet</p>
        <p className="text-sm text-gray-600 max-w-sm mx-auto">
          Cross-account analysis compares patterns across all your connected accounts.
          This report is generated weekly.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-3 px-4 py-3 bg-amber-950/30 border border-amber-900/40 rounded-xl">
        <span className="text-xl">🌐</span>
        <div>
          <p className="text-sm font-semibold text-amber-300">Cross-Account Analysis</p>
          <p className="text-xs text-amber-400/70">
            Comparing patterns across all accounts. Account IDs are shown in context labels.
          </p>
        </div>
      </div>

      <div className="space-y-4">
        {crossAccount.map((insight) => (
          <div key={insight.id} className="space-y-1">
            {/* Account context label */}
            <div className="flex items-center gap-2">
              <span className="text-xs font-mono text-amber-500 bg-amber-950/40 px-2 py-0.5 rounded">
                {insight.account_id ? `Account: ${insight.account_id.slice(0, 8)}…` : "All Accounts"}
              </span>
            </div>
            <DigestCard insight={insight} />
          </div>
        ))}
      </div>
    </div>
  );
}
