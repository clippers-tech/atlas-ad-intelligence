"use client";

import { useState, useMemo } from "react";

export type SortDir = "asc" | "desc";

export interface SortState<K extends string> {
  key: K;
  dir: SortDir;
}

/**
 * Generic hook for client-side table sorting.
 * Click once → desc, click again → asc, click a different column → desc.
 */
export function useTableSort<T, K extends string>(
  data: T[],
  defaultKey: K,
  defaultDir: SortDir = "desc"
) {
  const [sort, setSort] = useState<SortState<K>>({
    key: defaultKey,
    dir: defaultDir,
  });

  const toggle = (key: K) => {
    setSort((prev) =>
      prev.key === key
        ? { key, dir: prev.dir === "desc" ? "asc" : "desc" }
        : { key, dir: "desc" }
    );
  };

  const sorted = useMemo(() => {
    const k = sort.key as string;
    return [...data].sort((a, b) => {
      const av = (a as Record<string, unknown>)[k];
      const bv = (b as Record<string, unknown>)[k];
      const na = typeof av === "number" ? av : 0;
      const nb = typeof bv === "number" ? bv : 0;
      return sort.dir === "desc" ? nb - na : na - nb;
    });
  }, [data, sort]);

  return { sorted, sort, toggle };
}
