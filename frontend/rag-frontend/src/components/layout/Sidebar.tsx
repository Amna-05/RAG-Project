"use client";

import { cn } from "@/lib/utils/cn";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { LayoutDashboard, FileText, MessageSquare, Settings, X } from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";

/**
 * Dashboard Sidebar Component
 * 
 * Features:
 * - Navigation links
 * - Active route highlighting
 * - Mobile responsive (can be toggled)
 * - Smooth transitions
 */
interface SidebarProps {
  isOpen?: boolean;
  onClose?: () => void;
}

const navigation = [
  {
    name: "Dashboard",
    href: "/dashboard",
    icon: LayoutDashboard,
  },
  {
    name: "Documents",
    href: "/documents",
    icon: FileText,
  },
  {
    name: "Chat",
    href: "/chat",
    icon: MessageSquare,
  },
  {
    name: "Settings",
    href: "/settings",
    icon: Settings,
  },
];

export function Sidebar({ isOpen = true, onClose }: SidebarProps) {
  const pathname = usePathname();

  return (
    <>
      {/* Mobile overlay */}
      {isOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/50 md:hidden"
          onClick={onClose}
        />
      )}

      {/* Sidebar */}
      <aside
        className={cn(
          "fixed left-0 top-0 z-40 h-screen w-64 border-r bg-white dark:bg-slate-900 dark:border-slate-800 transition-transform duration-300 md:translate-x-0",
          isOpen ? "translate-x-0" : "-translate-x-full"
        )}
      >
        <div className="flex h-16 items-center justify-between px-4 border-b dark:border-slate-800">
          <Link href="/dashboard" className="flex items-center gap-2">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-blue-600 text-white font-bold">
              R
            </div>
            <span className="font-semibold text-lg">RAG System</span>
          </Link>
          <Button
            variant="ghost"
            size="icon"
            className="md:hidden"
            onClick={onClose}
          >
            <X className="h-5 w-5" />
          </Button>
        </div>

        <ScrollArea className="h-[calc(100vh-4rem)] px-3 py-4">
          <nav className="space-y-2">
            {navigation.map((item) => {
              const isActive = pathname === item.href || pathname?.startsWith(item.href + "/");
              const Icon = item.icon;

              return (
                <Link key={item.href} href={item.href} onClick={onClose}>
                  <Button
                    variant={isActive ? "secondary" : "ghost"}
                    className={cn(
                      "w-full justify-start",
                      isActive && "bg-blue-50 text-blue-700 hover:bg-blue-100 dark:bg-blue-900/20 dark:text-blue-400"
                    )}
                  >
                    <Icon className="mr-2 h-5 w-5" />
                    {item.name}
                  </Button>
                </Link>
              );
            })}
          </nav>

          {/* Stats card (optional) */}
          <div className="mt-8 rounded-lg bg-gradient-to-br from-blue-50 to-blue-100 dark:from-blue-900/20 dark:to-blue-800/20 p-4">
            <h3 className="font-semibold text-sm text-slate-900 dark:text-white mb-2">
              💡 Quick Tip
            </h3>
            <p className="text-xs text-slate-600 dark:text-slate-400">
              Upload documents to start chatting with AI about your files!
            </p>
          </div>
        </ScrollArea>
      </aside>
    </>
  );
}