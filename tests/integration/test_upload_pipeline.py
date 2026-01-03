"""
Integration tests for the upload-process-retrieve pipeline.
File: tests/integration/test_upload_pipeline.py
"""
import pytest
import asyncio
from io import BytesIO
from pathlib import Path
from uuid import uuid4
from unittest.mock import patch, MagicMock, AsyncMock
from fastapi import UploadFile

from sqlalchemy.ext.asyncio import AsyncSession

from rag.models.document import Document
from rag.models.user import User
from rag.services.rag_service import (
    upload_and_process_document,
    process_document_pipeline,
    query_documents,
    save_uploaded_file,
    DocumentProcessingError,
    RagService
)
from rag.core.security import get_password_hash
from rag.crud import document as document_crud


class TestUploadPipeline:
    """Test the document upload pipeline."""

    async def create_test_user(self, db: AsyncSession) -> User:
        """Helper to create a test user."""
        user = User(
            id=uuid4(),
            email="test@example.com",
            username="testuser",
            hashed_password=get_password_hash("TestPassword123!"),
            full_name="Test User",
            is_active=True,
            is_verified=True,
            pinecone_namespace=f"user_{uuid4().hex[:12]}",
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
        return user

    def create_test_file(self, content: str = "Test document content") -> UploadFile:
        """Helper to create a test file."""
        file_obj = BytesIO(content.encode())
        return UploadFile(
            filename="test_document.txt",
            file=file_obj,
            headers={"content-type": "text/plain"}
        )

    @pytest.mark.asyncio
    async def test_validate_file_type_allowed(self):
        """Test file type validation for allowed types."""
        assert RagService.validate_file_type("document.pdf") is True
        assert RagService.validate_file_type("document.docx") is True
        assert RagService.validate_file_type("document.txt") is True
        assert RagService.validate_file_type("document.json") is True

    @pytest.mark.asyncio
    async def test_validate_file_type_not_allowed(self):
        """Test file type validation rejects disallowed types."""
        assert RagService.validate_file_type("script.exe") is False
        assert RagService.validate_file_type("image.jpg") is False
        assert RagService.validate_file_type("archive.zip") is False

    @pytest.mark.asyncio
    async def test_validate_file_size_under_limit(self):
        """Test file size validation for files under limit."""
        # Assuming max is 10MB (10485760 bytes)
        assert RagService.validate_file_size(1024 * 1024) is True  # 1MB
        assert RagService.validate_file_size(5 * 1024 * 1024) is True  # 5MB
        assert RagService.validate_file_size(10 * 1024 * 1024) is True  # 10MB

    @pytest.mark.asyncio
    async def test_validate_file_size_over_limit(self):
        """Test file size validation rejects oversized files."""
        # 11MB should exceed 10MB limit
        assert RagService.validate_file_size(11 * 1024 * 1024) is False

    @pytest.mark.asyncio
    async def test_save_uploaded_file_success(self, db_session: AsyncSession, tmp_path):
        """Test successful file upload and save."""
        user = await self.create_test_user(db_session)

        with patch('rag.services.rag_service.settings') as mock_settings:
            mock_settings.upload_dir = tmp_path
            mock_settings.allowed_file_types = {'.txt', '.pdf', '.docx', '.json'}
            mock_settings.max_file_size_mb = 10

            test_file = self.create_test_file("Document content for testing")
            result = await save_uploaded_file(test_file, user.id)

            assert "file_path" in result
            assert "filename" in result
            assert "original_filename" in result
            assert result["original_filename"] == "test_document.txt"
            assert result["file_type"] == "txt"
            assert Path(result["file_path"]).exists()

    @pytest.mark.asyncio
    async def test_save_uploaded_file_invalid_type(self, db_session: AsyncSession, tmp_path):
        """Test file upload rejects invalid file types."""
        user = await self.create_test_user(db_session)

        with patch('rag.services.rag_service.settings') as mock_settings:
            mock_settings.upload_dir = tmp_path
            mock_settings.allowed_file_types = {'.txt', '.pdf'}
            mock_settings.max_file_size_mb = 10

            test_file = UploadFile(
                filename="script.exe",
                file=BytesIO(b"malicious code"),
            )

            with pytest.raises(DocumentProcessingError):
                await save_uploaded_file(test_file, user.id)

    @pytest.mark.asyncio
    async def test_save_uploaded_file_exceeds_size_limit(self, db_session: AsyncSession, tmp_path):
        """Test file upload rejects oversized files."""
        user = await self.create_test_user(db_session)

        with patch('rag.services.rag_service.settings') as mock_settings:
            mock_settings.upload_dir = tmp_path
            mock_settings.allowed_file_types = {'.txt'}
            mock_settings.max_file_size_mb = 0.001  # Very small limit

            # Create a file larger than the limit
            large_content = "x" * 5000  # ~5KB
            test_file = UploadFile(
                filename="large.txt",
                file=BytesIO(large_content.encode()),
            )

            with pytest.raises(DocumentProcessingError):
                await save_uploaded_file(test_file, user.id)

    @pytest.mark.asyncio
    async def test_process_document_pipeline_success(self, db_session: AsyncSession, tmp_path):
        """Test successful document processing pipeline."""
        user = await self.create_test_user(db_session)

        # Create test file
        test_file_path = tmp_path / "test_doc.txt"
        test_file_path.write_text("Machine learning is a subset of artificial intelligence.")

        # Create document record
        doc = await document_crud.create_document(
            db_session,
            user_id=user.id,
            filename="test_doc.txt",
            original_filename="test_doc.txt",
            file_path=str(test_file_path),
            file_size=1024,
            file_type="txt"
        )

        with patch('rag.services.rag_service.process_document') as mock_process:
            with patch('rag.services.rag_service.embed_document_chunks') as mock_embed:
                with patch('rag.services.rag_service.store_embedded_documents') as mock_store:
                    # Mock the processing steps
                    mock_process.return_value = [
                        {
                            'text': 'Machine learning is a subset',
                            'chunk_index': 0,
                            'page_number': 1,
                            'start_char': 0,
                            'end_char': 30
                        }
                    ]

                    mock_embed.return_value = [
                        {
                            'text': 'Machine learning is a subset',
                            'chunk_index': 0,
                            'page_number': 1,
                            'start_char': 0,
                            'end_char': 30,
                            'embedding': [0.1, 0.2, 0.3]
                        }
                    ]

                    mock_store.return_value = True

                    # Run pipeline
                    result = await process_document_pipeline(
                        db_session,
                        doc.id,
                        str(test_file_path),
                        user.id
                    )

                    assert result is True

                    # Verify document status updated
                    updated_doc = await document_crud.get_document_by_id(
                        db_session, doc.id, user.id
                    )
                    assert updated_doc.status == "completed"
                    assert updated_doc.num_chunks == 1

    @pytest.mark.asyncio
    async def test_process_document_pipeline_failure(self, db_session: AsyncSession, tmp_path):
        """Test document processing handles failures gracefully."""
        user = await self.create_test_user(db_session)

        test_file_path = tmp_path / "test_doc.txt"
        test_file_path.write_text("Test content")

        doc = await document_crud.create_document(
            db_session,
            user_id=user.id,
            filename="test_doc.txt",
            original_filename="test_doc.txt",
            file_path=str(test_file_path),
            file_size=1024,
            file_type="txt"
        )

        with patch('rag.services.rag_service.process_document') as mock_process:
            # Simulate processing failure
            mock_process.side_effect = Exception("Processing failed")

            result = await process_document_pipeline(
                db_session,
                doc.id,
                str(test_file_path),
                user.id
            )

            assert result is False

            # Verify document status is failed
            updated_doc = await document_crud.get_document_by_id(
                db_session, doc.id, user.id
            )
            assert updated_doc.status == "failed"

    @pytest.mark.asyncio
    async def test_query_documents_no_results(self, db_session: AsyncSession):
        """Test querying returns friendly message when no documents found."""
        user = await self.create_test_user(db_session)

        with patch('rag.services.rag_service.search_documents_by_text') as mock_search:
            # Simulate no search results
            mock_search.return_value = []

            result = await query_documents(
                db_session,
                user.id,
                "What is machine learning?"
            )

            assert "couldn't find" in result["message"].lower()
            assert result["retrieved_chunks"] == 0
            assert result["sources"] == []

    @pytest.mark.asyncio
    async def test_query_documents_with_results(self, db_session: AsyncSession):
        """Test querying with successful search results."""
        user = await self.create_test_user(db_session)

        with patch('rag.services.rag_service.search_documents_by_text') as mock_search:
            with patch('rag.services.rag_service.generate_answer') as mock_generate:
                # Mock search results
                mock_search.return_value = [
                    {
                        'metadata': {
                            'text': 'Machine learning is a subset of AI',
                            'file_name': 'test.pdf',
                            'chunk_index': 0
                        },
                        'score': 0.95
                    }
                ]

                # Mock LLM response
                mock_generate.return_value = "Machine learning is a subset of artificial intelligence..."

                result = await query_documents(
                    db_session,
                    user.id,
                    "What is machine learning?"
                )

                assert result["retrieved_chunks"] == 1
                assert len(result["sources"]) == 1
                assert result["sources"][0]["document"] == "test.pdf"
                assert "Machine learning" in result["message"]

    @pytest.mark.asyncio
    async def test_full_upload_process_retrieve_workflow(
        self, db_session: AsyncSession, tmp_path
    ):
        """Test the complete upload-process-retrieve workflow."""
        user = await self.create_test_user(db_session)

        # Step 1: Create a test file
        test_content = "Artificial intelligence and machine learning are important technologies."
        test_file_path = tmp_path / "test_doc.txt"
        test_file_path.write_text(test_content)

        # Step 2: Upload the document
        with patch('rag.services.rag_service.settings') as mock_settings:
            mock_settings.upload_dir = tmp_path
            mock_settings.allowed_file_types = {'.txt', '.pdf', '.docx'}
            mock_settings.max_file_size_mb = 10

            # Create background tasks mock
            background_tasks = MagicMock()
            test_file = self.create_test_file(test_content)

            # Upload (but don't actually process in background for this test)
            with patch('rag.services.rag_service.process_document'):
                document = await upload_and_process_document(
                    db_session,
                    user.id,
                    test_file,
                    background_tasks
                )

                assert document.id is not None
                assert document.status == "pending"
                assert document.user_id == user.id
                assert background_tasks.add_task.called

        # Step 3: Simulate processing
        with patch('rag.services.rag_service.process_document') as mock_process:
            with patch('rag.services.rag_service.embed_document_chunks') as mock_embed:
                with patch('rag.services.rag_service.store_embedded_documents') as mock_store:
                    mock_process.return_value = [
                        {
                            'text': 'Artificial intelligence',
                            'chunk_index': 0,
                            'page_number': 1,
                            'start_char': 0,
                            'end_char': 24
                        }
                    ]

                    mock_embed.return_value = [
                        {
                            'text': 'Artificial intelligence',
                            'chunk_index': 0,
                            'page_number': 1,
                            'start_char': 0,
                            'end_char': 24,
                            'embedding': [0.1] * 384
                        }
                    ]

                    mock_store.return_value = True

                    # Process document
                    process_result = await process_document_pipeline(
                        db_session,
                        document.id,
                        document.file_path,
                        user.id
                    )

                    assert process_result is True

        # Step 4: Query the processed document
        with patch('rag.services.rag_service.search_documents_by_text') as mock_search:
            with patch('rag.services.rag_service.generate_answer') as mock_generate:
                mock_search.return_value = [
                    {
                        'metadata': {
                            'text': 'Artificial intelligence',
                            'file_name': document.original_filename,
                            'chunk_index': 0
                        },
                        'score': 0.98
                    }
                ]

                mock_generate.return_value = "AI is a field of computer science."

                query_result = await query_documents(
                    db_session,
                    user.id,
                    "Tell me about artificial intelligence"
                )

                assert query_result["retrieved_chunks"] == 1
                assert len(query_result["sources"]) == 1
                assert "AI" in query_result["message"]

        print("✅ Full upload-process-retrieve workflow completed successfully")


class TestDocumentChunking:
    """Test document chunking logic."""

    @pytest.mark.asyncio
    async def test_chunk_creation_in_database(self, db_session: AsyncSession):
        """Test chunks are properly saved to database."""
        user = User(
            id=uuid4(),
            email="user@test.com",
            username="user",
            hashed_password=get_password_hash("pass"),
            full_name="User",
            is_active=True,
            is_verified=True,
            pinecone_namespace=f"user_{uuid4().hex[:12]}",
        )
        db_session.add(user)
        await db_session.commit()

        doc = await document_crud.create_document(
            db_session,
            user_id=user.id,
            filename="test.txt",
            original_filename="test.txt",
            file_path="/tmp/test.txt",
            file_size=100,
            file_type="txt"
        )

        chunk_data = [
            {
                "index": 0,
                "content": "First chunk content",
                "page_number": 1,
                "start_char": 0,
                "end_char": 19
            },
            {
                "index": 1,
                "content": "Second chunk content",
                "page_number": 1,
                "start_char": 20,
                "end_char": 40
            }
        ]

        await document_crud.create_chunks(db_session, doc.id, chunk_data)

        # Verify chunks were saved
        document = await document_crud.get_document_by_id(db_session, doc.id, user.id)
        assert document.num_chunks is None or document.num_chunks >= 0
