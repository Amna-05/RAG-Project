"""
RAG Service - Orchestrates document processing and querying.
Integrates existing RAG pipeline with database tracking.
"""
import logging
import shutil
from pathlib import Path
from typing import List, Dict, Any, Optional
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from rag.models.document import Document
from rag.crud import document as document_crud
from rag.core.config import get_settings

# Your existing RAG pipeline
from rag.documents import process_document
from rag.embeddings import embed_document_chunks
from rag.vectorstore import store_embedded_documents, search_documents_by_text, delete_document
from rag.llm_integration import ask_question_detailed

settings = get_settings()
logger = logging.getLogger(__name__)


class DocumentProcessingError(Exception):
    """Raised when document processing fails."""
    pass


class RagService:
    """Service for RAG operations."""
    
    @staticmethod
    def get_user_upload_dir(user_id: UUID) -> Path:
        """Get user-specific upload directory."""
        upload_dir = settings.upload_dir / str(user_id)
        upload_dir.mkdir(parents=True, exist_ok=True)
        return upload_dir
    
    @staticmethod
    def validate_file_type(filename: str) -> bool:
        """Validate file type is allowed."""
        file_ext = Path(filename).suffix.lower()
        return file_ext in settings.allowed_file_types
    
    @staticmethod
    def validate_file_size(file_size: int) -> bool:
        """Validate file size is within limit."""
        max_size = settings.max_file_size_mb * 1024 * 1024
        return file_size <= max_size


async def save_uploaded_file(uploaded_file, user_id: UUID) -> Dict[str, Any]:
    """Save uploaded file to disk."""
    if not RagService.validate_file_type(uploaded_file.filename):
        raise DocumentProcessingError(
            f"File type not allowed. Allowed: {settings.allowed_file_types}"
        )
    
    upload_dir = RagService.get_user_upload_dir(user_id)
    
    file_extension = Path(uploaded_file.filename).suffix
    unique_filename = f"{uuid4()}{file_extension}"
    file_path = upload_dir / unique_filename
    
    try:
        with open(file_path, "wb") as buffer:
            while chunk := await uploaded_file.read(8192):
                buffer.write(chunk)
        
        file_size = file_path.stat().st_size
        
        if not RagService.validate_file_size(file_size):
            file_path.unlink()
            raise DocumentProcessingError(
                f"File too large. Max: {settings.max_file_size_mb}MB"
            )
        
        logger.info(f"Saved file: {unique_filename} ({file_size} bytes)")
        
        return {
            "file_path": str(file_path),
            "filename": unique_filename,
            "original_filename": uploaded_file.filename,
            "file_size": file_size,
            "file_type": file_extension.lstrip('.')
        }
        
    except DocumentProcessingError:
        raise
    except Exception as e:
        if file_path.exists():
            file_path.unlink()
        logger.error(f"Failed to save file: {e}")
        raise DocumentProcessingError(f"Failed to save file: {str(e)}")


async def process_document_pipeline(
    db: AsyncSession,
    document_id: UUID,
    file_path: str,
    user_id: UUID
) -> bool:
    """Background task: Process document through RAG pipeline."""
    try:
        await document_crud.update_document_status(db, document_id, status="processing")
        
        logger.info(f"Processing document {document_id}: {file_path}")
        chunks = process_document(file_path)
        
        if not chunks:
            raise DocumentProcessingError("No chunks created")
        
        logger.info(f"Created {len(chunks)} chunks")
        
        embedded_chunks = embed_document_chunks(chunks)
        
        successful_embeddings = sum(
            1 for chunk in embedded_chunks 
            if chunk.get('embedding') is not None
        )
        
        if successful_embeddings == 0:
            raise DocumentProcessingError("Failed to generate embeddings")
        
        logger.info(f"Generated {successful_embeddings} embeddings")
        
        # Add metadata for filtering
        for chunk in embedded_chunks:
            if 'metadata' not in chunk:
                chunk['metadata'] = {}
            
            chunk['metadata'].update({
                'user_id': str(user_id),
                'document_id': str(document_id)
            })
            
            chunk['id'] = f"{document_id}_{chunk['chunk_index']}"
        
        # Store in Pinecone with namespace
        namespace = str(user_id) if settings.pinecone_use_namespaces else None
        logger.info(f"Storing in Pinecone with namespace: {namespace}")  
        success = store_embedded_documents(embedded_chunks, namespace=namespace)
        
        if not success:
            raise DocumentProcessingError("Failed to store in Pinecone")
        
        # Save chunks to database
        chunk_data = [
            {
                "index": chunk['chunk_index'],
                "content": chunk['text'],
                "page_number": chunk.get('page_number'),
                "start_char": chunk.get('start_char'),
                "end_char": chunk.get('end_char')
            }
            for chunk in embedded_chunks
        ]
        
        await document_crud.create_chunks(db, document_id, chunk_data)
        
        total_tokens = sum(len(chunk['text'].split()) for chunk in embedded_chunks)
        
        await document_crud.update_document_status(
            db,
            document_id,
            status="completed",
            num_chunks=len(embedded_chunks),
            total_tokens=total_tokens
        )
        
        logger.info(f"✅ Document {document_id} processed successfully")
        return True
        
    except Exception as e:
        logger.error(f"Document processing failed: {e}")
        
        await document_crud.update_document_status(
            db, document_id, status="failed", error=str(e)
        )
        
        return False


