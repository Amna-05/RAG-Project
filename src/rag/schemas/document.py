"""
Pydantic schemas for document operations.
"""
from datetime import datetime
from uuid import UUID
from typing import Optional, List

from pydantic import BaseModel, Field


class DocumentUploadResponse(BaseModel):
    """Response after uploading a document."""
    id: UUID
    filename: str
    file_size: int
    file_type: str
    status: str
    uploaded_at: datetime
    
    class Config:
        from_attributes = True


class DocumentListItem(BaseModel):
    """Single document in list view."""
    id: UUID
    original_filename: str
    file_size: int
    file_type: str
    status: str
    num_chunks: int
    uploaded_at: datetime
    processed_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class DocumentDetail(BaseModel):
    """Detailed document view."""
    id: UUID
    original_filename: str
    file_size: int
    file_type: str
    status: str
    num_chunks: int
    total_tokens: int
    uploaded_at: datetime
    processed_at: Optional[datetime]
    processing_error: Optional[str]
    
    class Config:
        from_attributes = True


class ChatRequest(BaseModel):
    """Request for chat endpoint."""
    message: str = Field(..., min_length=1, max_length=5000)
    session_id: Optional[str] = None  # For conversation context
    
    class Config:
        json_schema_extra = {
            "example": {
                "message": "What are the main points in the document?",
                "session_id": "conv-123-abc"
            }
        }


class ChatResponse(BaseModel):
    """Response from chat endpoint."""
    session_id: str
    message: str
    role: str = "assistant"
    retrieved_chunks: int
    sources: List[dict]  # Which documents/chunks were used
    
    class Config:
        json_schema_extra = {
            "example": {
                "session_id": "conv-123-abc",
                "message": "Based on the documents...",
                "role": "assistant",
                "retrieved_chunks": 3,
                "sources": [
                    {"document": "report.pdf", "chunk": 2},
                    {"document": "notes.txt", "chunk": 5}
                ]
            }
        }


class ChatHistoryResponse(BaseModel):
    """Chat history for a session."""
    session_id: str
    messages: List[dict]
    total_messages: int