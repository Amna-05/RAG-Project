"use client";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { Toaster } from "sonner";
import { useState } from "react";

/**
 * Application providers
 * 
 * Wraps the entire app with:
 * - React Query (server state management)
 * - Toast notifications
 * - Theme provider (future: dark mode)
 */
export function Providers({ children }: { children: React.ReactNode }) {
  // Create QueryClient inside component to avoid sharing between requests
  const [queryClient] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            // Data stays fresh for 5 minutes
            staleTime: 5 * 60 * 1000,
            // Cache for 10 minutes
            gcTime: 10 * 60 * 1000,
            // Don't refetch on window focus by default
            refetchOnWindowFocus: false,
            // Retry failed requests once
            retry: 1,
          },
        },
      })
  );

  return (
    <QueryClientProvider client={queryClient}>
      {children}
      {/* Toast notifications - positioned top-right */}
      <Toaster position="top-right" richColors closeButton />
    </QueryClientProvider>
  );
}