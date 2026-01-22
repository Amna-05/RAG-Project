"use client";

import { LogOut, Settings, User, Menu } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { useAuth } from "@/lib/hooks/useAuth";
import Link from "next/link";
import { ThemeToggle } from "./ThemeToggle";

/**
 * Dashboard Header Component
 * 
 * Features:
 * - Logo and branding
 * - User avatar with dropdown menu
 * - Mobile menu toggle
 * - Logout functionality
 */
interface HeaderProps {
  onMenuClick?: () => void;
}

export function Header({ onMenuClick }: HeaderProps) {
  const { user, logout } = useAuth();

  // Get user initials for avatar
  const initials = user?.full_name
    ?.split(" ")
    .map((n) => n[0])
    .join("")
    .toUpperCase() || user?.username?.slice(0, 2).toUpperCase() || "U";

  return (
    <header className="sticky top-0 z-40 w-full border-b border-slate-200 dark:border-slate-800 bg-gradient-to-r from-white to-slate-50 dark:from-slate-900 dark:to-slate-800/50 backdrop-blur-xl shadow-sm">
      <div className="flex h-16 items-center px-4 md:px-6 lg:px-8 gap-4">
        {/* Mobile menu button */}
        <Button
          variant="ghost"
          size="icon"
          className="md:hidden hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors duration-200"
          onClick={onMenuClick}
        >
          <Menu className="h-5 w-5" />
        </Button>

        {/* Logo */}
        <Link href="/dashboard" className="flex items-center gap-3 group">
          <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-gradient-to-br from-blue-600 to-blue-700 text-white font-bold shadow-lg group-hover:shadow-blue-500/50 transition-all duration-300">
            R
          </div>
          <span className="hidden sm:inline-block font-bold text-lg bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent group-hover:from-blue-700 group-hover:to-purple-700 transition-all duration-300">
            RAG System
          </span>
        </Link>

        {/* Spacer */}
        <div className="flex-1" />

        {/* Theme Toggle */}
        <ThemeToggle />

        {/* User menu */}
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button
              variant="ghost"
              className="relative h-10 w-10 rounded-full hover:bg-slate-100 dark:hover:bg-slate-800 transition-all duration-200 hover:shadow-md"
            >
              <Avatar className="h-10 w-10 border-2 border-slate-200 dark:border-slate-700">
                <AvatarFallback className="bg-gradient-to-br from-blue-500 to-blue-600 text-white font-bold text-sm">
                  {initials}
                </AvatarFallback>
              </Avatar>
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent className="w-56" align="end">
            <DropdownMenuLabel className="py-3">
              <div className="flex flex-col space-y-2">
                <p className="text-sm font-bold text-slate-900 dark:text-white">
                  {user?.full_name || user?.username}
                </p>
                <p className="text-xs text-slate-500 dark:text-slate-400 break-all">
                  {user?.email}
                </p>
              </div>
            </DropdownMenuLabel>
            <DropdownMenuSeparator />
            <DropdownMenuItem
              asChild
              className="cursor-pointer hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors duration-200"
            >
              <Link href="/settings" className="flex items-center">
                <User className="mr-2 h-4 w-4 text-blue-600 dark:text-blue-400" />
                Profile
              </Link>
            </DropdownMenuItem>
            <DropdownMenuItem
              asChild
              className="cursor-pointer hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors duration-200"
            >
              <Link href="/settings" className="flex items-center">
                <Settings className="mr-2 h-4 w-4 text-blue-600 dark:text-blue-400" />
                Settings
              </Link>
            </DropdownMenuItem>
            <DropdownMenuSeparator />
            <DropdownMenuItem
              className="text-red-600 dark:text-red-400 cursor-pointer hover:bg-red-50 dark:hover:bg-red-900/20 transition-colors duration-200"
              onClick={logout}
            >
              <LogOut className="mr-2 h-4 w-4" />
              Log out
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    </header>
  );
}