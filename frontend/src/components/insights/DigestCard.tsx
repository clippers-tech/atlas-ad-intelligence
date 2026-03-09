"use client";

import { useState } from "react";
import type { ClaudeInsight } from "@/lib/types";
import { formatDate, formatRelative } from "@/lib/utils";

interface DigestCardProps {
  insight: ClaudeInsight;
}

const TYPE_CONFIG: Record<string, { label: string; color: string; icon: string }> = {
  daily_digest: {
    label: "Daily Digest",
    color: "bg-blue-500/20 text-blue-400 border-blue-500/30",
    icon: "📊",
  },
  weekly_strategy: {
    label: "Weekly Strategy",
    color: "bg-violet-500/20 text-violet-400 border-violet-500/30",
    icon: "🎯",
  },
  cross_account: {
    label: "Cross Account",
    color: "bg-amber-500/20 text-amber-400 border-amber-500/30",
    icon: "🌐",
  },
  ask: {
    label: "Q&A",
    color: "bg-emerald-500/20 text-emerald-400 border-emerald-500/30",
    icon: "💬",
  },
};

function formatResponse(text: string): string[] {
  return text.split("\n").filter((line) => line.trim().length > 0);
}

export default function DigestCard({ insight }: DigestCardProps) {
  const [expanded, setExpanded] = useState(false);
  const config = TYPE_CONFIG[insight.type] ?? {
    label: insight.type,
    color: "bg-gray-500/20 text-gray-400 border-gray-500/30",
    icon: "📝",
  };

  const lines = insight.response_text ? formatResponse(insight.response_text) : [];
  const preview = lines.slice(0, 3);
  const rest = lines.slice(3);

  return (
    <div className="border border-gray-800 rounded-xl bg-gray-900/50 overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 bg-gray-900/70 border-b border-gray-800">
        <div className="flex items-center gap-3">
          <span className="text-lg">{config.icon}</span>
          <div>
            <span
              className={`inline-block px-2 py-0.5 rounded-full text-xs font-semibold border ${config.color}`}
            >
              {config.label}
            </span>
            <p className="text-xs text-gray-500 mt-0.5">
              {formatDate(insight.created_at)} · {formatRelative(insight.created_at)}
            </p>
          </div>
        </div>
        {lines.length > 3 && (
          <button
            onClick={() => setExpanded(!expanded)}
            className="text-xs text-gray-400 hover:text-gray-200 transition-colors flex items-center gap-1"
          >
            {expanded ? "Collapse ↑" : "Expand ↓"}
          </button>
        )}
      </div>

      {/* Content */}
      <div className="px-4 py-4 space-y-2 text-sm text-gray-300 leading-relaxed">
        {!insight.response_text && (
          <p className="text-gray-500 italic">No response generated.</p>
        )}
        {preview.map((line, i) => (
          <p key={i} className={line.startsWith("**") || line.startsWith("#") ? "font-semibold text-gray-100" : ""}>
            {line.replace(/\*\*/g, "")}
          </p>
        ))}
        {expanded &&
          rest.map((line, i) => (
            <p
              key={i + 100}
              className={line.startsWith("**") || line.startsWith("#") ? "font-semibold text-gray-100" : ""}
            >
              {line.replace(/\*\*/g, "")}
            </p>
          ))}
      </div>

      {/* Footer meta */}
      {insight.tokens_used && (
        <div className="px-4 py-2 border-t border-gray-800/60 flex items-center gap-3 text-xs text-gray-600">
          <span>{insight.model_used ?? "claude"}</span>
          <span>·</span>
          <span>{insight.tokens_used.toLocaleString()} tokens</span>
          {insight.cost_usd && <span>· ${insight.cost_usd.toFixed(4)}</span>}
        </div>
      )}
    </div>
  );
}
