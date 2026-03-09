"use client";

interface VelocityAlertProps {
  daysWithoutNew: number;
  fatiguedCount: number;
  totalActive: number;
}

export function VelocityAlert({
  daysWithoutNew,
  fatiguedCount,
  totalActive,
}: VelocityAlertProps) {
  const isCritical = daysWithoutNew > 21;
  const isWarning = daysWithoutNew > 14;
  const fatiguedRatio = totalActive > 0 ? fatiguedCount / totalActive : 0;
  const highFatigue = fatiguedRatio > 0.5;

  // No alert needed
  if (!isWarning && !highFatigue) return null;

  const level: "critical" | "warning" = isCritical || highFatigue ? "critical" : "warning";

  const styles = {
    critical: {
      container: "bg-red-950/40 border-red-500/30",
      icon: "🚨",
      title: "text-red-400",
      text: "text-red-300",
    },
    warning: {
      container: "bg-amber-950/40 border-amber-500/30",
      icon: "⚠️",
      title: "text-amber-400",
      text: "text-amber-300",
    },
  }[level];

  const messages: string[] = [];

  if (isCritical) {
    messages.push(
      `No new creatives uploaded in ${daysWithoutNew} days — critical drought.`
    );
  } else if (isWarning) {
    messages.push(
      `${daysWithoutNew} days since last creative upload — approaching drought.`
    );
  }

  if (highFatigue) {
    messages.push(
      `${fatiguedCount} of ${totalActive} active creatives are burned or declining (${Math.round(fatiguedRatio * 100)}%).`
    );
  }

  return (
    <div className={`border rounded-xl px-5 py-4 flex items-start gap-3 ${styles.container}`}>
      <span className="text-xl flex-shrink-0" role="img" aria-label={level}>
        {styles.icon}
      </span>
      <div>
        <p className={`text-sm font-semibold mb-1 ${styles.title}`}>
          {level === "critical" ? "Creative Drought Critical" : "Creative Velocity Warning"}
        </p>
        <ul className={`text-sm space-y-0.5 ${styles.text}`}>
          {messages.map((msg, i) => (
            <li key={i}>{msg}</li>
          ))}
        </ul>
        <p className="text-xs text-gray-500 mt-2">
          Upload new creative assets to maintain performance.
        </p>
      </div>
    </div>
  );
}
