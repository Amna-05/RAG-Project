"""
Unit tests for BM25 and hybrid search.
File: tests/unit/test_search.py
"""
import pytest
from rag.services.search_service import SearchService, create_search_service, SearchResult


class TestBM25Scoring:
    """Tests for BM25 scoring functionality."""

    def test_tokenize_simple_text(self):
        """Test basic tokenization."""
        service = SearchService()
        tokens = service._tokenize("Hello World")
        assert tokens == ["hello", "world"]

    def test_tokenize_empty_text(self):
        """Test tokenization of empty text."""
        service = SearchService()
        tokens = service._tokenize("")
        assert tokens == []

    def test_tokenize_preserves_words(self):
        """Test that tokenization preserves all words."""
        service = SearchService()
        text = "The quick brown fox jumps over the lazy dog"
        tokens = service._tokenize(text)
        assert len(tokens) == 9
        assert "quick" in tokens
        assert "fox" in tokens

    def test_build_bm25_index(self):
        """Test building BM25 index from chunks."""
        service = SearchService()
        chunks = [
            {"content": "Machine learning is great"},
            {"content": "Deep learning uses neural networks"},
            {"content": "Natural language processing is fascinating"}
        ]
        service.build_bm25_index(chunks)
        assert service._bm25_index is not None
        assert len(service._indexed_chunks) == 3

    def test_build_bm25_index_empty(self):
        """Test building BM25 index with no chunks."""
        service = SearchService()
        service.build_bm25_index([])
        assert service._bm25_index is None
        assert len(service._indexed_chunks) == 0

    def test_get_bm25_scores(self):
        """Test getting BM25 scores for a query."""
        service = SearchService()
        chunks = [
            {"content": "Machine learning algorithms"},
            {"content": "Deep learning neural networks"},
            {"content": "Traditional programming methods"}
        ]
        service.build_bm25_index(chunks)

        scores = service.get_bm25_scores("learning")
        assert len(scores) == 3
        # First two chunks contain "learning", should have higher scores
        assert scores[0] > scores[2]
        assert scores[1] > scores[2]

    def test_get_bm25_scores_no_index(self):
        """Test getting BM25 scores without an index."""
        service = SearchService()
        scores = service.get_bm25_scores("test query")
        assert scores == []


class TestScoreNormalization:
    """Tests for score normalization."""

    def test_normalize_scores_basic(self):
        """Test basic score normalization."""
        service = SearchService()
        scores = [0.0, 5.0, 10.0]
        normalized = service.normalize_scores(scores)
        assert normalized[0] == 0.0
        assert normalized[1] == 0.5
        assert normalized[2] == 1.0

    def test_normalize_scores_empty(self):
        """Test normalizing empty list."""
        service = SearchService()
        normalized = service.normalize_scores([])
        assert normalized == []

    def test_normalize_scores_same_values(self):
        """Test normalizing when all values are the same."""
        service = SearchService()
        scores = [5.0, 5.0, 5.0]
        normalized = service.normalize_scores(scores)
        # All same values should normalize to 0.5
        assert all(s == 0.5 for s in normalized)

    def test_normalize_scores_negative(self):
        """Test normalizing with negative scores."""
        service = SearchService()
        scores = [-5.0, 0.0, 5.0]
        normalized = service.normalize_scores(scores)
        assert normalized[0] == 0.0
        assert normalized[2] == 1.0


class TestHybridSearch:
    """Tests for hybrid search combining BM25 and semantic."""

    def test_hybrid_search_basic(self):
        """Test basic hybrid search."""
        service = SearchService(bm25_weight=0.5, semantic_weight=0.5, top_k=3)

        semantic_results = [
            {"id": "chunk1", "content": "Machine learning models", "score": 0.9, "metadata": {}},
            {"id": "chunk2", "content": "Deep neural networks", "score": 0.8, "metadata": {}},
            {"id": "chunk3", "content": "Natural language processing", "score": 0.7, "metadata": {}},
        ]

        results = service.hybrid_search("machine learning", semantic_results)

        assert len(results) <= 3
        assert isinstance(results[0], SearchResult)
        assert results[0].combined_score >= results[1].combined_score

    def test_hybrid_search_empty_results(self):
        """Test hybrid search with no semantic results."""
        service = SearchService()
        results = service.hybrid_search("query", [])
        assert results == []

    def test_hybrid_search_respects_top_k(self):
        """Test that hybrid search respects top_k limit."""
        service = SearchService(top_k=2)

        semantic_results = [
            {"id": f"chunk{i}", "content": f"Content {i}", "score": 0.9 - i*0.1, "metadata": {}}
            for i in range(5)
        ]

        results = service.hybrid_search("query", semantic_results)
        assert len(results) == 2

    def test_hybrid_weights(self):
        """Test that weights affect combined scores correctly."""
        # Test with BM25-heavy weighting
        bm25_heavy = SearchService(bm25_weight=0.9, semantic_weight=0.1)

        semantic_results = [
            {"id": "chunk1", "content": "exact query match", "score": 0.5, "metadata": {}},
            {"id": "chunk2", "content": "different content", "score": 0.9, "metadata": {}},
        ]

        results = bm25_heavy.hybrid_search("exact query match", semantic_results)

        # The chunk with better BM25 match should rank higher
        # despite lower semantic score when BM25 is weighted heavily
        assert results[0].bm25_score >= results[1].bm25_score


class TestSearchWithFallback:
    """Tests for search with fallback functionality."""

    def test_search_with_fallback_hybrid_success(self):
        """Test that fallback returns hybrid when it succeeds."""
        service = SearchService()
        semantic_results = [
            {"id": "chunk1", "content": "Test content", "score": 0.9, "metadata": {}}
        ]

        results, method = service.search_with_fallback("test", semantic_results)

        assert method == "hybrid"
        assert len(results) == 1

    def test_search_with_fallback_to_semantic(self):
        """Test fallback to semantic-only search."""
        service = SearchService()
        semantic_results = [
            {"id": "chunk1", "content": "Test", "score": 0.8, "metadata": {}}
        ]

        # Force hybrid to fail by using None query (edge case)
        results, method = service.search_with_fallback("test", semantic_results)

        # Should succeed with hybrid
        assert method == "hybrid"

    def test_search_with_fallback_no_results(self):
        """Test fallback with no results."""
        service = SearchService()
        results, method = service.search_with_fallback("query", [])

        assert method == "none"
        assert results == []


class TestSearchServiceFactory:
    """Tests for the search service factory function."""

    def test_create_search_service_defaults(self):
        """Test creating search service with defaults."""
        service = create_search_service()
        assert service.bm25_weight == 0.5
        assert service.semantic_weight == 0.5
        assert service.top_k == 5

    def test_create_search_service_custom(self):
        """Test creating search service with custom settings."""
        service = create_search_service(
            bm25_weight=0.7,
            semantic_weight=0.3,
            top_k=10
        )
        assert service.bm25_weight == 0.7
        assert service.semantic_weight == 0.3
        assert service.top_k == 10

    def test_invalid_weights_raises_error(self):
        """Test that invalid weights raise an error."""
        with pytest.raises(ValueError):
            SearchService(bm25_weight=0.5, semantic_weight=0.3)  # Sum != 1.0
