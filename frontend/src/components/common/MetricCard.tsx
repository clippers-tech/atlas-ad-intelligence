"use client";

interface MetricCardProps {
  title: string;
  value: string;
  change?: number;
  subtitle?: string;
  inverse?: boolean;
}

export function MetricCard({ title, value, change, subtitle, inverse = false }: MetricCardProps) {
  const getChangeStyle = () => {
    if (change === undefined || change === 0) return { color: "text-[var(--muted)]", arrow: "→" };
    const isPositive = change > 0;
    const isBetter = inverse ? !isPositive : isPositive;
    return {
      color: isBetter ? "text-emerald-400" : "text-red-400",
      arrow: isPositive ? "▲" : "▼",
    };
  };

  const { color, arrow } = getChangeStyle();

  return (
    <div className="bg-[var(--surface)] border border-[var(--border)] rounded-xl p-4 hover:border-[var(--border-light)] transition-colors">
      <p className="text-[11px] font-medium text-[var(--muted)] uppercase tracking-widest mb-2">
        {title}
      </p>
      <p className="text-2xl font-bold text-[var(--text)] tabular-nums leading-none mb-2">
        {value}
      </p>
      <div className="flex items-center gap-1.5">
        {change !== undefined && (
          <span className={`text-[11px] font-semibold ${color} tabular-nums`}>
            {arrow} {Math.abs(change).toFixed(1)}%
          </span>
        )}
        {subtitle && (
          <span className="text-[11px] text-[var(--muted)]">{subtitle}</span>
        )}
      </div>
    </div>
  );
}
