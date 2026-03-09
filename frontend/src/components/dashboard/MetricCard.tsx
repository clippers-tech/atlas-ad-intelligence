"use client";

import { Card } from "@tremor/react";

interface MetricCardProps {
  title: string;
  value: string;
  comparison: string;
  changePercent: number;
  inverse?: boolean;
}

function ChangeIndicator({
  changePercent,
  inverse,
}: {
  changePercent: number;
  inverse?: boolean;
}) {
  if (changePercent === 0) {
    return (
      <span className="text-gray-400 text-xs">
        → 0.0% vs yesterday
      </span>
    );
  }

  const isPositive = changePercent > 0;
  // For inverse metrics (CPL), lower is better → positive change is bad
  const isBetter = inverse ? !isPositive : isPositive;
  const colorClass = isBetter ? "text-emerald-400" : "text-red-400";
  const arrow = isPositive ? "↑" : "↓";

  return (
    <span className={`text-xs font-medium ${colorClass}`}>
      {arrow} {Math.abs(changePercent).toFixed(1)}% vs yesterday
    </span>
  );
}

export function MetricCard({
  title,
  value,
  comparison,
  changePercent,
  inverse = false,
}: MetricCardProps) {
  return (
    <Card className="bg-[#141414] border border-[#262626] rounded-xl p-4 ring-0 shadow-none">
      <p className="text-xs font-medium text-gray-400 uppercase tracking-wider mb-2">
        {title}
      </p>
      <p className="text-2xl font-bold text-white mb-1 tabular-nums">
        {value}
      </p>
      <div className="flex flex-col gap-0.5">
        <p className="text-xs text-gray-500">{comparison}</p>
        <ChangeIndicator changePercent={changePercent} inverse={inverse} />
      </div>
    </Card>
  );
}
