"use client";

interface HeatmapData {
  audienceLabels: string[];
  creativeLabels: string[];
  values: number[][];
}

interface AudienceHeatmapProps {
  data: HeatmapData;
}

// Map a CPL value to a color class (green = low CPL = good, red = high CPL = bad)
function cplToColor(value: number, min: number, max: number): string {
  if (max === min) return "bg-gray-500/20";
  const ratio = (value - min) / (max - min); // 0 = best (green), 1 = worst (red)

  if (ratio < 0.2) return "bg-emerald-500/40 text-emerald-300";
  if (ratio < 0.4) return "bg-emerald-500/20 text-emerald-400";
  if (ratio < 0.6) return "bg-amber-500/20 text-amber-400";
  if (ratio < 0.8) return "bg-red-500/20 text-red-400";
  return "bg-red-500/40 text-red-300";
}

export function AudienceHeatmap({ data }: AudienceHeatmapProps) {
  const { audienceLabels, creativeLabels, values } = data;

  if (!audienceLabels.length || !creativeLabels.length) {
    return (
      <div className="bg-[#141414] border border-[#262626] rounded-xl p-6 text-center text-gray-500 text-sm">
        No heatmap data available
      </div>
    );
  }

  // Find global min/max for color scaling
  const allValues = values.flat().filter((v) => v > 0);
  const min = Math.min(...allValues);
  const max = Math.max(...allValues);

  const truncate = (s: string, n: number) =>
    s.length > n ? s.slice(0, n) + "…" : s;

  return (
    <div className="bg-[#141414] border border-[#262626] rounded-xl p-5 overflow-x-auto">
      <h3 className="text-sm font-semibold text-white mb-4">
        Audience × Creative CPL Heatmap
      </h3>
      <div
        className="grid gap-1"
        style={{
          gridTemplateColumns: `120px repeat(${creativeLabels.length}, minmax(80px, 1fr))`,
        }}
      >
        {/* Header row */}
        <div className="h-8" />
        {creativeLabels.map((label) => (
          <div
            key={label}
            className="h-8 flex items-end justify-center pb-1"
            title={label}
          >
            <span
              className="text-[10px] text-gray-500 text-center leading-tight"
              style={{ writingMode: "vertical-rl", transform: "rotate(180deg)" }}
            >
              {truncate(label, 12)}
            </span>
          </div>
        ))}

        {/* Data rows */}
        {audienceLabels.map((audLabel, rowIdx) => (
          <>
            <div
              key={`label-${audLabel}`}
              className="flex items-center text-xs text-gray-400 truncate pr-2"
              title={audLabel}
            >
              {truncate(audLabel, 16)}
            </div>
            {creativeLabels.map((_, colIdx) => {
              const val = values[rowIdx]?.[colIdx] ?? 0;
              const colorClass = val > 0
                ? cplToColor(val, min, max)
                : "bg-[#1a1a1a] text-gray-600";

              return (
                <div
                  key={`${rowIdx}-${colIdx}`}
                  className={`h-9 rounded flex items-center justify-center text-xs font-medium tabular-nums transition-colors ${colorClass}`}
                  title={val > 0 ? `£${val.toFixed(0)}` : "No data"}
                >
                  {val > 0 ? `£${val.toFixed(0)}` : "—"}
                </div>
              );
            })}
          </>
        ))}
      </div>

      {/* Legend */}
      <div className="flex items-center gap-3 mt-4 pt-3 border-t border-[#262626]">
        <span className="text-xs text-gray-500">CPL:</span>
        <div className="flex items-center gap-1">
          <span className="w-4 h-4 rounded bg-emerald-500/40" />
          <span className="text-xs text-gray-500">Low</span>
        </div>
        <div className="flex items-center gap-1">
          <span className="w-4 h-4 rounded bg-amber-500/20" />
          <span className="text-xs text-gray-500">Mid</span>
        </div>
        <div className="flex items-center gap-1">
          <span className="w-4 h-4 rounded bg-red-500/40" />
          <span className="text-xs text-gray-500">High</span>
        </div>
      </div>
    </div>
  );
}
