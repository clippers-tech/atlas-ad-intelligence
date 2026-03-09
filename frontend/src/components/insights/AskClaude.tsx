"use client";

import { useState, type FormEvent } from "react";
import { LoadingSpinner } from "@/components/common/LoadingSpinner";

interface AskClaudeProps {
  onAsk: (question: string) => void;
  isLoading: boolean;
  lastResponse: string | null;
}

const SUGGESTED = [
  "Which campaigns have the best ROAS this week?",
  "What creative hooks are driving the most leads?",
  "Which audiences should I scale and which should I pause?",
  "How does my CPL compare to last month?",
];

export default function AskClaude({ onAsk, isLoading, lastResponse }: AskClaudeProps) {
  const [question, setQuestion] = useState("");

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    if (!question.trim()) return;
    onAsk(question.trim());
  };

  const handleSuggestion = (q: string) => {
    setQuestion(q);
  };

  return (
    <div className="space-y-5">
      {/* Input */}
      <form onSubmit={handleSubmit} className="space-y-3">
        <div className="relative">
          <textarea
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            placeholder="Ask Claude anything about your ad performance…"
            rows={3}
            className="w-full bg-gray-800 border border-gray-700 text-gray-200 text-sm rounded-xl px-4 py-3 focus:outline-none focus:ring-1 focus:ring-violet-500 placeholder-gray-600 resize-none"
            onKeyDown={(e) => {
              if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) handleSubmit(e);
            }}
          />
        </div>
        <div className="flex items-center justify-between">
          <span className="text-xs text-gray-600">⌘+Enter to send</span>
          <button
            type="submit"
            disabled={!question.trim() || isLoading}
            className="flex items-center gap-2 px-5 py-2 bg-violet-600 hover:bg-violet-500 disabled:opacity-40 disabled:cursor-not-allowed text-white text-sm font-medium rounded-lg transition-colors"
          >
            {isLoading ? <LoadingSpinner size={16} /> : "🤖"}
            {isLoading ? "Asking Claude…" : "Ask Claude"}
          </button>
        </div>
      </form>

      {/* Suggestions */}
      {!lastResponse && !isLoading && (
        <div>
          <p className="text-xs text-gray-500 mb-2">Suggested questions:</p>
          <div className="flex flex-wrap gap-2">
            {SUGGESTED.map((q) => (
              <button
                key={q}
                onClick={() => handleSuggestion(q)}
                className="text-xs px-3 py-1.5 bg-gray-800 border border-gray-700 hover:border-violet-600 text-gray-400 hover:text-violet-400 rounded-lg transition-colors"
              >
                {q}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Response */}
      {isLoading && (
        <div className="flex items-center gap-3 py-4 text-sm text-gray-400">
          <LoadingSpinner />
          <span>Claude is analysing your account data…</span>
        </div>
      )}

      {lastResponse && !isLoading && (
        <div className="bg-gray-800/60 border border-gray-700 rounded-xl px-5 py-4">
          <div className="flex items-center gap-2 mb-3">
            <span className="text-base">🤖</span>
            <span className="text-xs font-semibold text-violet-400">Claude's Response</span>
          </div>
          <div className="text-sm text-gray-300 leading-relaxed whitespace-pre-wrap">
            {lastResponse}
          </div>
        </div>
      )}
    </div>
  );
}
