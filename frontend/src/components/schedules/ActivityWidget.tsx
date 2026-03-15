"use client";

import Link from "next/link";
import { useSchedules } from "@/hooks/useSchedules";
import { Card } from "@/components/common/Card";
import { ActivityFeed } from "@/components/schedules/ActivityFeed";

export function ActivityWidget() {
  const { data: logs, isLoading } = useSchedules(5);

  if (isLoading || !logs || logs.length === 0) return null;

  return (
    <Card
      title="Automation Activity"
      subtitle="Recent scheduled runs"
    >
      <ActivityFeed logs={logs} compact />
      <Link
        href="/schedules"
        className="block mt-3 text-center text-[11px] text-amber-400 hover:text-amber-300 transition-colors"
      >
        View all activity →
      </Link>
    </Card>
  );
}
