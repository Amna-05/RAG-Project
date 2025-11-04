export interface Document {
  id: string;
  filename: string;
  original_filename: string;
  file_size: number;
  file_type: string;
  status: "pending" | "processing" | "completed" | "failed";
  num_chunks?: number;
  uploaded_at: string;
  processed_at?: string;
  user_id: string;
}

export interface DocumentUploadResponse {
  id: string;
  filename: string;
  original_filename: string;
  file_size: number;
  file_type: string;
  status: string;
  uploaded_at: string;
}

export interface DocumentChunk {
  id: string;
  document_id: string;
  chunk_index: number;
  content: string;
  metadata?: Record<string, any>;
}