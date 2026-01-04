"use client";

import { useAuth } from "@/lib/hooks/useAuth";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { FileText, MessageSquare, Upload, TrendingUp } from "lucide-react";
import Link from "next/link";

/**
 * Dashboard Home Page
 * 
 * Shows:
 * - Welcome message
 * - Quick stats
 * - Quick action buttons
 */
export default function DashboardPage() {
  const { user } = useAuth();

  return (
    <div className="space-y-8">
      {/* Welcome section */}
      <div>
        <h1 className="text-3xl font-bold text-slate-900 dark:text-white">
          Welcome back, {user?.full_name || user?.username}! 👋
        </h1>
        <p className="mt-2 text-slate-600 dark:text-slate-400">
          Here's what's happening with your documents today.
        </p>
      </div>

      {/* Stats cards */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-slate-600 dark:text-slate-400">
              Total Documents
            </CardTitle>
            <FileText className="h-4 w-4 text-slate-600 dark:text-slate-400" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">0</div>
            <p className="text-xs text-slate-600 dark:text-slate-400 mt-1">
              No documents yet
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-slate-600 dark:text-slate-400">
              Chat Sessions
            </CardTitle>
            <MessageSquare className="h-4 w-4 text-slate-600 dark:text-slate-400" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">0</div>
            <p className="text-xs text-slate-600 dark:text-slate-400 mt-1">
              Start chatting with your docs
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-slate-600 dark:text-slate-400">
              Processing
            </CardTitle>
            <TrendingUp className="h-4 w-4 text-slate-600 dark:text-slate-400" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">0</div>
            <p className="text-xs text-slate-600 dark:text-slate-400 mt-1">
              All documents processed
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-slate-600 dark:text-slate-400">
              Storage Used
            </CardTitle>
            <Upload className="h-4 w-4 text-slate-600 dark:text-slate-400" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">0 MB</div>
            <p className="text-xs text-slate-600 dark:text-slate-400 mt-1">
              of unlimited
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Quick actions */}
      <Card>
        <CardHeader>
          <CardTitle>Quick Actions</CardTitle>
        </CardHeader>
        <CardContent className="flex flex-wrap gap-4">
          <Link href="/documents">
            <Button className="gap-2">
              <Upload className="h-4 w-4" />
              Upload Document
            </Button>
          </Link>
          <Link href="/chat">
            <Button variant="outline" className="gap-2">
              <MessageSquare className="h-4 w-4" />
              Start Chat
            </Button>
          </Link>
        </CardContent>
      </Card>

      {/* Getting started guide */}
      <Card>
        <CardHeader>
          <CardTitle>Getting Started</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex gap-4 items-start">
            <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-blue-100 text-blue-700 dark:bg-blue-900/20 dark:text-blue-400 font-semibold">
              1
            </div>
            <div>
              <h3 className="font-semibold text-slate-900 dark:text-white">
                Upload Your Documents
              </h3>
              <p className="text-sm text-slate-600 dark:text-slate-400 mt-1">
                Upload PDFs, DOCX, TXT, or JSON files to get started.
              </p>
            </div>
          </div>

          <div className="flex gap-4 items-start">
            <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-blue-100 text-blue-700 dark:bg-blue-900/20 dark:text-blue-400 font-semibold">
              2
            </div>
            <div>
              <h3 className="font-semibold text-slate-900 dark:text-white">
                Wait for Processing
              </h3>
              <p className="text-sm text-slate-600 dark:text-slate-400 mt-1">
                We'll process your documents and create embeddings for AI chat.
              </p>
            </div>
          </div>

          <div className="flex gap-4 items-start">
            <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-blue-100 text-blue-700 dark:bg-blue-900/20 dark:text-blue-400 font-semibold">
              3
            </div>
            <div>
              <h3 className="font-semibold text-slate-900 dark:text-white">
                Start Chatting
              </h3>
              <p className="text-sm text-slate-600 dark:text-slate-400 mt-1">
                Ask questions about your documents and get AI-powered answers with source citations.
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}