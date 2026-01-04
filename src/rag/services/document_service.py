"""
Document processing service.
File: src/rag/services/document_service.py

PURPOSE:
Handles the complete document ingestion pipeline:
1. Save uploaded file
2. Extract text (PDF, DOCX, TXT, MD)
3. Create chunks
4. Generate embeddings
5. Store in Pinecone (user's namespace)
6. Save metadata to PostgreSQL
"""
import logging
import uuid
from pathlib import Path
from typing import List, Dict, Any, Optional
import json

from sqlalchemy.ext.asyncio import AsyncSession

from rag.models.user import User
from rag.models.document import DocumentMetadata
from rag.documents import process_document  #  existing code
from rag.embeddings import embed_document_chunks  # existing code
from rag.core.config import get_settings  # existing code
from rag.vectorstore import store_embedded_documents  # existing code

settings = get_settings()
logger = logging.getLogger(__name__)


async def save_uploaded_file(
    file_content: bytes,
    filename: str,
    user_id: uuid.UUID
) -> Path:
    """
    Save uploaded file to disk.
    
    Files stored as: data/uploads/{user_id}/{filename}
    This keeps user files isolated.
    """
    # Create user's upload directory
    user_upload_dir = settings.upload_dir / str(user_id)
    user_upload_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate unique filename (prevent overwrite)
    file_path = user_upload_dir / filename
    counter = 1
    while file_path.exists():
        stem = Path(filename).stem
        suffix = Path(filename).suffix
        file_path = user_upload_dir / f"{stem}_{counter}{suffix}"
        counter += 1
    
    # Save file
    with open(file_path, 'wb') as f:
        f.write(file_content)
    
    logger.info(f"✅ Saved file: {file_path}")
    return file_path


async def process_and_store_document(
    db: AsyncSession,
    user: User,
    file_path: Path,
    original_filename: str
) -> DocumentMetadata:
    """
    Complete document processing pipeline.
    
    STEPS:
    1. Process document (chunking)
    2. Generate embeddings
    3. Store in Pinecone (user's namespace)
    4. Save metadata to database
    
    Returns:
        DocumentMetadata object
    """
    # Create database record (mark as processing)
    doc_metadata = DocumentMetadata(
        user_id=user.id,
        filename=file_path.name,
        original_filename=original_filename,
        file_type=file_path.suffix,
        file_size=file_path.stat().st_size,
        embedding_model=settings.embedding_model,
        processing_status="processing"
    )
    db.add(doc_metadata)
    await db.commit()
    await db.refresh(doc_metadata)
    
    try:
        # Step 1: Process document (chunking)
        logger.info(f"📄 Processing document: {file_path}")
        chunks = process_document(file_path)
        
        if not chunks:
            raise ValueError("No content extracted from document")
        
        logger.info(f"✅ Created {len(chunks)} chunks")
        
        # Step 2: Generate embeddings
        logger.info("🔢 Generating embeddings...")
        embedded_chunks = embed_document_chunks(chunks)
        
        successful_embeddings = sum(
            1 for chunk in embedded_chunks 
            if chunk.get('embedding') is not None
        )
        logger.info(f"✅ Generated {successful_embeddings} embeddings")
        
        # Step 3: Store in Pinecone (user's namespace)
        logger.info(f"📤 Storing in Pinecone namespace: {user.pinecone_namespace}")
        pinecone_ids = await store_embedded_documents(
            embedded_chunks,
            namespace=user.pinecone_namespace,
            document_id=str(doc_metadata.id)
        )
        
        # Step 4: Update database metadata
        from sqlalchemy import update
        from datetime import datetime
        
        await db.execute(
            update(DocumentMetadata)
            .where(DocumentMetadata.id == doc_metadata.id)
            .values(
                chunk_count=len(chunks),
                processing_status="completed",
                processed_at=datetime.utcnow(),
                pinecone_ids=json.dumps(pinecone_ids)
            )
        )
        await db.commit()
        
        # Update user's document count
        from rag.crud import user as user_crud
        await user_crud.increment_document_count(db, user.id)
        
        logger.info(f"✅ Document processed successfully: {doc_metadata.id}")
        
        # Refresh to get updated data
        await db.refresh(doc_metadata)
        return doc_metadata
        
    except Exception as e:
        logger.error(f"❌ Document processing failed: {e}")
        
        # Update status to failed
        from sqlalchemy import update
        await db.execute(
            update(DocumentMetadata)
            .where(DocumentMetadata.id == doc_metadata.id)
            .values(
                processing_status="failed",
                error_message=str(e)
            )
        )
        await db.commit()
        
        raise


