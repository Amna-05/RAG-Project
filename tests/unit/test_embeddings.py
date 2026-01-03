"""
Unit tests for embeddings module.
File: tests/unit/test_embeddings.py
"""
import pytest
import numpy as np
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from rag.embeddings import (
    EmbeddingGenerator,
    SimpleEmbeddingCache,
    embed_document_chunks
)


class TestSimpleEmbeddingCache:
    """Test the SimpleEmbeddingCache class."""

    def test_cache_initialization(self, tmp_path):
        """Test cache directory initialization."""
        with patch('rag.embeddings.get_settings') as mock_settings:
            mock_settings.return_value.data_dir = tmp_path
            cache = SimpleEmbeddingCache()
            assert cache.cache_dir == tmp_path / "embeddings_cache"
            assert cache.cache_dir.exists()

    def test_get_cache_key_deterministic(self):
        """Test cache key generation is deterministic."""
        with patch('rag.embeddings.get_settings'):
            cache = SimpleEmbeddingCache()
            text = "Test embedding text"
            model = "test-model"

            key1 = cache._get_cache_key(text, model)
            key2 = cache._get_cache_key(text, model)

            assert key1 == key2

    def test_get_cache_key_different_for_different_text(self):
        """Test different texts produce different cache keys."""
        with patch('rag.embeddings.get_settings'):
            cache = SimpleEmbeddingCache()
            text1 = "First text"
            text2 = "Second text"
            model = "test-model"

            key1 = cache._get_cache_key(text1, model)
            key2 = cache._get_cache_key(text2, model)

            assert key1 != key2

    def test_get_cache_key_different_for_different_model(self):
        """Test different models produce different cache keys."""
        with patch('rag.embeddings.get_settings'):
            cache = SimpleEmbeddingCache()
            text = "Same text"
            model1 = "model-1"
            model2 = "model-2"

            key1 = cache._get_cache_key(text, model1)
            key2 = cache._get_cache_key(text, model2)

            assert key1 != key2

    def test_set_and_get_embedding(self, tmp_path):
        """Test saving and retrieving embedding from cache."""
        with patch('rag.embeddings.get_settings') as mock_settings:
            mock_settings.return_value.data_dir = tmp_path
            cache = SimpleEmbeddingCache()

            text = "Test text"
            model = "test-model"
            embedding = np.array([0.1, 0.2, 0.3])

            # Set embedding
            cache.set(text, model, embedding)

            # Get embedding
            retrieved = cache.get(text, model)
            assert retrieved is not None
            np.testing.assert_array_almost_equal(retrieved, embedding)

    def test_get_nonexistent_embedding(self, tmp_path):
        """Test getting nonexistent embedding returns None."""
        with patch('rag.embeddings.get_settings') as mock_settings:
            mock_settings.return_value.data_dir = tmp_path
            cache = SimpleEmbeddingCache()

            result = cache.get("nonexistent", "model")
            assert result is None

    def test_cache_handles_read_errors_gracefully(self, tmp_path):
        """Test cache handles read errors gracefully."""
        with patch('rag.embeddings.get_settings') as mock_settings:
            mock_settings.return_value.data_dir = tmp_path
            cache = SimpleEmbeddingCache()

            # Mock corrupted cache file
            with patch('numpy.load', side_effect=Exception("Corrupted file")):
                result = cache.get("text", "model")
                assert result is None

    def test_cache_handles_write_errors_gracefully(self, tmp_path):
        """Test cache handles write errors gracefully."""
        with patch('rag.embeddings.get_settings') as mock_settings:
            mock_settings.return_value.data_dir = tmp_path
            cache = SimpleEmbeddingCache()

            # Mock write error
            with patch('numpy.save', side_effect=Exception("Write error")):
                # Should not raise
                cache.set("text", "model", np.array([0.1, 0.2]))


