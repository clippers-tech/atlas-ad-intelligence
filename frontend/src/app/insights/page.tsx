"use client";

import { useState } from "react";
import { useInsights, useAskClaude } from "@/hooks/useInsights";
import InsightHistory from "@/components/insights/InsightHistory";
import AskClaude from "@/components/insights/AskClaude";
import OutcomeTracker from "@/components/insights/OutcomeTracker";
import CrossAccountTab from "@/components/insights/CrossAccountTab";
import { LoadingSpinner } from "@/components/common/LoadingSpinner";

type TabKey = "daily" | "weekly" | "ask" | "outcomes" | "cross";

const TABS: { key: TabKey; label: string; icon: string }[] = [
  { key: "daily", label: "Daily Digest", icon: "📊" },
  { key: "weekly", label: "Weekly Strategy", icon: "🎯" },
  { key: "ask", label: "Ask Claude", icon: "🤖" },
  { key: "outcomes", label: "Outcomes", icon: "📈" },
  { key: "cross", label: "Cross-Account", icon: "🌐" },
];

export default function InsightsPage() {
  const [activeTab, setActiveTab] = useState<TabKey>("daily");

  const { data: allInsights = [], isLoading } = useInsights();
  const askClaude = useAskClaude();

  const dailyInsights = allInsights.filter((i) => i.type === "daily_digest");
  const weeklyInsights = allInsights.filter((i) => i.type === "weekly_strategy");
  const lastAskResponse = askClaude.data?.response_text ?? null;

  // Mock outcomes data (would come from a dedicated endpoint in production)
  const mockOutcomes: {
    date: string;
    recommendation: string;
    action_taken: boolean;
    outcome: string;
  }[] = [];

  if (isLoading) {
    return (
      <div className="flex justify-center py-24">
        <LoadingSpinner />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-100">Claude Insights</h1>
        <p className="text-sm text-gray-400 mt-0.5">
          AI-powered analysis and strategy recommendations for your ad accounts.
        </p>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 bg-gray-900/50 border border-gray-800 rounded-xl p-1 overflow-x-auto">
        {TABS.map((tab) => (
          <button
            key={tab.key}
            onClick={() => setActiveTab(tab.key)}
            className={`flex items-center gap-2 px-4 py-2 text-sm rounded-lg font-medium whitespace-nowrap transition-colors flex-shrink-0 ${
              activeTab === tab.key
                ? "bg-violet-600 text-white shadow"
                : "text-gray-400 hover:text-gray-200 hover:bg-gray-800"
            }`}
          >
            <span>{tab.icon}</span>
            {tab.label}
          </button>
        ))}
      </div>

      {/* Tab Content */}
      <div>
        {activeTab === "daily" && (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <p className="text-sm text-gray-400">
                {dailyInsights.length} daily digests
              </p>
            </div>
            <InsightHistory insights={dailyInsights} />
          </div>
        )}

        {activeTab === "weekly" && (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <p className="text-sm text-gray-400">
                {weeklyInsights.length} weekly strategy reports
              </p>
            </div>
            <InsightHistory insights={weeklyInsights} />
          </div>
        )}

        {activeTab === "ask" && (
          <div className="max-w-2xl">
            <AskClaude
              onAsk={(q) => askClaude.mutate(q)}
              isLoading={askClaude.isPending}
              lastResponse={lastAskResponse}
            />
          </div>
        )}

        {activeTab === "outcomes" && (
          <OutcomeTracker outcomes={mockOutcomes} />
        )}

        {activeTab === "cross" && (
          <CrossAccountTab insights={allInsights} />
        )}
      </div>
    </div>
  );
}