async def store_in_pinecone(
    embedded_chunks: List[Dict[str, Any]],
    namespace: str,
    document_id: str
) -> List[str]:
    """
    Store embeddings in Pinecone with user's namespace.
    
    Args:
        embedded_chunks: Chunks with embeddings
        namespace: User's Pinecone namespace
        document_id: Document ID for tracking
        
    Returns:
        List of Pinecone vector IDs
    """
    from pinecone import Pinecone
    
    pc = Pinecone(api_key=settings.pinecone_api_key)
    index = pc.Index(settings.pinecone_index_name)
    
    vectors = []
    pinecone_ids = []
    
    for i, chunk in enumerate(embedded_chunks):
        if chunk.get('embedding') is None:
            continue
        
        # Generate unique ID: {document_id}_{chunk_index}
        vector_id = f"{document_id}_{i}"
        pinecone_ids.append(vector_id)
        
        vector = {
            'id': vector_id,
            'values': chunk['embedding'],
            'metadata': {
                'text': chunk.get('text', '')[:1000],  # Pinecone metadata limit
                'source': chunk.get('source', ''),
                'chunk_index': chunk.get('chunk_index', i),
                'document_id': document_id
            }
        }
        vectors.append(vector)
    
    # Upsert to Pinecone with namespace
    if vectors:
        index.upsert(vectors=vectors, namespace=namespace)
        logger.info(f"✅ Stored {len(vectors)} vectors in namespace: {namespace}")
    
    return pinecone_ids


async def delete_document(
    db: AsyncSession,
    user: User,
    document_id: uuid.UUID
) -> bool:
    """
    Delete document and its vectors from Pinecone.
    
    STEPS:
    1. Get document metadata
    2. Delete vectors from Pinecone
    3. Delete file from disk
    4. Delete metadata from database
    """
    # Get document
    from sqlalchemy import select
    result = await db.execute(
        select(DocumentMetadata).where(
            DocumentMetadata.id == document_id,
            DocumentMetadata.user_id == user.id
        )
    )
    doc = result.scalar_one_or_none()
    
    if not doc:
        return False
    
    try:
        # Delete from Pinecone
        if doc.pinecone_ids:
            from pinecone import Pinecone
            
            pc = Pinecone(api_key=settings.pinecone_api_key)
            index = pc.Index(settings.pinecone_index_name)
            
            vector_ids = json.loads(doc.pinecone_ids)
            index.delete(ids=vector_ids, namespace=user.pinecone_namespace)
            logger.info(f"✅ Deleted {len(vector_ids)} vectors from Pinecone")
        
        # Delete file from disk
        user_upload_dir = settings.upload_dir / str(user.id)
        file_path = user_upload_dir / doc.filename
        if file_path.exists():
            file_path.unlink()
            logger.info(f"✅ Deleted file: {file_path}")
        
        # Delete from database
        await db.delete(doc)
        await db.commit()
        
        # Update user's document count
        from rag.crud import user as user_crud
        from sqlalchemy import update
        await db.execute(
            update(User)
            .where(User.id == user.id)
            .values(document_count=User.document_count - 1)
        )
        await db.commit()
        
        logger.info(f"✅ Document deleted: {document_id}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to delete document: {e}")
        return False


async def get_user_documents(
    db: AsyncSession,
    user_id: uuid.UUID
) -> List[DocumentMetadata]:
    """Get all documents for a user."""
    from sqlalchemy import select
    
    result = await db.execute(
        select(DocumentMetadata)
        .where(DocumentMetadata.user_id == user_id)
        .order_by(DocumentMetadata.uploaded_at.desc())
    )
    
    return list(result.scalars().all())


    