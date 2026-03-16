"use client";

import { useState, useRef, useEffect } from "react";
import { formatNumber } from "@/lib/utils";

interface ConversionItem {
  name: string;
  value: number;
}

interface Props {
  result: number;
  resultLabel?: string;
  breakdown?: ConversionItem[] | null;
  className?: string;
}

/**
 * Shows result count with hover tooltip breaking down
 * conversions by type (like Meta Ads Manager).
 */
export function ConversionTooltip({
  result,
  resultLabel,
  breakdown,
  className = "",
}: Props) {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!open) return;
    const handleClick = (e: MouseEvent) => {
      if (
        ref.current &&
        !ref.current.contains(e.target as Node)
      ) {
        setOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClick);
    return () =>
      document.removeEventListener(
        "mousedown", handleClick
      );
  }, [open]);

  const hasBreakdown =
    breakdown && breakdown.length > 0;

  return (
    <div ref={ref} className={`relative ${className}`}>
      <div
        className="cursor-default"
        onMouseEnter={() =>
          hasBreakdown && setOpen(true)
        }
        onMouseLeave={() => setOpen(false)}
      >
        <span className="text-[13px] tabular-nums text-[var(--text)]">
          {result > 0 ? formatNumber(result) : "—"}
        </span>
        {resultLabel && result > 0 && (
          <p className="text-[10px] text-[var(--muted)] truncate max-w-[120px]">
            {resultLabel}
          </p>
        )}
      </div>

      {open && hasBreakdown && (
        <div
          className={
            "absolute z-50 left-0 top-full mt-1 " +
            "w-[260px] bg-[var(--surface)] " +
            "border border-[var(--border)] " +
            "rounded-lg shadow-lg p-3"
          }
        >
          <h4 className="text-[12px] font-semibold text-[var(--text)] mb-2">
            Conversions
          </h4>
          <div className="flex flex-col gap-1.5">
            {breakdown!.map((item) => (
              <div
                key={item.name}
                className="flex items-center justify-between"
              >
                <span className="text-[12px] text-[var(--text-secondary)]">
                  {item.name}
                </span>
                <span className="text-[12px] font-medium tabular-nums text-[var(--text)]">
                  {formatNumber(item.value)}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
