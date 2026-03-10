"use client";

interface DateRangePickerProps {
  startDate: string;
  endDate: string;
  onChange: (start: string, end: string) => void;
}

export function DateRangePicker({ startDate, endDate, onChange }: DateRangePickerProps) {
  return (
    <div className="flex items-center gap-2">
      <input
        type="date"
        value={startDate}
        onChange={(e) => onChange(e.target.value, endDate)}
        className="bg-[var(--surface-2)] border border-[var(--border)] rounded-lg px-2.5 py-1.5 text-[12px] text-[var(--text)] focus:border-amber-500/50 focus:outline-none transition-colors"
      />
      <span className="text-[11px] text-[var(--muted)]">to</span>
      <input
        type="date"
        value={endDate}
        onChange={(e) => onChange(startDate, e.target.value)}
        className="bg-[var(--surface-2)] border border-[var(--border)] rounded-lg px-2.5 py-1.5 text-[12px] text-[var(--text)] focus:border-amber-500/50 focus:outline-none transition-colors"
      />
    </div>
  );
}
