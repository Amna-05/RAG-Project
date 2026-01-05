import Link from "next/link";
import { Button } from "@/components/ui/button";
import { AlertCircle } from "lucide-react";

/**
 * 404 Not Found Page
 *
 * Displayed when a user navigates to a non-existent route
 */
export default function NotFound() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-900 dark:to-slate-800 flex items-center justify-center px-4">
      <div className="text-center max-w-md">
        <div className="flex justify-center mb-6">
          <div className="flex h-16 w-16 items-center justify-center rounded-full bg-red-100 dark:bg-red-900/30">
            <AlertCircle className="h-8 w-8 text-red-600 dark:text-red-400" />
          </div>
        </div>

        <h1 className="text-4xl font-bold text-slate-900 dark:text-white mb-2">
          404
        </h1>
        <h2 className="text-2xl font-bold text-slate-900 dark:text-white mb-4">
          Page not found
        </h2>
        <p className="text-slate-600 dark:text-slate-400 mb-8">
          The page you're looking for doesn't exist or has been moved. Let's get
          you back on track.
        </p>

        <div className="flex gap-4 justify-center">
          <Link href="/">
            <Button>Go to Home</Button>
          </Link>
          <Link href="/dashboard">
            <Button variant="outline">Go to Dashboard</Button>
          </Link>
        </div>
      </div>
    </div>
  );
}
