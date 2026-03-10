"use client";

interface EmptyStateProps {
  title: string;
  description: string;
  action?: { label: string; onClick: () => void };
}

export function EmptyState({ title, description, action }: EmptyStateProps) {
  return (
    <div className="flex flex-col items-center justify-center py-16 px-6 text-center">
      <div className="w-12 h-12 rounded-xl bg-[var(--surface-2)] border border-[var(--border)] flex items-center justify-center mb-4">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none"
          stroke="var(--muted)" strokeWidth="1.5">
          <path d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" />
        </svg>
      </div>
      <h3 className="text-sm font-semibold text-[var(--text)] mb-1">{title}</h3>
      <p className="text-[12px] text-[var(--muted)] max-w-xs">{description}</p>
      {action && (
        <button
          onClick={action.onClick}
          className="mt-4 px-3 py-1.5 rounded-lg bg-amber-500/15 text-amber-400 text-[12px] font-medium hover:bg-amber-500/25 transition-colors"
        >
          {action.label}
        </button>
      )}
    </div>
  );
}
