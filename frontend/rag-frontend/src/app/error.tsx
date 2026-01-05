"use client";

import { useEffect } from "react";
import { Button } from "@/components/ui/button";
import { AlertTriangle } from "lucide-react";

/**
 * Error Boundary Component
 *
 * Catches errors in the app and displays a user-friendly error page
 * Allows users to retry or go home
 */
export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    // Log error to console in development
    console.error("Application error:", error);
  }, [error]);

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-900 dark:to-slate-800 flex items-center justify-center px-4">
      <div className="text-center max-w-md">
        <div className="flex justify-center mb-6">
          <div className="flex h-16 w-16 items-center justify-center rounded-full bg-yellow-100 dark:bg-yellow-900/30">
            <AlertTriangle className="h-8 w-8 text-yellow-600 dark:text-yellow-400" />
          </div>
        </div>

        <h1 className="text-4xl font-bold text-slate-900 dark:text-white mb-2">
          Something went wrong
        </h1>
        <p className="text-slate-600 dark:text-slate-400 mb-4">
          We encountered an unexpected error. Our team has been notified.
        </p>

        {process.env.NODE_ENV === "development" && error.message && (
          <div className="mb-6 p-4 bg-red-50 dark:bg-red-900/20 rounded-lg border border-red-200 dark:border-red-800">
            <p className="text-sm text-red-600 dark:text-red-400 font-mono break-words">
              {error.message}
            </p>
          </div>
        )}

        <div className="flex gap-4 justify-center">
          <Button onClick={reset}>Try again</Button>
          <Button variant="outline" onClick={() => (window.location.href = "/")}>
            Go to Home
          </Button>
        </div>
      </div>
    </div>
  );
}
