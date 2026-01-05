"use client";

import { useState, useEffect } from "react";
import {
  Plus,
  MessageSquare,
  FileText,
  Settings,
  ChevronDown,
  Trash2,
  X,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { cn } from "@/lib/utils/cn";

interface ChatSession {
  id: string;
  title: string;
  created_at: string;
  updated_at: string;
}

interface Document {
  id: string;
  filename: string;
}

interface SidebarProps {
  isOpen?: boolean;
  onClose?: () => void;
}

/**
 * Dashboard Sidebar Component
 *
 * ChatGPT-like sidebar with:
 * - Add new chat button
 * - Chat history
 * - Documents section
 * - Settings link
 */
export function Sidebar({ isOpen = true, onClose }: SidebarProps) {
  const router = useRouter();
  const [showDocuments, setShowDocuments] = useState(true);
  const [chatSessions, setChatSessions] = useState<ChatSession[]>([]);
  const [documents, setDocuments] = useState<Document[]>([]);
  const [loading, setLoading] = useState(true);
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null);
  const [hoveredSession, setHoveredSession] = useState<string | null>(null);

  // Fetch chat sessions and documents on mount
  useEffect(() => {
    const loadData = async () => {
      try {
        setLoading(true);
        // TODO: Fetch from backend when endpoints are available
        // For now, use empty state
        setChatSessions([]);
        setDocuments([]);
      } catch (error) {
        console.error("Failed to load sidebar data:", error);
      } finally {
        setLoading(false);
      }
    };

    if (isOpen) {
      loadData();
    }
  }, [isOpen]);

  const handleNewChat = () => {
    // Navigate to new chat (no session_id in URL)
    router.push("/chat");
    setCurrentSessionId(null);
    onClose?.();
  };

  const handleSelectSession = (sessionId: string) => {
    // Navigate to chat with session_id
    router.push(`/chat?session_id=${sessionId}`);
    setCurrentSessionId(sessionId);
    onClose?.();
  };

  const handleDeleteSession = async (sessionId: string) => {
    try {
      // TODO: Implement delete on backend
      // await apiClient.delete(`/rag/sessions/${sessionId}`);
      setChatSessions((prev) => prev.filter((s) => s.id !== sessionId));
    } catch (error) {
      console.error("Failed to delete session:", error);
    }
  };

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
          "fixed left-0 top-0 z-50 h-screen w-64 bg-white dark:bg-slate-900 border-r border-slate-200 dark:border-slate-700 overflow-hidden flex flex-col transition-transform duration-300 md:translate-x-0",
          isOpen ? "translate-x-0" : "-translate-x-full"
        )}
        style={{ paddingTop: "4rem" }}
      >
        {/* Close button (mobile only) */}
        <Button
          variant="ghost"
          size="icon"
          className="absolute top-4 right-4 md:hidden"
          onClick={onClose}
        >
          <X className="h-5 w-5" />
        </Button>

        {/* New Chat Button */}
        <div className="p-4 border-b border-slate-200 dark:border-slate-700">
          <Button
            onClick={handleNewChat}
            className="w-full gap-2 bg-slate-900 hover:bg-slate-800 dark:bg-slate-700 dark:hover:bg-slate-600 text-white"
          >
            <Plus className="h-4 w-4" />
            New Chat
          </Button>
        </div>

        {/* Main Content Area */}
        <div className="flex-1 overflow-y-auto">
          {/* Documents Section */}
          <div className="border-b border-slate-200 dark:border-slate-700">
            <button
              onClick={() => setShowDocuments(!showDocuments)}
              className="w-full flex items-center justify-between px-4 py-3 hover:bg-slate-50 dark:hover:bg-slate-800/50 transition"
            >
              <div className="flex items-center gap-2">
                <FileText className="h-4 w-4 text-slate-500" />
                <span className="text-sm font-medium text-slate-900 dark:text-white">
                  Documents
                </span>
                {documents.length > 0 && (
                  <span className="ml-1 inline-flex items-center justify-center px-2 py-0.5 rounded-full bg-blue-100 dark:bg-blue-900/30 text-xs font-medium text-blue-700 dark:text-blue-300">
                    {documents.length}
                  </span>
                )}
              </div>
              <ChevronDown
                className={cn(
                  "h-4 w-4 text-slate-400 transition-transform",
                  showDocuments && "rotate-180"
                )}
              />
            </button>

            {showDocuments && (
              <div className="px-2 py-2 space-y-1">
                {documents.length === 0 ? (
                  <p className="px-2 py-2 text-xs text-slate-500 dark:text-slate-400">
                    No documents uploaded
                  </p>
                ) : (
                  documents.map((doc) => (
                    <div
                      key={doc.id}
                      className="px-2 py-1.5 text-xs text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800 rounded truncate cursor-pointer"
                      title={doc.filename}
                    >
                      {doc.filename}
                    </div>
                  ))
                )}
                <Link href="/documents">
                  <button className="w-full mt-2 px-2 py-1.5 text-xs text-blue-600 dark:text-blue-400 hover:bg-blue-50 dark:hover:bg-blue-900/20 rounded">
                    + Upload Document
                  </button>
                </Link>
              </div>
            )}
          </div>

          {/* Chat History Section */}
          <div className="flex-1">
            <div className="px-4 py-3 text-xs font-medium text-slate-500 dark:text-slate-400 uppercase tracking-wider">
              Chat History
            </div>

            {loading ? (
              <div className="px-4 py-2">
                <div className="h-2 bg-slate-200 dark:bg-slate-700 rounded animate-pulse" />
              </div>
            ) : chatSessions.length === 0 ? (
              <div className="px-4 py-4 text-xs text-slate-500 dark:text-slate-400 text-center">
                No chats yet. Start a new conversation!
              </div>
            ) : (
              <div className="space-y-1 px-2 py-2">
                {chatSessions.map((session) => (
                  <div
                    key={session.id}
                    className="group relative"
                    onMouseEnter={() => setHoveredSession(session.id)}
                    onMouseLeave={() => setHoveredSession(null)}
                  >
                    <button
                      onClick={() => handleSelectSession(session.id)}
                      className={cn(
                        "w-full text-left px-3 py-2 rounded text-sm truncate transition",
                        currentSessionId === session.id
                          ? "bg-blue-600 text-white"
                          : "text-slate-700 dark:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800"
                      )}
                      title={session.title}
                    >
                      <MessageSquare className="inline h-3 w-3 mr-2" />
                      {session.title}
                    </button>

                    {/* Delete button on hover */}
                    {hoveredSession === session.id && (
                      <button
                        onClick={() => handleDeleteSession(session.id)}
                        className="absolute right-2 top-1/2 -translate-y-1/2 p-1 rounded hover:bg-red-100 dark:hover:bg-red-900/30 text-red-600 dark:text-red-400 opacity-0 group-hover:opacity-100 transition"
                      >
                        <Trash2 className="h-3 w-3" />
                      </button>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Settings Footer */}
        <div className="border-t border-slate-200 dark:border-slate-700 p-4">
          <Link href="/settings">
            <Button
              variant="outline"
              className="w-full gap-2 justify-start text-slate-700 dark:text-slate-200"
            >
              <Settings className="h-4 w-4" />
              Settings
            </Button>
          </Link>
        </div>
      </aside>
    </>
  );
}