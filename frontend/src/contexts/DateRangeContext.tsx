"use client";

import {
  createContext,
  useContext,
  useState,
  useCallback,
  useMemo,
  ReactNode,
} from "react";

type RangeKey = "1d" | "7d" | "14d" | "30d" | "all";

interface DateRangeContextType {
  rangeKey: RangeKey;
  setRangeKey: (key: RangeKey) => void;
  dateFrom: string | undefined;
  dateTo: string | undefined;
}

const DateRangeContext = createContext<DateRangeContextType>({
  rangeKey: "7d",
  setRangeKey: () => {},
  dateFrom: undefined,
  dateTo: undefined,
});

function computeDates(key: RangeKey): {
  dateFrom: string | undefined;
  dateTo: string | undefined;
} {
  if (key === "all") return { dateFrom: undefined, dateTo: undefined };

  const now = new Date();
  const to = now.toISOString().slice(0, 10);

  const days = key === "1d" ? 0 : parseInt(key, 10);
  const from = new Date(now);
  from.setDate(from.getDate() - days);
  return { dateFrom: from.toISOString().slice(0, 10), dateTo: to };
}

export function DateRangeProvider({ children }: { children: ReactNode }) {
  const [rangeKey, setRangeKeyState] = useState<RangeKey>("7d");

  const setRangeKey = useCallback((key: RangeKey) => {
    setRangeKeyState(key);
  }, []);

  const { dateFrom, dateTo } = useMemo(
    () => computeDates(rangeKey),
    [rangeKey]
  );

  return (
    <DateRangeContext.Provider
      value={{ rangeKey, setRangeKey, dateFrom, dateTo }}
    >
      {children}
    </DateRangeContext.Provider>
  );
}

export function useDateRange() {
  return useContext(DateRangeContext);
}