async def upload_and_process_document(
    db: AsyncSession,
    user_id: UUID,
    uploaded_file,
    background_tasks
) -> Document:
    """Main entry point for document upload."""
    file_info = await save_uploaded_file(uploaded_file, user_id)
    
    document = await document_crud.create_document(
        db,
        user_id=user_id,
        filename=file_info["filename"],
        original_filename=file_info["original_filename"],
        file_path=file_info["file_path"],
        file_size=file_info["file_size"],
        file_type=file_info["file_type"]
    )
    
    background_tasks.add_task(
        process_document_pipeline,
        db,
        document.id,
        file_info["file_path"],
        user_id
    )
    
    logger.info(f"Document {document.id} queued for processing")
    return document


async def query_documents(
    db: AsyncSession,
    user_id: UUID,
    query: str,
    session_id: Optional[str] = None,
    top_k: int = None
) -> Dict[str, Any]:
    """Query user's documents using RAG pipeline."""
    if top_k is None:
        top_k = settings.default_top_k
    
    if not session_id:
        session_id = f"session-{uuid4()}"
    
    logger.info(f"Querying documents for user {user_id}: {query}")
    
    try:
        # FIXED: Pass user namespace and filter to search
        namespace = str(user_id) if settings.pinecone_use_namespaces else None
        user_id_str = None if settings.pinecone_use_namespaces else str(user_id)
        
        # Search with user filtering
        from rag.vectorstore import search_documents_by_text
        
        search_results = search_documents_by_text(
            query,
            top_k=top_k,
            namespace=namespace,
            user_id=user_id_str
        )
        
        logger.info(f"Found {len(search_results)} relevant chunks")
        
        # If no documents found, return friendly message
        if not search_results:
            await document_crud.create_chat_message(
                db, user_id=user_id, session_id=session_id,
                role="user", content=query
            )
            
            no_docs_message = (
                "I couldn't find any relevant documents to answer your question. "
                "Please make sure you've uploaded documents and they've finished processing."
            )
            
            await document_crud.create_chat_message(
                db, user_id=user_id, session_id=session_id,
                role="assistant", content=no_docs_message,
                retrieved_chunks=0, model_used=settings.gemini_model
            )
            
            return {
                "session_id": session_id,
                "message": no_docs_message,
                "role": "assistant",
                "retrieved_chunks": 0,
                "sources": [],
                "model_used": settings.gemini_model
            }
        
        # Build context from search results
        context_parts = []
        for i, result in enumerate(search_results):
            metadata = result.get('metadata', {})
            text = metadata.get('text', '')
            source = metadata.get('file_name', 'Unknown')
            
            context_parts.append(f"[Document {i+1}: {source}]\n{text}\n")
        
        context = "\n".join(context_parts)
        
        # Call Gemini LLM
        from rag.llm_integration import generate_answer_with_gemini
        
        prompt = f"""Based on the following documents, answer the question.

Documents:
{context}

Question: {query}

Answer:"""
        
        answer = generate_answer_with_gemini(prompt)
        
        # Save user message
        await document_crud.create_chat_message(
            db, user_id=user_id, session_id=session_id,
            role="user", content=query
        )
        
        # Save assistant response
        await document_crud.create_chat_message(
            db, user_id=user_id, session_id=session_id,
            role="assistant", content=answer,
            retrieved_chunks=len(search_results),
            model_used=settings.gemini_model
        )
        
        # Format sources
        formatted_sources = [
            {
                "document": result.get('metadata', {}).get('file_name', 'Unknown'),
                "chunk_index": result.get('metadata', {}).get('chunk_index', 0),
                "relevance_score": result.get('score', 0.0),
                "preview": result.get('metadata', {}).get('text', '')[:200]
            }
            for result in search_results
        ]
        
        return {
            "session_id": session_id,
            "message": answer,
            "role": "assistant",
            "retrieved_chunks": len(search_results),
            "sources": formatted_sources,
            "model_used": settings.gemini_model
        }
        
    except Exception as e:
        logger.error(f"Query failed: {e}")
        raise DocumentProcessingError(f"Query failed: {str(e)}")

async def get_user_documents_list(
    db: AsyncSession,
    user_id: UUID,
    skip: int = 0,
    limit: int = 100
) -> List[Document]:
    """Get list of user's documents."""
    return await document_crud.get_user_documents(db, user_id, skip, limit)


async def get_document_detail(
    db: AsyncSession,
    user_id: UUID,
    document_id: UUID
) -> Optional[Document]:
    """Get detailed information about a document."""
    return await document_crud.get_document_by_id(db, document_id, user_id)


async def delete_user_document(
    db: AsyncSession,
    user_id: UUID,
    document_id: UUID
) -> bool:
    """Delete a document (soft delete in DB, remove from Pinecone)."""
    success = await document_crud.soft_delete_document(db, document_id, user_id)
    
    if success:
        namespace = str(user_id) if settings.pinecone_use_namespaces else None
        delete_document(str(document_id), namespace=namespace)
        logger.info(f"Document {document_id} deleted")
    
    return success


async def get_chat_sessions(
    db: AsyncSession,
    user_id: UUID
) -> List[str]:
    """Get list of user's chat sessions."""
    return await document_crud.get_user_sessions(db, user_id)


async def get_session_history(
    db: AsyncSession,
    user_id: UUID,
    session_id: str
) -> List[Dict[str, Any]]:
    """Get chat history for a specific session."""
    messages = await document_crud.get_chat_history(db, user_id, session_id)
    
    return [
        {
            "id": str(msg.id),
            "role": msg.role,
            "content": msg.content,
            "created_at": msg.created_at.isoformat(),
            "retrieved_chunks": msg.retrieved_chunks
        }
        for msg in messages
    ]