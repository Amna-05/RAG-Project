"""
Query Pydantic schemas.
File: src/rag/schemas/query.py
"""
from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict


class QueryRequest(BaseModel):
    """RAG query request."""
    query: str = Field(..., min_length=3, max_length=1000)
    top_k: int = Field(default=5, ge=1, le=20)


class SourceInfo(BaseModel):
    """Information about a retrieved source."""
    document_id: str
    relevance_score: float
    text_preview: str
    chunk_index: int


class QueryResponse(BaseModel):
    """RAG query response."""
    query: str
    answer: str
    sources: list[SourceInfo]
    processing_time: float
    timestamp: datetime


class QueryHistoryItem(BaseModel):
    """Query history item."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    query_text: str
    response_text: Optional[str]
    sources_count: int
    top_relevance_score: Optional[float]
    processing_time: Optional[float]
    created_at: datetime