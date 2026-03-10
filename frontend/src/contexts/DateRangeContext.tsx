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

function computeDates(key: string): {
  dateFrom: string | undefined;
  dateTo: string | undefined;
} {
  if (key === "all") return { dateFrom: undefined, dateTo: undefined };

  const days = parseInt(key, 10);
  if (isNaN(days)) return { dateFrom: undefined, dateTo: undefined };

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
