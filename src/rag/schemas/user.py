"""
User Pydantic schemas.
File: src/rag/schemas/user.py
"""
from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, ConfigDict


class UserBase(BaseModel):
    """Base user schema with common fields."""
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)
    full_name: Optional[str] = Field(None, max_length=100)


class UserCreate(UserBase):
    """Schema for user registration."""
    password: str = Field(..., min_length=8, max_length=100)


class UserUpdate(BaseModel):
    """Schema for user profile updates."""
    full_name: Optional[str] = Field(None, max_length=100)
    email: Optional[EmailStr] = None


class UserResponse(UserBase):
    """Schema for user response (no sensitive data)."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    is_active: bool
    is_verified: bool
    pinecone_namespace: str
    document_count: int
    query_count: int
    created_at: datetime
    last_login: Optional[datetime]


class UserStats(BaseModel):
    """User usage statistics."""
    total_documents: int
    total_queries: int
    total_storage_mb: float
    avg_query_time: Optional[float]
    last_activity: Optional[datetime]