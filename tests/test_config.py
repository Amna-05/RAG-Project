"""Test configuration module."""
import pytest
from rag.config import get_settings, Settings


def test_settings_creation():
    """Test that settings can be created."""
    settings = get_settings()
    assert settings.project_name == "rag-project"
    assert settings.chunk_size == 1000


def test_settings_validation():
    """Test settings validation."""
    settings = Settings(chunk_size=500)
    assert settings.chunk_size == 500


def test_directories_created():
    """Test that directories are created."""
    settings = get_settings()
    assert settings.data_dir.exists()
    assert settings.logs_dir.exists()

def test_api_keys_loaded():
    settings = get_settings()
    assert settings.pinecone_api_key is not None, "Pinecone API Key is missing!"
    assert settings.google_api_key is not None, "Google API Key is missing!"    