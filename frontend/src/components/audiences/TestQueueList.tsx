"use client";

interface TestQueueEntry {
  id: string;
  name: string;
  audience_type: string;
  status: "queued" | "active" | "killed" | "graduated";
  created_at: string;
  notes?: string;
}

interface TestQueueListProps {
  tests: TestQueueEntry[];
}

const STATUS_CONFIG: Record<
  TestQueueEntry["status"],
  { label: string; className: string; icon: string }
> = {
  queued: {
    label: "Queued",
    className: "bg-blue-500/20 text-blue-400 border-blue-500/30",
    icon: "⏳",
  },
  active: {
    label: "Active",
    className: "bg-emerald-500/20 text-emerald-400 border-emerald-500/30",
    icon: "▶️",
  },
  killed: {
    label: "Killed",
    className: "bg-red-500/20 text-red-400 border-red-500/30",
    icon: "❌",
  },
  graduated: {
    label: "Graduated",
    className: "bg-violet-500/20 text-violet-400 border-violet-500/30",
    icon: "🎓",
  },
};

const STATUS_ORDER: TestQueueEntry["status"][] = [
  "active",
  "queued",
  "graduated",
  "killed",
];

export function TestQueueList({ tests }: TestQueueListProps) {
  if (!tests || tests.length === 0) {
    return (
      <div className="bg-[#141414] border border-[#262626] rounded-xl p-6 text-center text-gray-500 text-sm">
        No tests in queue
      </div>
    );
  }

  const grouped = STATUS_ORDER.reduce<Record<string, TestQueueEntry[]>>(
    (acc, status) => {
      acc[status] = tests.filter((t) => t.status === status);
      return acc;
    },
    {}
  );

  return (
    <div className="bg-[#141414] border border-[#262626] rounded-xl overflow-hidden">
      <div className="px-6 py-4 border-b border-[#262626]">
        <h3 className="text-sm font-semibold text-white">
          Audience Test Queue
        </h3>
      </div>
      <div className="divide-y divide-[#262626]">
        {STATUS_ORDER.filter((s) => grouped[s]?.length > 0).map((status) => {
          const config = STATUS_CONFIG[status];
          return (
            <div key={status} className="px-6 py-4">
              <div className="flex items-center gap-2 mb-3">
                <span>{config.icon}</span>
                <span
                  className={`inline-flex items-center px-2 py-0.5 rounded-full border text-xs font-medium ${config.className}`}
                >
                  {config.label}
                </span>
                <span className="text-xs text-gray-500">
                  {grouped[status].length} test{grouped[status].length !== 1 ? "s" : ""}
                </span>
              </div>
              <div className="flex flex-col gap-2">
                {grouped[status].map((test) => (
                  <div
                    key={test.id}
                    className="flex items-center justify-between gap-4 bg-[#1a1a1a] rounded-lg px-4 py-2.5"
                  >
                    <div className="flex-1 min-w-0">
                      <p className="text-sm text-gray-200 font-medium truncate">
                        {test.name}
                      </p>
                      {test.notes && (
                        <p className="text-xs text-gray-500 mt-0.5 truncate">
                          {test.notes}
                        </p>
                      )}
                    </div>
                    <span className="text-xs text-gray-500 capitalize flex-shrink-0">
                      {test.audience_type}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
