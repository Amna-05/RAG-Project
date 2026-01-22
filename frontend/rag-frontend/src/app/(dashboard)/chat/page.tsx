"use client";

import { useState, useRef, useEffect } from "react";
import { Send, Loader2, AlertCircle, RefreshCw, Zap, MessageSquare } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { toast } from "sonner";
import { apiClient, getErrorMessage, isRateLimitError } from "@/lib/api/client";
import { useSearchParams } from "next/navigation";

interface Message {
  id: string;
  role: "user" | "assistant" | "error";
  content: string;
  timestamp: Date;
  error?: {
    code?: string;
    suggestion?: string;
  };
}

/**
 * Chat Page with History & Documents
 *
 * Real chat interface with session history and document management
 */
export default function ChatPage() {
  const searchParams = useSearchParams();
  const sessionId = searchParams.get("session_id") || `session_${Date.now()}`;

  const [messages, setMessages] = useState<Message[]>([
    {
      id: "1",
      role: "assistant",
      content: "Hello! 👋 I'm your AI assistant. Ask me questions about your documents or anything else!",
      timestamp: new Date(),
    },
  ]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Load chat history if session_id is provided
  useEffect(() => {
    const loadHistory = async () => {
      if (sessionId && sessionId.startsWith("session_") === false) {
        // Don't load for new sessions (timestamp-based)
        await loadChatHistory();
      }
    };
    loadHistory();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [sessionId]);

  const loadChatHistory = async () => {
    if (!sessionId) return;

    try {
      const response = await apiClient.get(`/rag/chat/history/${sessionId}`);

      if (response.data.messages && response.data.messages.length > 0) {
        // Convert backend messages to frontend format
        const historyMessages = response.data.messages.map((msg: { role: string; content: string; created_at: string }, idx: number) => ({
          id: `${idx}`,
          role: msg.role as "user" | "assistant" | "error",
          content: msg.content,
          timestamp: new Date(msg.created_at),
        }));

        setMessages(historyMessages);
      }
    } catch (error) {
      console.error("Failed to load chat history:", error);
      // Don't show error to user for history loading
    }
  };

  // Scroll to bottom when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!input.trim()) return;

    // Add user message
    const userMessage: Message = {
      id: Date.now().toString(),
      role: "user",
      content: input,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setIsLoading(true);

    try {
      // Update URL with current sessionId if it's a new session
      if (typeof window !== 'undefined') {
        const currentUrl = new URLSearchParams(window.location.search).get('session_id');
        if (!currentUrl || currentUrl.startsWith('session_')) {
          const newUrl = new URL(window.location.href);
          newUrl.searchParams.set('session_id', sessionId);
          window.history.replaceState({}, '', newUrl.toString());
        }
      }

      // Call backend chat endpoint with current sessionId
      const response = await apiClient.post("/rag/chat", {
        message: input,
        session_id: sessionId,
      });

      const data = response.data;

      // Add assistant message
      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: data.message || "No response received",
        timestamp: new Date(),
      };

      setMessages((prev) => [...prev, assistantMessage]);
    } catch (error: unknown) {
      let errorMessage = getErrorMessage(error);
      let suggestion = "";
      let errorCode = "unknown";

      // Check if it's a rate limit error
      if (isRateLimitError(error)) {
        errorCode = "rate_limit";
        suggestion = "You've reached the chat limit. Please wait before trying again.";
      } else {
        // Log other errors to console for debugging
        console.error("Chat error:", error);
        // Handle specific error cases for other errors
        const axiosError = error as { response?: { status?: number; data?: { detail?: string; headers?: Record<string, string> }; headers?: Record<string, string> }; message?: string };
        if (axiosError.response?.data?.detail) {
          const detail = axiosError.response.data.detail.toLowerCase();

          if (detail.includes("quota") || detail.includes("limit") || detail.includes("exhausted")) {
            errorCode = "quota_exceeded";
            errorMessage = "🔑 Gemini API Quota Exceeded";
            suggestion = "The AI model's daily limit has been reached. Try again tomorrow.";
          } else if (detail.includes("token")) {
            errorCode = "token_limit";
            errorMessage = "⚠️ Token Limit Exceeded";
            suggestion = "The response would be too long. Try asking a more specific question.";
          } else if (detail.includes("connection") || detail.includes("network")) {
            errorCode = "network_error";
            errorMessage = "🌐 Network Connection Error";
            suggestion = "Unable to connect to the AI service. Check your internet connection.";
          } else if (detail.includes("no document") || detail.includes("not found")) {
            errorCode = "no_documents";
            errorMessage = "📄 No Documents Found";
            suggestion = "You can still chat with the AI! Upload documents for document-specific questions.";
          } else {
            suggestion = "Please try again or contact support if the issue persists.";
          }
        } else {
          suggestion = "Please try again or contact support.";
        }
      }

      // Add error message to chat
      const errorMsg: Message = {
        id: (Date.now() + 2).toString(),
        role: "error",
        content: errorMessage,
        timestamp: new Date(),
        error: {
          code: errorCode,
          suggestion,
        },
      };

      setMessages((prev) => [...prev, errorMsg]);
      toast.error(errorMessage, {
        duration: isRateLimitError(error) ? 5000 : 4000,
        icon: errorCode === "rate_limit" ? "⏳" : "❌",
      });

      setIsLoading(false);
    } finally {
      setIsLoading(false);
    }
  };

  // Retry last message
  const handleRetry = () => {
    const lastUserMessage = messages
      .reverse()
      .find((m) => m.role === "user");

    if (lastUserMessage) {
      // Remove error messages
      setMessages((prev) =>
        prev.filter((m) => m.role !== "error" && m.id !== lastUserMessage.id + "1")
      );
      setInput(lastUserMessage.content);
      // Message will be sent by the user clicking send again
    }
  };

  return (
    <div className="flex flex-col h-full gap-2">
      {/* Chat Header - Minimal */}
      <div className="animate-fade-in flex-shrink-0 py-1">
        <h1 className="text-xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
          Chat
        </h1>
      </div>

      {/* Messages Container */}
      <div className="flex-1 rounded-xl border border-slate-200 dark:border-slate-700 bg-gradient-to-br from-white to-blue-50 dark:from-slate-800/50 dark:to-slate-900/50 overflow-y-auto p-4 space-y-4 shadow-sm flex flex-col">
        {messages.length === 1 && messages[0].role === "assistant" && (
          <div className="h-full flex items-center justify-center">
            <div className="text-center opacity-60">
              <MessageSquare className="h-16 w-16 mx-auto text-slate-400 dark:text-slate-600 mb-4" />
              <p className="text-slate-500 dark:text-slate-400 font-medium">
                Start a conversation by asking a question
              </p>
            </div>
          </div>
        )}

        {messages.map((message, index) => (
          <div
            key={message.id}
            className={`flex animate-message-in ${
              message.role === "user" ? "justify-end" : "justify-start"
            }`}
            style={{ animationDelay: `${index * 50}ms` }}
          >
            {message.role === "error" ? (
              <div className="max-w-xs lg:max-w-md xl:max-w-lg bg-gradient-to-br from-red-50 to-red-100/50 dark:from-red-900/20 dark:to-red-900/10 border border-red-200 dark:border-red-800 rounded-2xl p-4 shadow-md hover:shadow-lg transition-all duration-300">
                <div className="flex gap-3 mb-3">
                  <AlertCircle className="h-5 w-5 text-red-600 dark:text-red-400 flex-shrink-0 mt-0.5" />
                  <div className="flex-1">
                    <p className="font-semibold text-red-900 dark:text-red-200 text-sm">
                      {message.content}
                    </p>
                    {message.error?.suggestion && (
                      <p className="text-xs text-red-800 dark:text-red-300 mt-2 leading-relaxed">
                        💡 {message.error.suggestion}
                      </p>
                    )}
                    <div className="flex gap-2 mt-3 flex-wrap">
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={handleRetry}
                        className="gap-1 text-xs h-8 hover:bg-red-100 dark:hover:bg-red-900/30 transition-colors"
                      >
                        <RefreshCw className="h-3 w-3" />
                        Try Again
                      </Button>
                      {message.error?.code === "quota_exceeded" && (
                        <Button
                          size="sm"
                          variant="outline"
                          className="gap-1 text-xs h-8 hover:bg-red-100 dark:hover:bg-red-900/30 transition-colors"
                        >
                          <Zap className="h-3 w-3" />
                          Try Grok
                        </Button>
                      )}
                    </div>
                  </div>
                </div>
                <p className="text-xs text-red-700 dark:text-red-400 ml-8 opacity-75">
                  {message.timestamp.toLocaleTimeString([], {
                    hour: "2-digit",
                    minute: "2-digit",
                  })}
                </p>
              </div>
            ) : (
              <div
                className={`max-w-xs lg:max-w-md xl:max-w-lg px-5 py-3 rounded-2xl transition-all duration-300 shadow-sm hover:shadow-md ${
                  message.role === "user"
                    ? "bg-gradient-to-br from-blue-600 to-blue-700 text-white rounded-br-none"
                    : "bg-white dark:bg-slate-700/80 text-slate-900 dark:text-white rounded-bl-none border border-slate-200 dark:border-slate-600"
                }`}
              >
                <p className="text-sm leading-relaxed break-words">{message.content}</p>
                <p
                  className={`text-xs mt-2 font-medium opacity-70 ${
                    message.role === "user" ? "text-blue-100" : "text-slate-500 dark:text-slate-400"
                  }`}
                >
                  {message.timestamp.toLocaleTimeString([], {
                    hour: "2-digit",
                    minute: "2-digit",
                  })}
                </p>
              </div>
            )}
          </div>
        ))}

        {isLoading && (
          <div className="flex justify-start animate-message-in">
            <div className="bg-white dark:bg-slate-700/80 text-slate-900 dark:text-white rounded-2xl rounded-bl-none px-5 py-3 border border-slate-200 dark:border-slate-600 shadow-sm">
              <div className="flex items-center gap-3">
                <Loader2 className="h-4 w-4 animate-spin text-blue-600 dark:text-blue-400" />
                <span className="text-sm font-medium">Thinking...</span>
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input Form */}
      <form onSubmit={handleSendMessage} className="flex gap-2 flex-shrink-0">
        <div className="flex-1 relative group">
          <Input
            type="text"
            placeholder="Ask anything..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
            disabled={isLoading}
            className="flex-1 rounded-lg px-4 py-2.5 border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white placeholder-slate-400 dark:placeholder-slate-500 focus:border-blue-500 dark:focus:border-blue-400 focus:ring-2 focus:ring-blue-500/20 dark:focus:ring-blue-400/20 transition-all duration-300 disabled:opacity-50 text-sm"
          />
        </div>
        <Button
          type="submit"
          disabled={isLoading || !input.trim()}
          className="gap-1.5 rounded-lg px-4 py-2.5 bg-gradient-to-r from-blue-600 to-blue-700 hover:from-blue-700 hover:to-blue-800 text-white shadow-md hover:shadow-blue-500/50 transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed font-semibold text-sm flex-shrink-0"
        >
          {isLoading ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : (
            <Send className="h-4 w-4" />
          )}
          <span className="hidden sm:inline">Send</span>
        </Button>
      </form>

      <style jsx>{`
        @keyframes message-in {
          from {
            opacity: 0;
            transform: translateY(10px) scale(0.95);
          }
          to {
            opacity: 1;
            transform: translateY(0) scale(1);
          }
        }

        .animate-message-in {
          animation: message-in 0.3s ease-out forwards;
          opacity: 0;
        }

        .animate-fade-in {
          animation: fade-in 0.6s ease-out;
        }

        @keyframes fade-in {
          from {
            opacity: 0;
            transform: translateY(-10px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }
      `}</style>
    </div>
  );
}
