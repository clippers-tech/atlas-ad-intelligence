import { useQuery } from "@tanstack/react-query";
import { fetchData } from "@/lib/api";

export interface ScheduleLog {
  id: string;
  task_name: string;
  status: "running" | "completed" | "failed";
  source: string;
  summary: string | null;
  error_message: string | null;
  duration_ms: number | null;
  started_at: string;
  finished_at: string | null;
}

interface SchedulesResponse {
  data: ScheduleLog[];
  meta: { total: number; limit: number };
}

export function useSchedules(limit = 50) {
  return useQuery({
    queryKey: ["schedules", limit],
    queryFn: async () => {
      const res = await fetchData<SchedulesResponse>(
        "/schedules",
        { limit }
      );
      return res.data;
    },
    staleTime: 30_000,
    refetchInterval: 60_000,
  });
}
