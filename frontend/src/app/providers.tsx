"use client";

import { ReactNode, useState } from "react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { AccountProvider } from "@/contexts/AccountContext";
import { DateRangeProvider } from "@/contexts/DateRangeContext";

export function Providers({ children }: { children: ReactNode }) {
  const [queryClient] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            staleTime: 30 * 1000,
            retry: 2,
            refetchOnWindowFocus: false,
          },
        },
      })
  );

  return (
    <QueryClientProvider client={queryClient}>
      <AccountProvider>
        <DateRangeProvider>{children}</DateRangeProvider>
      </AccountProvider>
    </QueryClientProvider>
  );
}
