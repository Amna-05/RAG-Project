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
import { apiClient } from "@/lib/api/client";

interface ChatSession {
  id: string;
  title: string;
  created_at: string;
  updated_at: string;
}

interface Document {
  id: string;
  filename: string;
  status?: "pending" | "processing" | "completed" | "failed";
  num_chunks?: number;
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

        // Fetch documents
        const docsResponse = await apiClient.get("/rag/documents");
        const docsList = docsResponse.data || [];
        const formattedDocs = docsList.map((doc: { id: string; original_filename?: string; filename?: string; status?: string; num_chunks?: number }) => ({
          id: doc.id,
          filename: doc.original_filename || doc.filename,
          status: doc.status,
          num_chunks: doc.num_chunks,
        }));
        setDocuments(formattedDocs);

        // Fetch chat sessions
        const sessionsResponse = await apiClient.get("/rag/chat/sessions");
        const sessionsList = sessionsResponse.data || [];

        // Convert sessions to format with titles
        const formattedSessions = sessionsList.map((sessionId: string, index: number) => {
          // Try to extract timestamp from session ID if it's a timestamp-based ID
          let title = `Conversation ${sessionsList.length - index}`;

          // If session ID contains a timestamp (e.g., "session_1767689769")
          if (sessionId.includes('_')) {
            const parts = sessionId.split('_');
            const timestamp = parseInt(parts[parts.length - 1]);
            if (!isNaN(timestamp) && timestamp > 1000000000) {
              const date = new Date(timestamp * 1000);
              const now = new Date();
              const isToday = date.toDateString() === now.toDateString();

              if (isToday) {
                title = `Today ${date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}`;
              } else {
                title = date.toLocaleDateString([], { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' });
              }
            }
          }

          return {
            id: sessionId,
            title: title,
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString(),
          };
        });
        setChatSessions(formattedSessions);
      } catch (error) {
        console.error("Failed to load sidebar data:", error);
      } finally {
        setLoading(false);
      }
    };

