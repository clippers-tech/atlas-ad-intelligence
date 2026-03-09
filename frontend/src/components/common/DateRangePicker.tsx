"use client";

import { format, subDays, startOfToday } from "date-fns";

interface DateRange {
  from: string;
  to: string;
}

interface DateRangePickerProps {
  value: DateRange;
  onChange: (range: DateRange) => void;
}

const today = () => format(startOfToday(), "yyyy-MM-dd");
const daysAgo = (n: number) => format(subDays(new Date(), n), "yyyy-MM-dd");

const PRESETS = [
  {
    label: "Today",
    getRange: (): DateRange => ({ from: today(), to: today() }),
  },
  {
    label: "7d",
    getRange: (): DateRange => ({ from: daysAgo(6), to: today() }),
  },
  {
    label: "30d",
    getRange: (): DateRange => ({ from: daysAgo(29), to: today() }),
  },
  {
    label: "90d",
    getRange: (): DateRange => ({ from: daysAgo(89), to: today() }),
  },
];

const inputClass =
  "bg-[#1a1a1a] border border-[#262626] text-gray-300 text-sm rounded-md px-3 py-2 focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500 [color-scheme:dark]";

export function DateRangePicker({ value, onChange }: DateRangePickerProps) {
  const activePreset = PRESETS.find(
    (p) => {
      const r = p.getRange();
      return r.from === value.from && r.to === value.to;
    }
  )?.label;

  return (
    <div className="flex flex-wrap items-center gap-2">
      {/* Preset buttons */}
      <div className="flex items-center rounded-md border border-[#262626] overflow-hidden">
        {PRESETS.map((preset) => (
          <button
            key={preset.label}
            onClick={() => onChange(preset.getRange())}
            className={[
              "px-3 py-2 text-xs font-medium transition-colors",
              activePreset === preset.label
                ? "bg-blue-600 text-white"
                : "bg-[#1a1a1a] text-gray-400 hover:bg-[#262626] hover:text-gray-200",
            ].join(" ")}
          >
            {preset.label}
          </button>
        ))}
      </div>

      {/* Custom date inputs */}
      <div className="flex items-center gap-2">
        <input
          type="date"
          value={value.from}
          max={value.to}
          onChange={(e) => onChange({ ...value, from: e.target.value })}
          className={inputClass}
        />
        <span className="text-gray-500 text-sm">→</span>
        <input
          type="date"
          value={value.to}
          min={value.from}
          max={today()}
          onChange={(e) => onChange({ ...value, to: e.target.value })}
          className={inputClass}
        />
      </div>
    </div>
  );
}
