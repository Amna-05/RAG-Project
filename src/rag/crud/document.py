"""
CRUD operations for documents.
Data access layer - no business logic!
"""
from typing import List, Optional
from uuid import UUID
from datetime import datetime

from sqlalchemy import select, update, and_
from sqlalchemy.ext.asyncio import AsyncSession

from rag.models.document import Document, DocumentChunk, ChatMessage


# ============= DOCUMENT CRUD =============

async def create_document(
    db: AsyncSession,
    user_id: UUID,
    filename: str,
    original_filename: str,
    file_path: str,
    file_size: int,
    file_type: str
) -> Document:
    """Create document record in database."""
    document = Document(
        user_id=user_id,
        filename=filename,
        original_filename=original_filename,
        file_path=file_path,
        file_size=file_size,
        file_type=file_type,
        status="pending"
    )
    db.add(document)
    await db.commit()
    await db.refresh(document)
    return document


async def get_document_by_id(
    db: AsyncSession,
    document_id: UUID,
    user_id: UUID
) -> Optional[Document]:
    """Get document by ID (only if owned by user)."""
    result = await db.execute(
        select(Document).where(
            and_(
                Document.id == document_id,
                Document.user_id == user_id,
                Document.is_deleted == False
            )
        )
    )
    return result.scalar_one_or_none()


async def get_user_documents(
    db: AsyncSession,
    user_id: UUID,
    skip: int = 0,
    limit: int = 100
) -> List[Document]:
    """Get all documents for a user."""
    result = await db.execute(
        select(Document)
        .where(
            and_(
                Document.user_id == user_id,
                Document.is_deleted == False
            )
        )
        .order_by(Document.uploaded_at.desc())
        .offset(skip)
        .limit(limit)
    )
    return list(result.scalars().all())


async def update_document_status(
    db: AsyncSession,
    document_id: UUID,
    status: str,
    num_chunks: Optional[int] = None,
    total_tokens: Optional[int] = None,
    error: Optional[str] = None
) -> Optional[Document]:
    """Update document processing status."""
    update_data = {
        "status": status,
        "processed_at": datetime.utcnow() if status == "completed" else None
    }
    
    if num_chunks is not None:
        update_data["num_chunks"] = num_chunks
    if total_tokens is not None:
        update_data["total_tokens"] = total_tokens
    if error:
        update_data["processing_error"] = error
    
    await db.execute(
        update(Document)
        .where(Document.id == document_id)
        .values(**update_data)
    )
    await db.commit()
    
    result = await db.execute(
        select(Document).where(Document.id == document_id)
    )
    return result.scalar_one_or_none()


async def soft_delete_document(
    db: AsyncSession,
    document_id: UUID,
    user_id: UUID
) -> bool:
    """Soft delete document (mark as deleted)."""
    result = await db.execute(
        update(Document)
        .where(
            and_(
                Document.id == document_id,
                Document.user_id == user_id
            )
        )
        .values(is_deleted=True, deleted_at=datetime.utcnow())
    )
    await db.commit()
    return result.rowcount > 0


# ============= CHUNK CRUD =============

async def create_chunks(
    db: AsyncSession,
    document_id: UUID,
    chunks: List[dict]
) -> List[DocumentChunk]:
    """Bulk create document chunks."""
    db_chunks = [
        DocumentChunk(
            document_id=document_id,
            chunk_index=chunk["index"],
            content=chunk["content"],
            page_number=chunk.get("page_number"),
            start_char=chunk.get("start_char"),
            end_char=chunk.get("end_char")
        )
        for chunk in chunks
    ]
    
    db.add_all(db_chunks)
    await db.commit()
    return db_chunks


async def get_document_chunks(
    db: AsyncSession,
    document_id: UUID
) -> List[DocumentChunk]:
    """Get all chunks for a document."""
    result = await db.execute(
        select(DocumentChunk)
        .where(DocumentChunk.document_id == document_id)
        .order_by(DocumentChunk.chunk_index)
    )
    return list(result.scalars().all())


# ============= CHAT CRUD =============

async def create_chat_message(
    db: AsyncSession,
    user_id: UUID,
    session_id: str,
    role: str,
    content: str,
    retrieved_chunks: int = 0,
    model_used: Optional[str] = None
) -> ChatMessage:
    """Create chat message."""
    message = ChatMessage(
        user_id=user_id,
        session_id=session_id,
        role=role,
        content=content,
        retrieved_chunks=retrieved_chunks,
        model_used=model_used
    )
    db.add(message)
    await db.commit()
    await db.refresh(message)
    return message


async def get_chat_history(
    db: AsyncSession,
    user_id: UUID,
    session_id: str,
    limit: int = 50
) -> List[ChatMessage]:
    """Get chat history for a session."""
    result = await db.execute(
        select(ChatMessage)
        .where(
            and_(
                ChatMessage.user_id == user_id,
                ChatMessage.session_id == session_id
            )
        )
        .order_by(ChatMessage.created_at.desc())
        .limit(limit)
    )
    messages = list(result.scalars().all())
    return list(reversed(messages))  # Oldest first


async def get_user_sessions(
    db: AsyncSession,
    user_id: UUID,
    limit: int = 20
) -> List[str]:
    """Get list of session IDs for a user."""
    result = await db.execute(
        select(ChatMessage.session_id)
        .where(ChatMessage.user_id == user_id)
        .distinct()
        .order_by(ChatMessage.created_at.desc())
        .limit(limit)
    )
    return list(result.scalars().all())