    loadData();
  }, []);

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
          className="fixed inset-0 z-40 bg-black/50 md:hidden backdrop-blur-sm transition-all duration-300"
          onClick={onClose}
        />
      )}

      {/* Sidebar */}
      <aside
        className={cn(
          "fixed left-0 top-0 z-50 h-screen w-64 bg-gradient-to-b from-white to-slate-50 dark:from-slate-900 dark:to-slate-950 border-r border-slate-200 dark:border-slate-800 overflow-hidden flex flex-col transition-all duration-300 md:translate-x-0 shadow-xl md:shadow-lg",
          isOpen ? "translate-x-0" : "-translate-x-full"
        )}
        style={{ paddingTop: "4rem" }}
      >
        {/* Close button (mobile only) */}
        <Button
          variant="ghost"
          size="icon"
          className="absolute top-4 right-4 md:hidden hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
          onClick={onClose}
        >
          <X className="h-5 w-5" />
        </Button>

        {/* New Chat Button */}
        <div className="p-4 border-b border-slate-200 dark:border-slate-800">
          <Button
            onClick={handleNewChat}
            className="w-full gap-2 bg-gradient-to-r from-blue-600 to-blue-700 hover:from-blue-700 hover:to-blue-800 text-white shadow-lg hover:shadow-blue-500/50 transition-all duration-300 font-semibold rounded-lg"
          >
            <Plus className="h-4 w-4" />
            New Chat
          </Button>
        </div>

        {/* Main Content Area */}
        <div className="flex-1 overflow-y-auto scrollbar-thin scrollbar-thumb-slate-300 dark:scrollbar-thumb-slate-700">
          {/* Documents Section */}
          <div className="border-b border-slate-200 dark:border-slate-800">
            <button
              onClick={() => setShowDocuments(!showDocuments)}
              className="w-full flex items-center justify-between px-4 py-3 hover:bg-slate-100 dark:hover:bg-slate-800/50 transition-colors duration-200 group"
            >
              <div className="flex items-center gap-2">
                <FileText className="h-4 w-4 text-blue-600 dark:text-blue-400 group-hover:scale-110 transition-transform duration-200" />
                <span className="text-sm font-semibold text-slate-900 dark:text-white">
                  Documents
                </span>
                {documents.length > 0 && (
                  <span className="ml-1 inline-flex items-center justify-center px-2 py-0.5 rounded-full bg-gradient-to-r from-blue-100 to-blue-50 dark:from-blue-900/40 dark:to-blue-900/20 text-xs font-bold text-blue-700 dark:text-blue-300">
                    {documents.length}
                  </span>
                )}
              </div>
              <ChevronDown
                className={cn(
                  "h-4 w-4 text-slate-400 dark:text-slate-600 transition-all duration-300",
                  showDocuments && "rotate-180"
                )}
              />
            </button>

            {showDocuments && (
              <div className="px-2 py-3 space-y-1 bg-slate-50/50 dark:bg-slate-800/20 animate-in slide-in-from-top-2 duration-200">
                {documents.length === 0 ? (
                  <p className="px-3 py-2 text-xs text-slate-500 dark:text-slate-400 text-center">
                    No documents uploaded
                  </p>
                ) : (
                  documents.map((doc) => {
                    const statusColor =
                      doc.status === "completed"
                        ? "text-green-600 dark:text-green-400"
                        : doc.status === "processing"
                        ? "text-blue-600 dark:text-blue-400"
                        : doc.status === "failed"
                        ? "text-red-600 dark:text-red-400"
                        : "text-yellow-600 dark:text-yellow-400";

                    return (
                      <div
                        key={doc.id}
                        className="px-3 py-2.5 text-xs text-slate-700 dark:text-slate-300 hover:bg-blue-100 dark:hover:bg-blue-900/30 rounded-lg cursor-pointer transition-colors duration-200 group border border-transparent hover:border-blue-200 dark:hover:border-blue-800"
                        title={doc.filename}
                      >
                        <div className="flex items-center gap-2 mb-1">
                          <FileText className="h-3 w-3 text-blue-500 flex-shrink-0" />
                          <span className="truncate flex-1 font-medium">{doc.filename}</span>
                        </div>
                        <div className={`flex items-center gap-1 ml-5 ${statusColor}`}>
                          {doc.status === "completed" && "✓"}
                          {doc.status === "processing" && "⟳"}
                          {doc.status === "failed" && "✗"}
                          {doc.status === "pending" && "◦"}
                          <span>
                            {doc.status || "unknown"} {doc.num_chunks && `• ${doc.num_chunks} chunks`}
                          </span>
                        </div>
                      </div>
                    );
                  })
                )}
                <Link href="/documents">
                  <button className="w-full mt-2 px-3 py-2 text-xs font-semibold text-blue-600 dark:text-blue-400 hover:bg-blue-100 dark:hover:bg-blue-900/30 rounded-lg transition-all duration-200">
                    + Upload Document
                  </button>
                </Link>
              </div>
            )}
          </div>

          {/* Chat History Section */}
          <div className="flex-1">
            <div className="px-4 py-4 text-xs font-bold text-slate-600 dark:text-slate-500 uppercase tracking-widest">
              Chat History
            </div>

            {loading ? (
              <div className="px-4 py-2 space-y-2">
                {[1, 2, 3].map((i) => (
                  <div key={i} className="h-8 bg-slate-200 dark:bg-slate-700 rounded-lg animate-pulse" />
                ))}
              </div>
            ) : chatSessions.length === 0 ? (
              <div className="px-4 py-8 text-xs text-slate-500 dark:text-slate-400 text-center">
                <MessageSquare className="h-8 w-8 mx-auto text-slate-300 dark:text-slate-700 mb-2 opacity-50" />
                <p>No chats yet</p>
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
                        "w-full text-left px-3 py-2.5 rounded-lg text-sm truncate transition-all duration-200 flex items-center gap-2",
                        currentSessionId === session.id
                          ? "bg-gradient-to-r from-blue-600 to-blue-700 text-white shadow-md"
                          : "text-slate-700 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-slate-800/70"
                      )}
                      title={session.title}
                    >
                      <MessageSquare className="h-3.5 w-3.5 flex-shrink-0" />
                      <span className="flex-1 truncate">{session.title}</span>
                    </button>

                    {/* Delete button on hover */}
                    {hoveredSession === session.id && (
                      <button
                        onClick={() => handleDeleteSession(session.id)}
                        className="absolute right-2 top-1/2 -translate-y-1/2 p-1.5 rounded-lg hover:bg-red-100 dark:hover:bg-red-900/30 text-red-600 dark:text-red-400 opacity-0 group-hover:opacity-100 transition-all duration-200 hover:scale-110"
                      >
                        <Trash2 className="h-3.5 w-3.5" />
                      </button>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Settings Footer */}
        <div className="border-t border-slate-200 dark:border-slate-800 p-4 bg-gradient-to-t from-white dark:from-slate-950">
          <Link href="/settings">
            <Button
              variant="outline"
              className="w-full gap-2 justify-start text-slate-700 dark:text-slate-300 border-slate-200 dark:border-slate-700 hover:bg-slate-100 dark:hover:bg-slate-800 transition-all duration-200 font-semibold"
            >
              <Settings className="h-4 w-4" />
              Settings
            </Button>
          </Link>
        </div>
      </aside>

      <style jsx>{`
        .scrollbar-thin::-webkit-scrollbar {
          width: 6px;
        }
        .scrollbar-thumb-slate-300::-webkit-scrollbar-thumb {
          background-color: rgb(203, 213, 225);
          border-radius: 3px;
        }
        .scrollbar-thumb-slate-300::-webkit-scrollbar-thumb:hover {
          background-color: rgb(148, 163, 184);
        }
        .dark .scrollbar-thumb-slate-700::-webkit-scrollbar-thumb {
          background-color: rgb(55, 65, 81);
          border-radius: 3px;
        }
        .dark .scrollbar-thumb-slate-700::-webkit-scrollbar-thumb:hover {
          background-color: rgb(75, 85, 99);
        }
      `}</style>
    </>
  );
}