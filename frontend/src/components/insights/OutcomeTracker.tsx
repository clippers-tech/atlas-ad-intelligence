"use client";

import { formatDate } from "@/lib/utils";
import { truncate } from "@/lib/utils";

interface Outcome {
  date: string;
  recommendation: string;
  action_taken: boolean;
  outcome: string;
}

interface OutcomeTrackerProps {
  outcomes: Outcome[];
}

export default function OutcomeTracker({ outcomes }: OutcomeTrackerProps) {
  if (outcomes.length === 0) {
    return (
      <div className="text-center py-12 text-gray-500 text-sm">
        No outcomes tracked yet. Take actions on recommendations to see results here.
      </div>
    );
  }

  return (
    <div className="overflow-x-auto rounded-xl border border-gray-800">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-gray-800 bg-gray-900/50">
            {["Date", "Recommendation", "Action Taken", "Outcome"].map((h) => (
              <th
                key={h}
                className="px-4 py-3 text-left text-xs font-semibold text-gray-400 uppercase tracking-wide"
              >
                {h}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-800">
          {outcomes.map((item, idx) => (
            <tr key={idx} className="hover:bg-gray-800/30 transition-colors">
              <td className="px-4 py-3 text-gray-400 whitespace-nowrap">
                {formatDate(item.date)}
              </td>
              <td className="px-4 py-3 text-gray-300 max-w-xs">
                {truncate(item.recommendation, 80)}
              </td>
              <td className="px-4 py-3">
                <span
                  className={`text-base ${item.action_taken ? "text-emerald-400" : "text-red-400"}`}
                  title={item.action_taken ? "Action taken" : "No action taken"}
                >
                  {item.action_taken ? "✅" : "❌"}
                </span>
              </td>
              <td className="px-4 py-3 text-gray-400 max-w-sm">
                {truncate(item.outcome, 100)}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
