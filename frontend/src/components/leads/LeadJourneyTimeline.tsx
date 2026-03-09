"use client";

import type { JourneyEvent } from "@/lib/types";
import { formatDateTime } from "@/lib/utils";

interface LeadJourneyTimelineProps {
  events: JourneyEvent[];
}

const EVENT_ICONS: Record<string, string> = {
  click: "🖱️",
  landing_page: "📄",
  booking: "📅",
  call: "📞",
  proposal: "📋",
  payment: "💰",
  lead: "🆕",
  form_submit: "📝",
  email: "📧",
  page_view: "👁️",
};

function getIcon(type: string): string {
  return EVENT_ICONS[type] ?? "📌";
}

function getDotColor(type: string): string {
  const colors: Record<string, string> = {
    click: "bg-blue-500",
    landing_page: "bg-cyan-500",
    booking: "bg-violet-500",
    call: "bg-amber-500",
    proposal: "bg-orange-500",
    payment: "bg-emerald-500",
    lead: "bg-blue-400",
    form_submit: "bg-indigo-500",
    email: "bg-sky-500",
    page_view: "bg-gray-500",
  };
  return colors[type] ?? "bg-gray-500";
}

export default function LeadJourneyTimeline({ events }: LeadJourneyTimelineProps) {
  if (!events || events.length === 0) {
    return (
      <div className="text-center py-8 text-gray-500 text-sm">
        No journey events recorded yet.
      </div>
    );
  }

  return (
    <div className="relative">
      {/* Vertical line */}
      <div className="absolute left-4 top-0 bottom-0 w-px bg-gray-700" />

      <ol className="space-y-6">
        {events.map((event, idx) => (
          <li key={idx} className="relative flex gap-4 pl-10">
            {/* Dot */}
            <span
              className={`absolute left-2 top-1 w-5 h-5 rounded-full flex items-center justify-center text-xs ${getDotColor(event.type)} ring-2 ring-gray-900`}
              aria-hidden="true"
            >
              <span>{getIcon(event.type)}</span>
            </span>

            {/* Content */}
            <div className="flex-1 bg-gray-800/50 border border-gray-700/50 rounded-lg px-4 py-3">
              <div className="flex items-start justify-between gap-2">
                <div>
                  <p className="text-sm font-medium text-gray-200">
                    {event.description}
                  </p>
                  {event.details && (
                    <p className="text-xs text-gray-400 mt-1">{event.details}</p>
                  )}
                </div>
                <span className="text-xs text-gray-500 whitespace-nowrap flex-shrink-0">
                  {formatDateTime(event.timestamp)}
                </span>
              </div>
            </div>
          </li>
        ))}
      </ol>
    </div>
  );
}
