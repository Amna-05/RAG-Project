"use client";

import { useState, useRef, useEffect } from "react";
import { Send, Loader2, AlertCircle, RefreshCw, Zap } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { toast } from "sonner";
import { apiClient } from "@/lib/api/client";
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
 * Chat Page
 *
 * Real chat interface for asking questions about documents
 */
export default function ChatPage() {
  const searchParams = useSearchParams();
  const sessionId = searchParams.get("session_id");

  const [messages, setMessages] = useState<Message[]>([
    {
      id: "1",
      role: "assistant",
      content: "Hello! 👋 I'm your AI assistant. You can ask me questions about your documents, or just chat with me about any topic! Upload documents to get document-specific answers with citations.",
      timestamp: new Date(),
    },
  ]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Load chat history if session_id is provided
  useEffect(() => {
    if (sessionId) {
      const loadChatHistory = async () => {
        try {
          // TODO: Implement chat history endpoint on backend
          // const response = await apiClient.get(`/rag/sessions/${sessionId}/messages`);
          // setMessages(response.data.messages || []);
        } catch (error) {
          console.error("Failed to load chat history:", error);
        }
      };

      loadChatHistory();
    }
  }, [sessionId]);

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
      // Generate session_id if not provided (new chat)
      const sessionId = typeof window !== 'undefined'
        ? new URLSearchParams(window.location.search).get('session_id') || `session_${Date.now()}`
        : `session_${Date.now()}`;

      // Call backend chat endpoint
      const response = await apiClient.post("/rag/chat", {
        message: input,
        session_id: sessionId,
      });

      const data = response.data;

      // Add assistant message
      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: data.response || data.answer || "No response received",
        timestamp: new Date(),
      };

      setMessages((prev) => [...prev, assistantMessage]);
    } catch (error: unknown) {
      console.error("Chat error:", error);

      let errorMessage = "Failed to get response";
      let suggestion = "";
      let errorCode = "unknown";

      // Handle specific error cases
      const axiosError = error as { response?: { status?: number; data?: { detail?: string; headers?: Record<string, string> }; headers?: Record<string, string> }; message?: string };
      if (axiosError.response?.status === 429) {
        errorCode = "rate_limit";
        errorMessage = "⏳ Rate limit exceeded";
        suggestion = "You've reached the chat limit. Please wait a moment before trying again.";
      } else if (axiosError.response?.data?.detail) {
        const detail = axiosError.response.data.detail.toLowerCase();

        if (detail.includes("quota") || detail.includes("limit") || detail.includes("exhausted")) {
          errorCode = "quota_exceeded";
          errorMessage = "🔑 Gemini API Quota Exceeded";
          suggestion = "The AI model's daily limit has been reached. Try again tomorrow or use the Grok model for alternative responses.";
        } else if (detail.includes("token")) {
          errorCode = "token_limit";
          errorMessage = "⚠️ Token Limit Exceeded";
          suggestion = "The response would be too long. Try asking a more specific question or breaking it into smaller parts.";
        } else if (detail.includes("connection") || detail.includes("network")) {
          errorCode = "network_error";
          errorMessage = "🌐 Network Connection Error";
          suggestion = "Unable to connect to the AI service. Check your internet connection and try again.";
        } else if (detail.includes("no document") || detail.includes("not found")) {
          errorCode = "no_documents";
          errorMessage = "📄 No Documents Found";
          suggestion = "You can still chat with the AI! It will provide general knowledge answers. Upload documents to enable document-specific questions.";
        } else {
          errorMessage = detail;
          suggestion = "Please try again or contact support if the issue persists.";
        }
      } else if (axiosError.message) {
        errorMessage = axiosError.message;
        suggestion = "Please try again or contact support.";
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
      toast.error(errorMessage);

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
    <div className="flex flex-col h-full gap-4">
      {/* Chat Header */}
      <div>
        <h1 className="text-3xl font-bold text-slate-900 dark:text-white">
          Chat with AI
        </h1>
        <p className="text-slate-600 dark:text-slate-400">
          Chat freely or ask questions about your documents. Upload documents to get document-specific answers with citations.
        </p>
      </div>

      {/* Messages Container */}
      <div className="flex-1 rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800/50 overflow-y-auto p-4 space-y-4">
        {messages.map((message) => (
          <div
            key={message.id}
            className={`flex ${
              message.role === "user" ? "justify-end" : "justify-start"
            }`}
          >
            {message.role === "error" ? (
              <div className="max-w-xs lg:max-w-md xl:max-w-lg bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-3">
                <div className="flex gap-2 mb-2">
                  <AlertCircle className="h-5 w-5 text-red-600 dark:text-red-400 flex-shrink-0 mt-0.5" />
                  <div className="flex-1">
                    <p className="font-medium text-red-900 dark:text-red-200 text-sm">
                      {message.content}
                    </p>
                    {message.error?.suggestion && (
                      <p className="text-xs text-red-800 dark:text-red-300 mt-2">
                        💡 {message.error.suggestion}
                      </p>
                    )}
                    <div className="flex gap-2 mt-3">
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={handleRetry}
                        className="gap-1 text-xs h-8"
                      >
                        <RefreshCw className="h-3 w-3" />
                        Try Again
                      </Button>
                      {message.error?.code === "quota_exceeded" && (
                        <Button
                          size="sm"
                          variant="outline"
                          className="gap-1 text-xs h-8"
                        >
                          <Zap className="h-3 w-3" />
                          Try Grok
                        </Button>
                      )}
                    </div>
                  </div>
                </div>
                <p className="text-xs text-red-700 dark:text-red-400 ml-7">
                  {message.timestamp.toLocaleTimeString()}
                </p>
              </div>
            ) : (
              <div
                className={`max-w-xs lg:max-w-md xl:max-w-lg px-4 py-2 rounded-lg ${
                  message.role === "user"
                    ? "bg-blue-600 text-white rounded-br-none"
                    : "bg-white dark:bg-slate-700 text-slate-900 dark:text-white rounded-bl-none border border-slate-200 dark:border-slate-600"
                }`}
              >
                <p className="text-sm">{message.content}</p>
                <p
                  className={`text-xs mt-1 ${
                    message.role === "user"
                      ? "text-blue-100"
                      : "text-slate-500 dark:text-slate-400"
                  }`}
                >
                  {message.timestamp.toLocaleTimeString()}
                </p>
              </div>
            )}
          </div>
        ))}

        {isLoading && (
          <div className="flex justify-start">
            <div className="bg-white dark:bg-slate-700 text-slate-900 dark:text-white rounded-lg rounded-bl-none px-4 py-2 border border-slate-200 dark:border-slate-600">
              <div className="flex items-center gap-2">
                <Loader2 className="h-4 w-4 animate-spin" />
                <span className="text-sm">Thinking...</span>
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input Form */}
      <form onSubmit={handleSendMessage} className="flex gap-2">
        <Input
          type="text"
          placeholder="Ask anything... (no documents needed!)"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          disabled={isLoading}
          className="flex-1"
        />
        <Button
          type="submit"
          disabled={isLoading || !input.trim()}
          className="gap-2"
        >
          {isLoading ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : (
            <Send className="h-4 w-4" />
          )}
          Send
        </Button>
      </form>
    </div>
  );
}
