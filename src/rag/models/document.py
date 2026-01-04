"""
Document models for RAG system.
Tracks uploaded files and their metadata.
"""
from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Text, Boolean, Float
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import relationship

from rag.core.database import Base


class Document(Base):
    """
    Stores uploaded document metadata.
    
    WHY SEPARATE TABLE:
    - Track file ownership per user
    - Store processing status
    - Enable document management (list, delete)
    - Audit trail (when uploaded, by whom)
    """
    __tablename__ = "documents"
    
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    # File name
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)  
    # File info  

    file_path = Column(String(512), nullable=False)  # Where file is stored
    file_size = Column(Integer, nullable=False)  # Bytes
    file_type = Column(String(50), nullable=False)  # pdf, docx, txt
    
    # Processing status
    status = Column(String(20), default="pending")  # pending, processing, completed, failed
    processing_error = Column(Text, nullable=True)
    
    # Metadata
    num_chunks = Column(Integer, default=0)
    total_tokens = Column(Integer, default=0)
        
    # Timestamps
    uploaded_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    processed_at = Column(DateTime, nullable=True)
    
    # Soft delete
    is_deleted = Column(Boolean, default=False)
    deleted_at = Column(DateTime, nullable=True)
    
    # BM25 index status for hybrid search
    bm25_indexed = Column(Boolean, default=False)
    
    # Relationships
    user = relationship("User", back_populates="documents")
    chunks = relationship("DocumentChunk", back_populates="document", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Document {self.original_filename} by user {self.user_id}>"


class DocumentChunk(Base):
    """
    Stores individual chunks of documents.
    
    WHY STORE CHUNKS:
    - Vector DB might fail/reset
    - Enable re-indexing without re-processing
    - Store metadata per chunk
    - Debugging and auditing
    """
    __tablename__ = "document_chunks"
    
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    document_id = Column(PG_UUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    
    # Chunk data
    chunk_index = Column(Integer, nullable=False)  # Order in document
    content = Column(Text, nullable=False)
    
    # Vector embedding (optional - if you want to store in DB too)
    # embedding = Column(ARRAY(Float))  # Or store only in vector DB
    
    # Metadata for better retrieval
    page_number = Column(Integer, nullable=True)
    start_char = Column(Integer, nullable=True)
    end_char = Column(Integer, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    document = relationship("Document", back_populates="chunks")
    
    def __repr__(self):
        return f"<Chunk {self.chunk_index} of document {self.document_id}>"


class ChatMessage(Base):
    """
    Stores chat history per user.
    
    WHY STORE CHATS:
    - User can see history
    - Context for multi-turn conversations
    - Analytics and improvements
    - Fine-tuning data collection
    """
    __tablename__ = "chat_messages"
    
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    session_id = Column(String(100), nullable=False)  # Group messages in conversation
    
    # Message content
    role = Column(String(20), nullable=False)  # user, assistant, system
    content = Column(Text, nullable=False)
    
    # RAG metadata
    retrieved_chunks = Column(Integer, default=0)  # How many chunks used
    model_used = Column(String(50), nullable=True)  # gpt-4, claude, etc.
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="chat_messages")
    
    def __repr__(self):
        return f"<ChatMessage {self.role}: {self.content[:50]}...>"
    
