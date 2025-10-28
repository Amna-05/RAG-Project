"""
RAG endpoints for document management and chat.
File: src/rag/api/v1/rag.py

Protected endpoints - all require authentication.
"""
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, BackgroundTasks, Query
from sqlalchemy.ext.asyncio import AsyncSession

from rag.core.database import get_db
from rag.api.deps import get_current_user
from rag.models.user import User
from rag.schemas.document import (
    DocumentUploadResponse,
    DocumentListItem,
    DocumentDetail,
    ChatRequest,
    ChatResponse,
    ChatHistoryResponse
)
from rag.services import rag_service

router = APIRouter(prefix="/rag", tags=["RAG"])


@router.post("/upload", response_model=DocumentUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Upload a document for processing.
    
    **FLOW:**
    1. File is saved to disk
    2. Database record created (status="pending")
    3. Background task processes document
    4. Returns immediately (non-blocking)
    
    **Supported file types:** PDF, DOCX, TXT, JSON
    
    **Request:**
    - multipart/form-data with file field
    
    **Response:**
    - Document metadata with status="pending"
    - Check `/documents/{id}` to see when processing completes
    
    **Example (curl):**
```bash
    curl -X POST http://localhost:8000/api/v1/rag/upload \
      -H "Cookie: access_token=..." \
      -F "file=@report.pdf"
```
    
    **Example (JavaScript):**
```javascript
    const formData = new FormData();
    formData.append('file', fileInput.files[0]);
    
    const response = await fetch('/api/v1/rag/upload', {
        method: 'POST',
        credentials: 'include',
        body: formData
    });
    
    const doc = await response.json();
    console.log(`Uploaded: ${doc.filename}, Status: ${doc.status}`);
```
    """
    try:
        document = await rag_service.upload_and_process_document(
            db,
            current_user.id,
            file,
            background_tasks
        )
        
        return document
        
    except rag_service.DocumentProcessingError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Upload failed: {str(e)}"
        )


@router.get("/documents", response_model=List[DocumentListItem])
async def list_documents(
    skip: int = Query(0, ge=0, description="Number of documents to skip"),
    limit: int = Query(100, ge=1, le=100, description="Max documents to return"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get list of user's documents.
    
    **Returns:** List of documents with metadata and processing status
    
    **Statuses:**
    - `pending`: Just uploaded, not processed yet
    - `processing`: Currently being chunked/embedded
    - `completed`: Ready to query
    - `failed`: Processing error (check `processing_error` field)
    
    **Example:**
```javascript
    const response = await fetch('/api/v1/rag/documents', {
        credentials: 'include'
    });
    const documents = await response.json();
    
    documents.forEach(doc => {
        console.log(`${doc.original_filename}: ${doc.status}`);
    });
```
    """
    documents = await rag_service.get_user_documents_list(
        db,
        current_user.id,
        skip=skip,
        limit=limit
    )
    
    return documents


@router.get("/documents/{document_id}", response_model=DocumentDetail)
async def get_document(
    document_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get detailed information about a specific document.
    
    **Includes:**
    - Full metadata
    - Processing status
    - Number of chunks created
    - Total tokens
    - Error message (if failed)
    
    **Example:**
```javascript
    const doc = await fetch(`/api/v1/rag/documents/${docId}`, {
        credentials: 'include'
    }).then(r => r.json());
    
    console.log(`Chunks: ${doc.num_chunks}, Tokens: ${doc.total_tokens}`);
```
    """
    document = await rag_service.get_document_detail(
        db,
        current_user.id,
        document_id
    )
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    return document


@router.delete("/documents/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a document.
    
    **Actions:**
    1. Soft delete in database (mark as deleted)
    2. Remove from Pinecone vector database
    3. Keep file on disk (can be purged later by admin)
    
    **Note:** Cannot be undone!
    
    **Example:**
```javascript
    await fetch(`/api/v1/rag/documents/${docId}`, {
        method: 'DELETE',
        credentials: 'include'
    });
    // Document deleted
```
    """
    success = await rag_service.delete_user_document(
        db,
        current_user.id,
        document_id
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    return None


@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Query documents using natural language.
    
    **FLOW:**
    1. Convert query to embedding
    2. Search user's documents in Pinecone
    3. Retrieve top K relevant chunks
    4. Send chunks + query to Google Gemini
    5. Return AI-generated answer with sources
    6. Save conversation to database
    
    **Multi-turn conversations:**
    - Provide `session_id` to maintain context
    - System remembers last 5 messages
    
    **Request:**
```json
    {
      "message": "What are the main findings in the report?",
      "session_id": "session-abc-123"  // optional
    }
```
    
    **Response:**
```json
    {
      "session_id": "session-abc-123",
      "message": "The main findings are...",
      "role": "assistant",
      "retrieved_chunks": 3,
      "sources": [
        {
          "document": "report.pdf",
          "chunk_index": 2,
          "relevance_score": 0.92,
          "preview": "The study shows that..."
        }
      ],
      "model_used": "gemini-2.0-flash"
    }
```
    
    **Example:**
```javascript
    const response = await fetch('/api/v1/rag/chat', {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            message: 'Summarize the key points',
            session_id: sessionId
        })
    });
    
    const answer = await response.json();
    console.log(answer.message);
    console.log(`Used ${answer.retrieved_chunks} chunks`);
```
    """
    try:
        result = await rag_service.query_documents(
            db,
            current_user.id,
            request.message,
            session_id=request.session_id
        )
        
        return result
        
    except rag_service.DocumentProcessingError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Query failed: {str(e)}"
        )


@router.get("/chat/sessions", response_model=List[str])
async def get_chat_sessions(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get list of user's chat sessions.
    
    **Returns:** List of session IDs (most recent first)
    
    **Use case:** Show conversation history sidebar
    
    **Example:**
```javascript
    const sessions = await fetch('/api/v1/rag/chat/sessions', {
        credentials: 'include'
    }).then(r => r.json());
    
    // Display in sidebar:
    sessions.forEach(sessionId => {
        console.log(`Session: ${sessionId}`);
    });
```
    """
    sessions = await rag_service.get_chat_sessions(db, current_user.id)
    return sessions


@router.get("/chat/history/{session_id}", response_model=ChatHistoryResponse)
async def get_chat_history(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get full chat history for a session.
    
    **Returns:** All messages in chronological order
    
    **Use case:** Load previous conversation when user clicks on session
    
    **Example:**
```javascript
    const history = await fetch(`/api/v1/rag/chat/history/${sessionId}`, {
        credentials: 'include'
    }).then(r => r.json());
    
    history.messages.forEach(msg => {
        console.log(`${msg.role}: ${msg.content}`);
    });
```
    """
    messages = await rag_service.get_session_history(
        db,
        current_user.id,
        session_id
    )
    
    return {
        "session_id": session_id,
        "messages": messages,
        "total_messages": len(messages)
    }


@router.get("/health")
async def health_check(
    current_user: User = Depends(get_current_user)
):
    """
    Health check endpoint for RAG system.
    
    **Returns:** System status and user info
    """
    from rag.vectorstore import SimplePineconeStore
    
    try:
        # Test Pinecone connection
        store = SimplePineconeStore()
        pinecone_connected = store.connect_to_index()
        
        return {
            "status": "healthy",
            "user_id": str(current_user.id),
            "pinecone_connected": pinecone_connected,
            "message": "RAG system operational"
        }
    except Exception as e:
        return {
            "status": "degraded",
            "user_id": str(current_user.id),
            "pinecone_connected": False,
            "error": str(e)
        }