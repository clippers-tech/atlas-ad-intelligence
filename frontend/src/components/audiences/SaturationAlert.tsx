"use client";

interface SaturationAlertItem {
  audience: string;
  frequency: number;
  level: string;
}

interface SaturationAlertProps {
  alerts: SaturationAlertItem[];
}

function getSeverityStyle(level: string, frequency: number) {
  if (level === "critical" || frequency >= 5) {
    return {
      container: "bg-red-950/40 border-red-500/30",
      badge: "bg-red-500/20 text-red-400 border-red-500/30",
      icon: "🔴",
      label: "Critical",
    };
  }
  if (level === "warning" || frequency >= 3.5) {
    return {
      container: "bg-amber-950/40 border-amber-500/30",
      badge: "bg-amber-500/20 text-amber-400 border-amber-500/30",
      icon: "🟡",
      label: "Warning",
    };
  }
  return {
    container: "bg-[#1a1a1a] border-[#262626]",
    badge: "bg-gray-500/20 text-gray-400 border-gray-500/30",
    icon: "⚪",
    label: "Monitor",
  };
}

export function SaturationAlert({ alerts }: SaturationAlertProps) {
  if (!alerts || alerts.length === 0) return null;

  return (
    <div className="flex flex-col gap-2">
      <h3 className="text-sm font-semibold text-white mb-1">
        Frequency Saturation Alerts
      </h3>
      {alerts.map((alert, idx) => {
        const style = getSeverityStyle(alert.level, alert.frequency);
        return (
          <div
            key={idx}
            className={`flex items-center justify-between gap-4 border rounded-lg px-4 py-3 ${style.container}`}
          >
            <div className="flex items-center gap-3 min-w-0">
              <span className="text-base flex-shrink-0" role="img">
                {style.icon}
              </span>
              <div className="min-w-0">
                <p className="text-sm text-gray-200 font-medium truncate">
                  {alert.audience}
                </p>
                <p className="text-xs text-gray-500 mt-0.5">
                  Frequency approaching saturation
                </p>
              </div>
            </div>
            <div className="flex items-center gap-3 flex-shrink-0">
              <span className="text-sm font-bold tabular-nums text-gray-200">
                {alert.frequency.toFixed(1)}×
              </span>
              <span
                className={`inline-flex items-center px-2 py-0.5 rounded-full border text-xs font-medium ${style.badge}`}
              >
                {style.label}
              </span>
            </div>
          </div>
        );
      })}
    </div>
  );
}
