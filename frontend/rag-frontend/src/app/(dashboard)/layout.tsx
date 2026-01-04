"use client";

import { useState, useEffect } from "react";
import { Header } from "@/components/layout/Header";
import { Sidebar } from "@/components/layout/Sidebar";
import { useAuthStore } from "@/lib/store/authStore";

/**
 * Dashboard Layout - Protected Routes
 */
export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const { user, isAuthenticated } = useAuthStore();
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [mounted, setMounted] = useState(false);

  // Wait for client-side hydration
  useEffect(() => {
    setMounted(true);
  }, []);

  // Redirect if not authenticated (after mount)
  useEffect(() => {
    if (mounted && (!user || !isAuthenticated)) {
      console.log('🔴 [Dashboard] Not authenticated, redirecting');
      window.location.href = '/login';
    }
  }, [mounted, user, isAuthenticated]);

  // Show loading during SSR/hydration
  if (!mounted || !user || !isAuthenticated) {
    return (
      <div className="flex h-screen items-center justify-center bg-slate-50 dark:bg-slate-900">
        <div className="text-center">
          <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-blue-600 border-r-transparent"></div>
          <p className="mt-4 text-sm text-slate-600 dark:text-slate-400">
            Loading...
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex h-screen overflow-hidden bg-slate-50 dark:bg-slate-900">
      <Sidebar isOpen={sidebarOpen} onClose={() => setSidebarOpen(false)} />

      <div className="flex flex-1 flex-col overflow-hidden md:ml-64">
        <Header onMenuClick={() => setSidebarOpen(true)} />

        <main className="flex-1 overflow-y-auto p-4 md:p-6 lg:p-8">
          {children}
        </main>
      </div>
    </div>
  );
}