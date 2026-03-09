"use client";

import { useState } from "react";
import { DEAL_STAGES } from "@/lib/constants";

interface LeadStageDropdownProps {
  currentStage: string;
  onChange: (stage: string) => void;
  showRevenue?: boolean;
  onRevenueChange?: (revenue: number) => void;
}

export default function LeadStageDropdown({
  currentStage,
  onChange,
  showRevenue,
  onRevenueChange,
}: LeadStageDropdownProps) {
  const [selectedStage, setSelectedStage] = useState(currentStage);
  const [revenue, setRevenue] = useState<string>("");

  const handleStageChange = (stage: string) => {
    setSelectedStage(stage);
    onChange(stage);
  };

  const handleRevenueChange = (val: string) => {
    setRevenue(val);
    const num = parseFloat(val);
    if (!isNaN(num) && onRevenueChange) {
      onRevenueChange(num);
    }
  };

  const stageObj = DEAL_STAGES.find((s) => s.value === selectedStage);

  return (
    <div className="flex items-center gap-2 flex-wrap">
      <select
        value={selectedStage}
        onChange={(e) => handleStageChange(e.target.value)}
        className="bg-gray-800 border border-gray-700 text-gray-200 text-sm rounded-md px-2 py-1 focus:outline-none focus:ring-1 focus:ring-violet-500 cursor-pointer"
      >
        {DEAL_STAGES.map((stage) => (
          <option key={stage.value} value={stage.value}>
            {stage.emoji} {stage.label}
          </option>
        ))}
      </select>

      {(showRevenue || selectedStage === "closed_won") && (
        <input
          type="number"
          placeholder="Revenue £"
          value={revenue}
          onChange={(e) => handleRevenueChange(e.target.value)}
          className="bg-gray-800 border border-gray-700 text-gray-200 text-sm rounded-md px-2 py-1 w-28 focus:outline-none focus:ring-1 focus:ring-emerald-500 placeholder-gray-500"
          min={0}
        />
      )}

      {stageObj && (
        <span className="text-xs text-gray-500">
          {stageObj.emoji}
        </span>
      )}
    </div>
  );
}
