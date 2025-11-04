export const APP_NAME = process.env.NEXT_PUBLIC_APP_NAME || "RAG System";
export const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";
export const MAX_FILE_SIZE = Number(process.env.NEXT_PUBLIC_MAX_FILE_SIZE) || 10 * 1024 * 1024;

export const ALLOWED_FILE_TYPES = [".pdf", ".docx", ".txt", ".json"];

export const FILE_TYPE_ICONS: Record<string, string> = {
  pdf: "📄",
  docx: "📝",
  txt: "📃",
  json: "📋",
};

export const DOCUMENT_STATUS = {
  PENDING: "pending",
  PROCESSING: "processing",
  COMPLETED: "completed",
  FAILED: "failed",
} as const;

export const AUTH_ROUTES = ["/login", "/register"];
export const PROTECTED_ROUTES = ["/dashboard", "/documents", "/chat", "/settings"];