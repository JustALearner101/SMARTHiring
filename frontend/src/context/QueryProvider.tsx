"use client";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import React, { useState } from "react";

export function QueryProvider({ children }: { children: React.ReactNode }) {
  // Stable query client per browser session
  const [queryClient] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            // Data remains fresh for 1 minute — navigating back and forth within 1 minute
            // is instant (0ms loading) without hitting the backend server again!
            staleTime: 60 * 1000,
            // Keep unused cache data in memory for 5 minutes
            gcTime: 5 * 60 * 1000,
            // Do not refetch when switching browser tabs/windows
            refetchOnWindowFocus: false,
            // Retry failed requests at most once
            retry: 1,
          },
        },
      })
  );

  return (
    <QueryClientProvider client={queryClient}>
      {children}
    </QueryClientProvider>
  );
}
