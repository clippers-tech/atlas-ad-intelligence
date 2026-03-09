"use client";

import { METRICS, OPERATORS } from "@/lib/constants";
import type { RuleCondition } from "@/lib/types";

interface RuleConditionBuilderProps {
  conditions: RuleCondition[];
  onChange: (conditions: RuleCondition[]) => void;
}

const emptyCondition = (): RuleCondition => ({
  metric: "spend",
  operator: ">",
  value: 0,
});

export default function RuleConditionBuilder({
  conditions,
  onChange,
}: RuleConditionBuilderProps) {
  const updateCondition = (idx: number, field: keyof RuleCondition, value: string | number) => {
    const next = conditions.map((c, i) =>
      i === idx ? { ...c, [field]: value } : c
    );
    onChange(next);
  };

  const addCondition = () => {
    onChange([...conditions, emptyCondition()]);
  };

  const removeCondition = (idx: number) => {
    onChange(conditions.filter((_, i) => i !== idx));
  };

  return (
    <div className="space-y-3">
      <label className="block text-xs font-semibold text-gray-400 uppercase tracking-wide">
        Conditions
      </label>

      {conditions.map((cond, idx) => (
        <div key={idx} className="flex items-center gap-2 flex-wrap">
          {idx > 0 && (
            <span className="text-xs font-semibold text-violet-400 w-8 text-center">
              AND
            </span>
          )}
          {idx === 0 && (
            <span className="text-xs font-semibold text-gray-500 w-8 text-center">
              IF
            </span>
          )}

          {/* Metric */}
          <select
            value={cond.metric}
            onChange={(e) => updateCondition(idx, "metric", e.target.value)}
            className="bg-gray-800 border border-gray-700 text-gray-300 text-sm rounded-md px-2 py-1.5 focus:outline-none focus:ring-1 focus:ring-violet-500"
          >
            {METRICS.map((m) => (
              <option key={m} value={m}>{m}</option>
            ))}
          </select>

          {/* Operator */}
          <select
            value={cond.operator}
            onChange={(e) => updateCondition(idx, "operator", e.target.value)}
            className="bg-gray-800 border border-gray-700 text-gray-300 text-sm rounded-md px-2 py-1.5 w-16 focus:outline-none focus:ring-1 focus:ring-violet-500"
          >
            {OPERATORS.map((op) => (
              <option key={op} value={op}>{op}</option>
            ))}
          </select>

          {/* Value */}
          <input
            type="number"
            value={cond.value}
            onChange={(e) => updateCondition(idx, "value", parseFloat(e.target.value) || 0)}
            className="bg-gray-800 border border-gray-700 text-gray-200 text-sm rounded-md px-2 py-1.5 w-24 focus:outline-none focus:ring-1 focus:ring-violet-500"
            min={0}
            step={0.01}
          />

          {/* Remove */}
          {idx > 0 && (
            <button
              type="button"
              onClick={() => removeCondition(idx)}
              className="text-red-500 hover:text-red-400 text-lg leading-none transition-colors"
              aria-label="Remove condition"
            >
              ×
            </button>
          )}
        </div>
      ))}

      <button
        type="button"
        onClick={addCondition}
        className="text-xs text-violet-400 hover:text-violet-300 transition-colors mt-1"
      >
        + Add AND condition
      </button>
    </div>
  );
}
