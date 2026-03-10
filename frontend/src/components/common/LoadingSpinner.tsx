"use client";

export function LoadingSpinner({ size = "md" }: { size?: "sm" | "md" | "lg" }) {
  const dims = size === "sm" ? "w-4 h-4" : size === "lg" ? "w-8 h-8" : "w-5 h-5";

  return (
    <svg className={`${dims} animate-spin text-amber-500`} viewBox="0 0 24 24" fill="none">
      <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="3" opacity="0.2" />
      <path d="M12 2a10 10 0 019.95 9" stroke="currentColor" strokeWidth="3" strokeLinecap="round" />
    </svg>
  );
}

export function PageLoader() {
  return (
    <div className="flex items-center justify-center py-20">
      <div className="flex flex-col items-center gap-3">
        <LoadingSpinner size="lg" />
        <p className="text-[12px] text-[var(--muted)]">Loading...</p>
      </div>
    </div>
  );
}

export function SkeletonCard({ className = "h-24" }: { className?: string }) {
  return <div className={`skeleton ${className}`} />;
}

export function SkeletonRow() {
  return (
    <div className="flex gap-4 py-3">
      <div className="skeleton h-4 w-32" />
      <div className="skeleton h-4 w-20" />
      <div className="skeleton h-4 w-24" />
      <div className="skeleton h-4 w-16" />
    </div>
  );
}
