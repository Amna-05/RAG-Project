"""
Test fixtures and configuration.
File: tests/conftest.py
"""
import pytest
import asyncio
from typing import AsyncGenerator, Generator
from datetime import datetime, timedelta
from uuid import uuid4
import secrets
import hashlib

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool
from httpx import AsyncClient, ASGITransport

from rag.main import app
from rag.core.database import Base, get_db
from rag.models.user import User
from rag.models.document import Document, DocumentChunk
from rag.models.password_reset import PasswordResetToken
from rag.core.security import get_password_hash


# Test database URL (SQLite for speed)
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
async def async_engine():
    """Create async engine for tests."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest.fixture(scope="function")
async def db_session(async_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create a test database session."""
    async_session = async_sessionmaker(
        async_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    async with async_session() as session:
        yield session
        await session.rollback()


@pytest.fixture(scope="function")
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Create a test client with overridden dependencies."""
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest.fixture
async def test_user(db_session: AsyncSession) -> User:
    """Create a test user."""
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
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def test_document(db_session: AsyncSession, test_user: User) -> Document:
    """Create a test document."""
    doc = Document(
        id=uuid4(),
        user_id=test_user.id,
        filename="test_doc.pdf",
        original_filename="test_doc.pdf",
        file_path="/data/uploads/test_doc.pdf",
        file_size=1024,
        file_type="pdf",
        status="completed",
        num_chunks=3,
        bm25_indexed=True,
    )
    db_session.add(doc)
    await db_session.commit()
    await db_session.refresh(doc)
    return doc


@pytest.fixture
async def test_chunks(db_session: AsyncSession, test_document: Document) -> list[DocumentChunk]:
    """Create test document chunks."""
    chunks = [
        DocumentChunk(
            id=uuid4(),
            document_id=test_document.id,
            chunk_index=i,
            content=f"This is test content for chunk {i}. It contains some relevant information.",
            page_number=1,
            start_char=i * 100,
            end_char=(i + 1) * 100,
        )
        for i in range(3)
    ]
    for chunk in chunks:
        db_session.add(chunk)
    await db_session.commit()
    return chunks


@pytest.fixture
def password_reset_token() -> tuple[str, str]:
    """Generate a password reset token and its hash."""
    token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    return token, token_hash


@pytest.fixture
async def test_password_reset(
    db_session: AsyncSession,
    test_user: User,
    password_reset_token: tuple[str, str]
) -> tuple[PasswordResetToken, str]:
    """Create a test password reset token."""
    token, token_hash = password_reset_token
    reset = PasswordResetToken(
        id=uuid4(),
        user_id=test_user.id,
        token_hash=token_hash,
        expires_at=datetime.utcnow() + timedelta(hours=1),
    )
    db_session.add(reset)
    await db_session.commit()
    await db_session.refresh(reset)
    return reset, token


@pytest.fixture
def sample_text() -> str:
    """Sample text for chunking tests."""
    return """
    This is a sample document for testing purposes.
    It contains multiple paragraphs that will be chunked.

    The document discusses various topics including:
    - Machine learning and AI
    - Natural language processing
    - Document retrieval systems

    This paragraph provides additional context about the RAG system.
    Retrieval Augmented Generation combines the power of language models
    with external knowledge bases to provide more accurate responses.
    """ * 10  # Repeat for longer text


@pytest.fixture
def mock_embedding() -> list[float]:
    """Mock embedding vector (384 dimensions)."""
    return [0.1] * 384