class TestEmbeddingGenerator:
    """Test the EmbeddingGenerator class."""

    def test_initialization_with_defaults(self):
        """Test EmbeddingGenerator initialization with default values."""
        with patch('rag.embeddings.get_settings') as mock_settings:
            mock_settings.return_value.embedding_model = 'sentence-transformers/all-MiniLM-L6-v2'
            generator = EmbeddingGenerator()

            assert generator.model_name == 'sentence-transformers/all-MiniLM-L6-v2'
            assert generator.use_cache is True
            assert generator.model is None
            assert generator.cache is not None

    def test_initialization_with_custom_model(self):
        """Test EmbeddingGenerator with custom model name."""
        with patch('rag.embeddings.get_settings'):
            generator = EmbeddingGenerator(model_name="custom-model")
            assert generator.model_name == "custom-model"

    def test_initialization_without_cache(self):
        """Test EmbeddingGenerator without caching."""
        with patch('rag.embeddings.get_settings'):
            generator = EmbeddingGenerator(use_cache=False)
            assert generator.use_cache is False
            assert generator.cache is None

    def test_clean_text_removes_extra_whitespace(self):
        """Test text cleaning removes extra whitespace."""
        with patch('rag.embeddings.get_settings'):
            generator = EmbeddingGenerator()

            dirty = "  Multiple   spaces   between   words  "
            clean = generator._clean_text(dirty)

            assert clean == "Multiple spaces between words"

    def test_clean_text_truncates_long_text(self):
        """Test text cleaning truncates very long text."""
        with patch('rag.embeddings.get_settings'):
            generator = EmbeddingGenerator()

            long_text = "a" * 2500
            clean = generator._clean_text(long_text)

            assert len(clean) <= 2003  # 2000 + "..."
            assert clean.endswith("...")

    def test_clean_text_handles_empty_string(self):
        """Test text cleaning handles empty strings."""
        with patch('rag.embeddings.get_settings'):
            generator = EmbeddingGenerator()

            assert generator._clean_text("") == ""
            assert generator._clean_text(None) == ""

    def test_embed_single_text_returns_none_for_empty_text(self):
        """Test embedding empty text returns None."""
        with patch('rag.embeddings.get_settings'):
            generator = EmbeddingGenerator()
            result = generator.embed_single_text("")
            assert result is None

    @patch('rag.embeddings.SentenceTransformer')
    def test_embed_single_text_success(self, mock_transformer):
        """Test successful single text embedding."""
        mock_model = MagicMock()
        mock_embedding = np.array([0.1, 0.2, 0.3])
        mock_model.encode.return_value = np.array([[0.1, 0.2, 0.3]])
        mock_transformer.return_value = mock_model

        with patch('rag.embeddings.get_settings'):
            generator = EmbeddingGenerator(use_cache=False)
            result = generator.embed_single_text("Test text")

            assert result is not None
            np.testing.assert_array_almost_equal(result, mock_embedding)

    @patch('rag.embeddings.SentenceTransformer')
    def test_embed_single_text_uses_cache(self, mock_transformer):
        """Test that single text embedding uses cache."""
        mock_model = MagicMock()
        mock_model.encode.return_value = np.array([[0.1, 0.2, 0.3]])
        mock_transformer.return_value = mock_model

        with patch('rag.embeddings.get_settings'):
            with patch('rag.embeddings.SimpleEmbeddingCache') as mock_cache_class:
                mock_cache = MagicMock()
                mock_cache_class.return_value = mock_cache

                # First call: cache miss
                mock_cache.get.return_value = None
                generator = EmbeddingGenerator(use_cache=True)
                generator.embed_single_text("Test text")

                # Verify cache.set was called
                assert mock_cache.set.called

    def test_embed_texts_empty_list(self):
        """Test embedding empty list of texts."""
        with patch('rag.embeddings.get_settings'):
            generator = EmbeddingGenerator()
            result = generator.embed_texts([])
            assert result == []

    @patch('rag.embeddings.SentenceTransformer')
    def test_embed_texts_batch_processing(self, mock_transformer):
        """Test batch processing of multiple texts."""
        mock_model = MagicMock()
        mock_model.encode.return_value = np.array([
            [0.1, 0.2, 0.3],
            [0.4, 0.5, 0.6],
            [0.7, 0.8, 0.9]
        ])
        mock_transformer.return_value = mock_model

        with patch('rag.embeddings.get_settings'):
            generator = EmbeddingGenerator(use_cache=False)
            texts = ["Text 1", "Text 2", "Text 3"]
            results = generator.embed_texts(texts)

            assert len(results) == 3
            assert all(r is not None for r in results)

    @patch('rag.embeddings.SentenceTransformer')
    def test_embed_texts_with_batch_size(self, mock_transformer):
        """Test batch processing respects batch size."""
        mock_model = MagicMock()
        # Create embeddings for 6 texts
        embeddings = np.random.randn(6, 384)
        mock_model.encode.return_value = embeddings
        mock_transformer.return_value = mock_model

        with patch('rag.embeddings.get_settings'):
            generator = EmbeddingGenerator(use_cache=False)
            texts = [f"Text {i}" for i in range(6)]
            results = generator.embed_texts(texts, batch_size=2)

            assert len(results) == 6
            # Verify model.encode was called 3 times (batch_size=2, 6 texts = 3 batches)
            assert mock_model.encode.call_count == 3

    @patch('rag.embeddings.SentenceTransformer')
    def test_embed_documents_success(self, mock_transformer):
        """Test embedding documents with metadata."""
        mock_model = MagicMock()
        embeddings = np.random.randn(2, 384)
        mock_model.encode.return_value = embeddings
        mock_transformer.return_value = mock_model

        with patch('rag.embeddings.get_settings'):
            generator = EmbeddingGenerator(use_cache=False)

            documents = [
                {'id': 'doc1', 'text': 'First document'},
                {'id': 'doc2', 'text': 'Second document'}
            ]

            results = generator.embed_documents(documents)

            assert len(results) == 2
            assert all('embedding' in doc for doc in results)
            assert all('embedding_model' in doc for doc in results)

    @patch('rag.embeddings.SentenceTransformer')
    def test_embed_documents_handles_missing_text(self, mock_transformer):
        """Test embedding documents handles missing text field."""
        mock_model = MagicMock()
        mock_model.encode.return_value = np.array([[0.1, 0.2, 0.3]])
        mock_transformer.return_value = mock_model

        with patch('rag.embeddings.get_settings'):
            generator = EmbeddingGenerator(use_cache=False)

            documents = [
                {'id': 'doc1'},  # Missing 'text'
                {'id': 'doc2', 'text': 'Has text'}
            ]

            results = generator.embed_documents(documents)

            assert len(results) == 2
            # First doc should have None embedding due to missing text
            assert results[0]['embedding'] is None


