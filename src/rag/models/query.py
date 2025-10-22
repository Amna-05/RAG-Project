"""
Query history database model.
File: src/rag/models/query.py
"""
from datetime import datetime
from typing import Optional
import uuid

from sqlalchemy import String, DateTime, Integer, Text, Float
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID

from rag.models.base import Base


class QueryHistory(Base):
    """Track user queries for analytics and improvement."""
    __tablename__ = "query_history"
    
    # Primary key
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), 
        primary_key=True, 
        default=uuid.uuid4
    )
    
    # Foreign key to user
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), 
        nullable=False, 
        index=True
    )
    
    # Query data
    query_text: Mapped[str] = mapped_column(Text, nullable=False)
    response_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Retrieval metrics
    sources_count: Mapped[int] = mapped_column(Integer, default=0)
    top_relevance_score: Mapped[Optional[float]] = mapped_column(
        Float, 
        nullable=True
    )
    
    # Performance
    processing_time: Mapped[Optional[float]] = mapped_column(
        Float, 
        nullable=True
    )  # seconds
    
    # User feedback (optional)
    user_rating: Mapped[Optional[int]] = mapped_column(
        Integer, 
        nullable=True
    )  # 1-5 stars
    user_feedback: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Timestamp
    created_at: Mapped[datetime] = mapped_column(
        DateTime, 
        default=datetime.utcnow
    )
    
    def __repr__(self) -> str:
        return f"<Query {self.id}>"