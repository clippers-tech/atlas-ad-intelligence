"use client";

import {
  createContext,
  useContext,
  useState,
  useMemo,
  type ReactNode,
} from "react";

interface DateRangeState {
  rangeKey: string;
  dateFrom: string | undefined;
  dateTo: string | undefined;
  setRangeKey: (key: string) => void;
}

const DateRangeContext = createContext<DateRangeState | null>(null);

/** Map range keys to number of days back from today.
 *  "1d" = Today only (0 days back), "7d" = last 7 days, etc. */
const RANGE_DAYS: Record<string, number> = {
  "1d": 0,
  "7d": 7,
  "14d": 14,
  "30d": 30,
};

function computeDates(key: string): {
  dateFrom: string | undefined;
  dateTo: string | undefined;
} {
  if (key === "all") return { dateFrom: undefined, dateTo: undefined };

  const days = RANGE_DAYS[key];
  if (days === undefined) return { dateFrom: undefined, dateTo: undefined };

  const to = new Date();
  const from = new Date();
  from.setDate(to.getDate() - days);

  return {
    dateFrom: from.toISOString().slice(0, 10),
    dateTo: to.toISOString().slice(0, 10),
  };
}

export function DateRangeProvider({ children }: { children: ReactNode }) {
  const [rangeKey, setRangeKey] = useState("7d");

  const value = useMemo<DateRangeState>(() => {
    const { dateFrom, dateTo } = computeDates(rangeKey);
    return { rangeKey, dateFrom, dateTo, setRangeKey };
  }, [rangeKey]);

  return (
    <DateRangeContext.Provider value={value}>
      {children}
    </DateRangeContext.Provider>
  );
}

export function useDateRange(): DateRangeState {
  const ctx = useContext(DateRangeContext);
  if (!ctx) throw new Error("useDateRange must be inside DateRangeProvider");
  return ctx;
}
