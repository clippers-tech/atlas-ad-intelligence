"use client";

import clsx from "clsx";

type BadgeVariant = "success" | "warning" | "danger" | "info" | "muted" | "amber";

interface StatusBadgeProps {
  label: string;
  variant?: BadgeVariant;
  dot?: boolean;
  onClick?: () => void;
  loading?: boolean;
}

const variants: Record<BadgeVariant, string> = {
  success: "bg-emerald-500/12 text-emerald-400 border-emerald-500/20",
  warning: "bg-amber-500/12 text-amber-400 border-amber-500/20",
  danger: "bg-red-500/12 text-red-400 border-red-500/20",
  info: "bg-blue-500/12 text-blue-400 border-blue-500/20",
  muted: "bg-[var(--surface-3)] text-[var(--muted)] border-[var(--border)]",
  amber: "bg-amber-500/12 text-amber-400 border-amber-500/20",
};

const dotColors: Record<BadgeVariant, string> = {
  success: "bg-emerald-400",
  warning: "bg-amber-400",
  danger: "bg-red-400",
  info: "bg-blue-400",
  muted: "bg-[var(--muted)]",
  amber: "bg-amber-400",
};

export function StatusBadge({
  label, variant = "muted", dot = false, onClick, loading,
}: StatusBadgeProps) {
  const isClickable = !!onClick && !loading;
  return (
    <span
      role={isClickable ? "button" : undefined}
      tabIndex={isClickable ? 0 : undefined}
      onClick={isClickable ? onClick : undefined}
      onKeyDown={isClickable ? (e) => {
        if (e.key === "Enter" || e.key === " ") onClick();
      } : undefined}
      className={clsx(
        "inline-flex items-center gap-1.5 px-2 py-0.5 rounded-md text-[11px] font-medium border",
        variants[variant],
        isClickable && "cursor-pointer hover:opacity-80 transition-opacity",
        loading && "opacity-50 cursor-wait",
      )}
    >
      {dot && <span className={clsx("w-1.5 h-1.5 rounded-full", dotColors[variant])} />}
      {loading ? "..." : label}
    </span>
  );
}

export function getStatusVariant(status: string): BadgeVariant {
  const s = status.toLowerCase();
  if (s === "active" || s === "running" || s === "live") return "success";
  if (s === "paused" || s === "warning" || s === "degraded") return "warning";
  if (s === "deleted" || s === "error" || s === "critical" || s === "failed") return "danger";
  if (s === "draft" || s === "pending") return "info";
  return "muted";
}
