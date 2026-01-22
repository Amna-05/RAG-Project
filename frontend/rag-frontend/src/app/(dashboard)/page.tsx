"use client";
/* eslint-disable react/no-unescaped-entities */

import { FileText, MessageSquare, Zap, TrendingUp } from "lucide-react";
import { Button } from "@/components/ui/button";
import Link from "next/link";
import useAuthStore from "@/lib/store/authStore";

/**
 * Dashboard Home Page
 *
 * Overview of documents and recent chats
 */
export default function DashboardPage() {
  const { user } = useAuthStore();

  return (
    <div className="space-y-8">
      {/* Welcome Section */}
      <div>
        <h1 className="text-4xl font-bold text-slate-900 dark:text-white">
          Welcome back, {user?.username || "User"}!
        </h1>
        <p className="text-lg text-slate-600 dark:text-slate-400 mt-2">
          Here&apos;s what you can do with your documents
        </p>
      </div>

      {/* Quick Actions Grid */}
      <div className="grid md:grid-cols-3 gap-6">
        {/* Upload Document */}
        <Link href="/documents">
          <div className="rounded-lg border border-slate-200 dark:border-slate-700 p-6 hover:border-blue-400 dark:hover:border-blue-600 transition cursor-pointer h-full">
            <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-blue-100 dark:bg-blue-900/30 mb-4">
              <FileText className="h-6 w-6 text-blue-600 dark:text-blue-400" />
            </div>
            <h3 className="text-lg font-semibold text-slate-900 dark:text-white mb-2">
              My Documents
            </h3>
            <p className="text-slate-600 dark:text-slate-400 text-sm mb-4">
              Upload and manage your PDF, DOCX, and text files
            </p>
            <Button variant="outline" size="sm" className="w-full">
              Go to Documents
            </Button>
          </div>
        </Link>

        {/* Start Chat */}
        <Link href="/chat">
          <div className="rounded-lg border border-slate-200 dark:border-slate-700 p-6 hover:border-green-400 dark:hover:border-green-600 transition cursor-pointer h-full">
            <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-green-100 dark:bg-green-900/30 mb-4">
              <MessageSquare className="h-6 w-6 text-green-600 dark:text-green-400" />
            </div>
            <h3 className="text-lg font-semibold text-slate-900 dark:text-white mb-2">
              Chat with Docs
            </h3>
            <p className="text-slate-600 dark:text-slate-400 text-sm mb-4">
              Ask questions about your documents using AI
            </p>
            <Button variant="outline" size="sm" className="w-full">
              Start Chat
            </Button>
          </div>
        </Link>

        {/* Settings */}
        <Link href="/settings">
          <div className="rounded-lg border border-slate-200 dark:border-slate-700 p-6 hover:border-purple-400 dark:hover:border-purple-600 transition cursor-pointer h-full">
            <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-purple-100 dark:bg-purple-900/30 mb-4">
              <Zap className="h-6 w-6 text-purple-600 dark:text-purple-400" />
            </div>
            <h3 className="text-lg font-semibold text-slate-900 dark:text-white mb-2">
              Settings
            </h3>
            <p className="text-slate-600 dark:text-slate-400 text-sm mb-4">
              Manage your profile and preferences
            </p>
            <Button variant="outline" size="sm" className="w-full">
              Go to Settings
            </Button>
          </div>
        </Link>
      </div>

      {/* Stats Section */}
      <div className="rounded-lg border border-slate-200 dark:border-slate-700 p-6 bg-slate-50 dark:bg-slate-800/50">
        <div className="flex items-center gap-2 mb-6">
          <TrendingUp className="h-5 w-5 text-blue-600 dark:text-blue-400" />
          <h2 className="text-xl font-semibold text-slate-900 dark:text-white">
            Your Stats
          </h2>
        </div>
        <div className="grid md:grid-cols-3 gap-4">
          <div>
            <p className="text-slate-600 dark:text-slate-400 text-sm">Documents</p>
            <p className="text-3xl font-bold text-slate-900 dark:text-white">0</p>
          </div>
          <div>
            <p className="text-slate-600 dark:text-slate-400 text-sm">Conversations</p>
            <p className="text-3xl font-bold text-slate-900 dark:text-white">0</p>
          </div>
          <div>
            <p className="text-slate-600 dark:text-slate-400 text-sm">Questions Asked</p>
            <p className="text-3xl font-bold text-slate-900 dark:text-white">0</p>
          </div>
        </div>
      </div>

      {/* Help Section */}
      <div className="rounded-lg border-l-4 border-blue-500 bg-blue-50 dark:bg-blue-900/20 p-4">
        <p className="text-sm text-blue-900 dark:text-blue-200">
          <strong>Getting started:</strong> Upload your first document to begin asking questions with AI. Our system will analyze your documents and provide accurate answers with source citations.
        </p>
      </div>
    </div>
  );
}
