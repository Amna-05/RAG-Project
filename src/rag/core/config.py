"""
Enhanced configuration for multi-user RAG system.
File: src/rag/core/config.py
"""
from pathlib import Path
from typing import Optional, List
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with validation."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra='ignore'
    )
    
    # ============ Application Settings ============
    app_name: str = "RAG System"
    app_version: str = "1.0.0"
    debug: bool = False
    api_prefix: str = "/api/v1"
    
    # ============ Database Settings ============
    database_url: str = Field(
        default="postgresql+asyncpg://postgres:password@localhost:5432/rag_db"
    )
    db_pool_size: int = 5
    db_max_overflow: int = 10
    db_pool_timeout: int = 30
    db_echo: bool = False
    
    # ============ JWT Settings ============
    jwt_secret_key: str = Field(default="change-this-secret-key")
    jwt_refresh_secret_key: str = Field(default="change-this-refresh-key")
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7
    
    # ============ Security Settings ============
    cors_origins: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:3001", "http://localhost:8000"]
    )
    cors_credentials: bool = True
    cors_methods: List[str] = ["*"]
    cors_headers: List[str] = ["*"]
    
    # ============ Pinecone Settings ============
    pinecone_api_key: str = Field(default="")
    pinecone_index_name: str = Field(default="rag-index")
    pinecone_environment: Optional[str] = None
    pinecone_use_namespaces: bool = True
    
    # ============ Embedding Settings ============
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    embedding_dimension: int = 384
    embedding_batch_size: int = 32
    embedding_cache_enabled: bool = True
    
    # ============ OpenAI Settings ============
    openai_api_key: str = Field(default="")
    openai_model: str = "gpt-4o-mini"
    openai_temperature: float = 0.7
    openai_max_tokens: int = 1024
    
    # ============ Google Gemini Settings ============
    google_api_key: str = Field(default="")
    gemini_model: str = "gemini-2.5-flash"
    gemini_temperature: float = 0.7
    gemini_max_tokens: int = 1024
    
    # ============ Anthropic Claude Settings ============
    anthropic_api_key: str = Field(default="")
    claude_model: str = "claude-3-5-sonnet-20241022"
    claude_temperature: float = 0.7
    claude_max_tokens: int = 1024
    
    # ============ xAI Grok Settings ============
    xai_api_key: str = Field(default="")
    grok_model: str = "grok-3"
    grok_temperature: float = 0.7
    grok_max_tokens: int = 1024

    # ============ Ollama (Local) Settings ============
    use_ollama: bool = False
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.2"
    
    # ============ Document Processing Settings ============
    chunk_size: int = 1000
    chunk_overlap: int = 200
    max_file_size_mb: int = 10
    allowed_file_types: List[str] = [".pdf", ".docx", ".txt", ".json"]
    enable_ocr: bool = False
    
    # ============ Storage Settings ============
    upload_dir: Path = Path("data/uploads")
    data_dir: Path = Path("data")
    cache_dir: Path = Path("data/embeddings_cache")
    logs_dir: Path = Path("logs")
    
    @field_validator('upload_dir', 'data_dir', 'cache_dir', 'logs_dir')
    @classmethod
    def create_directories(cls, path: Path) -> Path:
        """Create directories if they don't exist."""
        path.mkdir(exist_ok=True, parents=True)
        return path
    
    # ============ Search Settings ============
    default_top_k: int = 5
    min_relevance_score: float = 0.5
    enable_hybrid_search: bool = False

    # ============ Email Settings (SMTP) ============
    resend_api_key: str = Field(default="")
    smtp_from_email: str = Field(default="noreply@example.com")
    smtp_from_name: str = Field(default="RAG Application")

    # ============ Frontend Settings ============
    frontend_url: str = Field(default="http://localhost:3000")

    # ============ Logging Settings ============
    log_level: str = "INFO"
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    # ============ Rate Limiting Settings ============
    # Redis URL for distributed rate limit storage
    redis_url: str = Field(default="redis://localhost:6379/0")

    # Storage backend: "redis" or "memory"
    rate_limit_storage: str = Field(default="memory")

    # Chat endpoint limits (per user)
    rate_limit_chat_requests: int = Field(default=10)
    rate_limit_chat_window_minutes: int = Field(default=1)

    # Upload endpoint limits (per user)
    rate_limit_upload_requests: int = Field(default=2)
    rate_limit_upload_window_minutes: int = Field(default=10)

    # Auth endpoint limits (per IP)
    rate_limit_auth_requests: int = Field(default=5)
    rate_limit_auth_window_minutes: int = Field(default=1)

    # Global rate limiting toggle
    rate_limit_enabled: bool = Field(default=True)


# Singleton instance
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Get application settings (singleton pattern)."""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings