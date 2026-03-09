"use client";

interface LoadingSpinnerProps {
  size?: number;
  label?: string;
  fullHeight?: boolean;
}

export function LoadingSpinner({
  size = 32,
  label = "Loading...",
  fullHeight = false,
}: LoadingSpinnerProps) {
  return (
    <div
      className={[
        "flex flex-col items-center justify-center gap-3",
        fullHeight ? "min-h-[60vh]" : "py-12",
      ].join(" ")}
    >
      <svg
        width={size}
        height={size}
        viewBox="0 0 24 24"
        fill="none"
        className="animate-spin text-blue-500"
        aria-hidden="true"
      >
        <circle
          cx="12"
          cy="12"
          r="10"
          stroke="currentColor"
          strokeWidth="2.5"
          strokeLinecap="round"
          strokeDasharray="31.416"
          strokeDashoffset="23.562"
          className="opacity-20"
        />
        <path
          d="M12 2a10 10 0 0 1 10 10"
          stroke="currentColor"
          strokeWidth="2.5"
          strokeLinecap="round"
        />
      </svg>
      {label && (
        <p className="text-sm text-gray-500">{label}</p>
      )}
    </div>
  );
}
