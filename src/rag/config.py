"""Configuration management for RAG system."""
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import field_validator, ConfigDict


class Settings(BaseSettings):
    """Application settings with validation."""

    # ✅ Pydantic v2 style config
    model_config = ConfigDict(
        env_file=".env",
        env_file_encoding="utf-8"
    )

    # Basic settings
    project_name: str = "rag-project"
    debug: bool = False

    # API keys & model settings
    pinecone_api_key: Optional[str] = None
    google_api_key: Optional[str] = None
    pinecone_index_name: Optional[str] = None
    embedding_model: Optional[str] = None

    # Processing settings
    chunk_size: int = 1000
    chunk_overlap: int = 200

    # Paths
    data_dir: Path = Path("data")
    logs_dir: Path = Path("logs")

    @field_validator('data_dir', 'logs_dir')
    @classmethod
    def create_directories(cls, path: Path) -> Path:
        """Create directories if they don't exist."""
        path.mkdir(exist_ok=True, parents=True)
        return path


def get_settings() -> Settings:
    """Get application settings (singleton pattern)."""
    return Settings()


# Test function
def test_config():
    """Test configuration loading."""
    settings = get_settings()
    print(f"✅ Config loaded: {settings.project_name}")
    print(f"✅ Data dir: {settings.data_dir}")
    print(f"✅ Chunk size: {settings.chunk_size}")

    if settings.pinecone_api_key:
        print(f"🔑 Pinecone API Key: {settings.pinecone_api_key}")
    else:
        print("⚠️ No Pinecone API Key set")

    if settings.google_api_key:
        print(f"🔑 Google API Key: {settings.google_api_key}")
    else:
        print("⚠️ No Google API Key set")

    return True


if __name__ == "__main__":
    test_config()
