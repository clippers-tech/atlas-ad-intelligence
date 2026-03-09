"use client";

import { useState } from "react";
import type { Rule, RuleCondition } from "@/lib/types";
import { RULE_TYPES, ACTION_TYPES } from "@/lib/constants";
import RuleConditionBuilder from "./RuleConditionBuilder";

interface RuleFormProps {
  initialValues?: Rule;
  onSubmit: (data: Partial<Rule>) => void;
  onCancel: () => void;
}

export default function RuleForm({ initialValues, onSubmit, onCancel }: RuleFormProps) {
  const [name, setName] = useState(initialValues?.name ?? "");
  const [type, setType] = useState<Rule["type"]>(initialValues?.type ?? "kill");
  const [description, setDescription] = useState(initialValues?.description ?? "");
  const [conditions, setConditions] = useState<RuleCondition[]>([
    initialValues?.condition_json ?? { metric: "spend", operator: ">", value: 50 },
  ]);
  const [actionType, setActionType] = useState(
    initialValues?.action_json?.action ?? "pause"
  );
  const [actionPercent, setActionPercent] = useState<string>(
    String(initialValues?.action_json?.percent ?? "")
  );
  const [cooldown, setCooldown] = useState(initialValues?.cooldown_minutes ?? 60);
  const [priority, setPriority] = useState(initialValues?.priority ?? 5);

  const percentActions = ["increase_budget", "decrease_budget", "bid_adjust"];
  const showPercent = percentActions.includes(actionType);

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    const [primary, ...rest] = conditions;
    const conditionJson: RuleCondition = {
      ...primary,
      ...(rest.length > 0 ? { and: rest } : {}),
    };
    onSubmit({
      ...(initialValues ? { id: initialValues.id, account_id: initialValues.account_id } : {}),
      name,
      type,
      description: description || null,
      condition_json: conditionJson,
      action_json: {
        action: actionType,
        ...(showPercent && actionPercent ? { percent: parseFloat(actionPercent) } : {}),
      },
      cooldown_minutes: cooldown,
      priority,
      is_enabled: initialValues?.is_enabled ?? true,
    });
  };

  const inputClass =
    "w-full bg-gray-800 border border-gray-700 text-gray-200 text-sm rounded-lg px-3 py-2 focus:outline-none focus:ring-1 focus:ring-violet-500 placeholder-gray-600";

  return (
    <form onSubmit={handleSubmit} className="space-y-5">
      {/* Name */}
      <div>
        <label className="block text-xs font-semibold text-gray-400 uppercase tracking-wide mb-1.5">
          Rule Name
        </label>
        <input
          value={name}
          onChange={(e) => setName(e.target.value)}
          required
          placeholder="e.g. Kill high-spend zero-conversion ads"
          className={inputClass}
        />
      </div>

      {/* Type */}
      <div>
        <label className="block text-xs font-semibold text-gray-400 uppercase tracking-wide mb-1.5">
          Type
        </label>
        <div className="flex gap-2 flex-wrap">
          {RULE_TYPES.map((t) => (
            <button
              key={t.value}
              type="button"
              onClick={() => setType(t.value as Rule["type"])}
              className={`px-3 py-1.5 text-sm rounded-lg border transition-colors ${
                type === t.value
                  ? "bg-violet-600 border-violet-500 text-white"
                  : "bg-gray-800 border-gray-700 text-gray-400 hover:border-gray-500"
              }`}
            >
              {t.label}
            </button>
          ))}
        </div>
      </div>

      {/* Description */}
      <div>
        <label className="block text-xs font-semibold text-gray-400 uppercase tracking-wide mb-1.5">
          Description (optional)
        </label>
        <textarea
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          rows={2}
          placeholder="What does this rule do?"
          className={inputClass}
        />
      </div>

      {/* Condition builder */}
      <RuleConditionBuilder conditions={conditions} onChange={setConditions} />

      {/* Action */}
      <div className="space-y-3">
        <label className="block text-xs font-semibold text-gray-400 uppercase tracking-wide">
          Action
        </label>
        <select
          value={actionType}
          onChange={(e) => setActionType(e.target.value)}
          className={inputClass}
        >
          {ACTION_TYPES.map((a) => (
            <option key={a.value} value={a.value}>
              {a.icon} {a.label}
            </option>
          ))}
        </select>
        {showPercent && (
          <div className="flex items-center gap-2">
            <input
              type="number"
              value={actionPercent}
              onChange={(e) => setActionPercent(e.target.value)}
              placeholder="Percent"
              min={1}
              max={500}
              className="w-28 bg-gray-800 border border-gray-700 text-gray-200 text-sm rounded-lg px-3 py-2 focus:outline-none focus:ring-1 focus:ring-violet-500"
            />
            <span className="text-gray-500 text-sm">%</span>
          </div>
        )}
      </div>

      {/* Cooldown + Priority */}
      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-xs font-semibold text-gray-400 uppercase tracking-wide mb-1.5">
            Cooldown (minutes)
          </label>
          <input
            type="number"
            value={cooldown}
            onChange={(e) => setCooldown(Number(e.target.value))}
            min={5}
            className={inputClass}
          />
        </div>
        <div>
          <label className="block text-xs font-semibold text-gray-400 uppercase tracking-wide mb-1.5">
            Priority (1–10)
          </label>
          <input
            type="number"
            value={priority}
            onChange={(e) => setPriority(Number(e.target.value))}
            min={1}
            max={10}
            className={inputClass}
          />
        </div>
      </div>

      {/* Buttons */}
      <div className="flex gap-3 pt-2">
        <button
          type="submit"
          className="px-5 py-2 bg-violet-600 hover:bg-violet-500 text-white text-sm font-medium rounded-lg transition-colors"
        >
          {initialValues ? "Save Changes" : "Create Rule"}
        </button>
        <button
          type="button"
          onClick={onCancel}
          className="px-4 py-2 bg-gray-700 hover:bg-gray-600 text-gray-300 text-sm rounded-lg transition-colors"
        >
          Cancel
        </button>
      </div>
    </form>
  );
}
