"use client";

import clsx from "clsx";

interface CardProps {
  children: React.ReactNode;
  title?: string;
  subtitle?: string;
  actions?: React.ReactNode;
  className?: string;
  noPadding?: boolean;
}

export function Card({ children, title, subtitle, actions, className, noPadding }: CardProps) {
  return (
    <div className={clsx(
      "bg-[var(--surface)] border border-[var(--border)] rounded-xl",
      !noPadding && "p-5",
      className
    )}>
      {(title || actions) && (
        <div className={clsx(
          "flex items-center justify-between",
          noPadding ? "px-5 pt-5 pb-3" : "mb-4"
        )}>
          <div>
            {title && (
              <h3 className="text-[13px] font-semibold text-[var(--text)]">
                {title}
              </h3>
            )}
            {subtitle && (
              <p className="text-[11px] text-[var(--muted)] mt-0.5">{subtitle}</p>
            )}
          </div>
          {actions && <div className="flex items-center gap-2">{actions}</div>}
        </div>
      )}
      {children}
    </div>
  );
}