class TestEmbeddingProcessing:
    """Test document embedding processing."""

    @patch('rag.embeddings.EmbeddingGenerator')
    def test_embed_document_chunks_function(self, mock_generator_class):
        """Test the convenience function embed_document_chunks."""
        mock_generator = MagicMock()
        mock_generator_class.return_value = mock_generator

        documents = [
            {'id': 'doc1', 'text': 'First chunk'},
            {'id': 'doc2', 'text': 'Second chunk'}
        ]

        expected = [
            {'id': 'doc1', 'text': 'First chunk', 'embedding': [0.1, 0.2]},
            {'id': 'doc2', 'text': 'Second chunk', 'embedding': [0.3, 0.4]}
        ]

        mock_generator.embed_documents.return_value = expected

        result = embed_document_chunks(documents)

        assert result == expected
        mock_generator_class.assert_called_once_with(use_cache=True)
        mock_generator.embed_documents.assert_called_once_with(documents)

    @patch('rag.embeddings.SentenceTransformer')
    def test_embed_documents_preserves_metadata(self, mock_transformer):
        """Test that embedding preserves document metadata."""
        mock_model = MagicMock()
        mock_model.encode.return_value = np.random.randn(2, 384)
        mock_transformer.return_value = mock_model

        with patch('rag.embeddings.get_settings'):
            generator = EmbeddingGenerator(use_cache=False)

            documents = [
                {
                    'id': 'doc1',
                    'text': 'Content',
                    'page': 1,
                    'source': 'file.pdf'
                }
            ]

            result = generator.embed_documents(documents)

            assert result[0]['id'] == 'doc1'
            assert result[0]['page'] == 1
            assert result[0]['source'] == 'file.pdf'


class TestEmbeddingEdgeCases:
    """Test edge cases and error conditions."""

    def test_clean_text_with_unicode(self):
        """Test text cleaning handles unicode properly."""
        with patch('rag.embeddings.get_settings'):
            generator = EmbeddingGenerator()

            unicode_text = "Hello 世界 مرحبا мир"
            clean = generator._clean_text(unicode_text)

            assert "世界" in clean
            assert "مرحبا" in clean
            assert "мир" in clean

    @patch('rag.embeddings.SentenceTransformer')
    def test_embed_single_text_model_load_failure(self, mock_transformer):
        """Test handling of model load failure."""
        mock_transformer.side_effect = Exception("Model not found")

        with patch('rag.embeddings.get_settings'):
            generator = EmbeddingGenerator(use_cache=False)
            result = generator.embed_single_text("Test")

            assert result is None

    @patch('rag.embeddings.SentenceTransformer')
    def test_embed_texts_partial_failure(self, mock_transformer):
        """Test batch processing handles partial failures."""
        mock_model = MagicMock()
        # Simulate a failure in the second batch
        mock_model.encode.side_effect = [
            np.array([[0.1, 0.2, 0.3]]),  # First batch succeeds
            Exception("Encoding failed")     # Second batch fails
        ]
        mock_transformer.return_value = mock_model

        with patch('rag.embeddings.get_settings'):
            generator = EmbeddingGenerator(use_cache=False)
            texts = ["Text 1", "Text 2", "Text 3"]
            results = generator.embed_texts(texts, batch_size=2)

            # Should have results but some might be None
            assert len(results) == 3
            assert any(r is not None for r in results)
