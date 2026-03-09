"use client";

type Size = "sm" | "md";

interface StatusBadgeProps {
  status: string;
  size?: Size;
}

function getStatusColors(status: string): string {
  const s = status.toLowerCase();

  if (["active", "approved", "enabled", "running", "closed_won"].includes(s)) {
    return "bg-emerald-500/20 text-emerald-400 border-emerald-500/30";
  }
  if (["paused", "disapproved", "disabled", "closed_lost", "burned"].includes(s)) {
    return "bg-red-500/20 text-red-400 border-red-500/30";
  }
  if (["pending", "in_review", "pending_review", "declining", "scheduled"].includes(s)) {
    return "bg-amber-500/20 text-amber-400 border-amber-500/30";
  }
  if (["draft", "archived", "inactive"].includes(s)) {
    return "bg-gray-500/20 text-gray-400 border-gray-500/30";
  }
  if (["completed", "fresh", "qualified"].includes(s)) {
    return "bg-blue-500/20 text-blue-400 border-blue-500/30";
  }
  if (["high", "critical"].includes(s)) {
    return "bg-red-500/20 text-red-400 border-red-500/30";
  }
  if (["medium"].includes(s)) {
    return "bg-amber-500/20 text-amber-400 border-amber-500/30";
  }
  if (["low"].includes(s)) {
    return "bg-emerald-500/20 text-emerald-400 border-emerald-500/30";
  }

  return "bg-gray-500/20 text-gray-400 border-gray-500/30";
}

function formatLabel(status: string): string {
  return status
    .replace(/_/g, " ")
    .replace(/\b\w/g, (c) => c.toUpperCase());
}

export function StatusBadge({ status, size = "md" }: StatusBadgeProps) {
  const colors = getStatusColors(status);
  const sizeClasses =
    size === "sm"
      ? "px-1.5 py-0.5 text-[10px]"
      : "px-2.5 py-1 text-xs";

  return (
    <span
      className={[
        "inline-flex items-center rounded-full border font-medium",
        sizeClasses,
        colors,
      ].join(" ")}
    >
      {formatLabel(status)}
    </span>
  );
}
