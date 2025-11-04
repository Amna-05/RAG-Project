export interface ChatMessage {
  id: string;
  session_id: string;
  role: "user" | "assistant";
  message: string;
  retrieved_chunks?: number;
  model_used?: string;
  created_at: string;
  sources?: Source[];
}

export interface Source {
  document: string;
  chunk_index: number;
  relevance_score: number;
  preview: string;
}

export interface ChatRequest {
  message: string;
  session_id?: string;
}

export interface ChatResponse {
  session_id: string;
  message: string;
  role: "assistant";
  retrieved_chunks: number;
  sources: Source[];
  model_used: string;
}

export interface ChatSession {
  session_id: string;
  created_at: string;
  last_message_at: string;
  message_count: number;
}