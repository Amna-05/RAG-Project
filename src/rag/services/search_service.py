"""
Hybrid search service combining BM25 and semantic search.
File: src/rag/services/search_service.py
"""
import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass

from rank_bm25 import BM25Okapi
import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class SearchResult:
    """A search result with scores from both methods."""
    chunk_id: str
    content: str
    metadata: Dict[str, Any]
    bm25_score: float
    semantic_score: float
    combined_score: float


class SearchService:
    """
    Hybrid search service combining BM25 keyword matching
    with semantic similarity search.

    Uses 50/50 weighted scoring (configurable).
    """

    def __init__(
        self,
        bm25_weight: float = 0.5,
        semantic_weight: float = 0.5,
        top_k: int = 5
    ):
        """
        Initialize the search service.

        Args:
            bm25_weight: Weight for BM25 scores (default 0.5)
            semantic_weight: Weight for semantic scores (default 0.5)
            top_k: Number of results to return (default 5)
        """
        if abs(bm25_weight + semantic_weight - 1.0) > 0.01:
            raise ValueError("BM25 and semantic weights must sum to 1.0")

        self.bm25_weight = bm25_weight
        self.semantic_weight = semantic_weight
        self.top_k = top_k
        self._bm25_index: Optional[BM25Okapi] = None
        self._indexed_chunks: List[Dict[str, Any]] = []

    def build_bm25_index(self, chunks: List[Dict[str, Any]]) -> None:
        """
        Build BM25 index from chunks.

        Args:
            chunks: List of chunk dictionaries with 'content' field
        """
        if not chunks:
            logger.warning("No chunks provided for BM25 indexing")
            self._bm25_index = None
            self._indexed_chunks = []
            return

        self._indexed_chunks = chunks
        # Tokenize content for BM25
        tokenized_corpus = [
            self._tokenize(chunk.get("content", ""))
            for chunk in chunks
        ]
        self._bm25_index = BM25Okapi(tokenized_corpus)
        logger.info(f"Built BM25 index with {len(chunks)} documents")

    def _tokenize(self, text: str) -> List[str]:
        """
        Tokenize text for BM25.
        Uses simple whitespace tokenization with lowercasing.
        """
        if not text:
            return []
        # Simple tokenization: lowercase, split on whitespace
        return text.lower().split()

    def get_bm25_scores(self, query: str) -> List[float]:
        """
        Get BM25 scores for all indexed documents.

        Args:
            query: Search query string

        Returns:
            List of BM25 scores for each indexed document
        """
        if self._bm25_index is None:
            return []

        tokenized_query = self._tokenize(query)
        if not tokenized_query:
            return [0.0] * len(self._indexed_chunks)

        return self._bm25_index.get_scores(tokenized_query).tolist()

    def normalize_scores(self, scores: List[float]) -> List[float]:
        """
        Normalize scores to [0, 1] range using min-max scaling.

        Args:
            scores: List of raw scores

        Returns:
            Normalized scores in [0, 1] range
        """
        if not scores:
            return []

        scores_array = np.array(scores)
        min_score = scores_array.min()
        max_score = scores_array.max()

        if max_score == min_score:
            # All scores are the same
            return [0.5] * len(scores)

        return ((scores_array - min_score) / (max_score - min_score)).tolist()

    def hybrid_search(
        self,
        query: str,
        semantic_results: List[Dict[str, Any]],
        chunks: Optional[List[Dict[str, Any]]] = None
    ) -> List[SearchResult]:
        """
        Perform hybrid search combining BM25 and semantic scores.

        Args:
            query: Search query string
            semantic_results: Results from semantic (vector) search
                Each result should have: id, score, metadata, content
            chunks: Optional list of chunks for BM25 indexing
                (if not already indexed)

        Returns:
            List of SearchResult objects, sorted by combined score
        """
        if not semantic_results:
            logger.warning("No semantic results provided")
            return []

        # Build BM25 index if chunks provided and not yet indexed
        if chunks and len(chunks) != len(self._indexed_chunks):
            self.build_bm25_index(chunks)

        # Get content from semantic results for BM25 scoring
        contents = [r.get("content", "") for r in semantic_results]

        # Build temporary BM25 index for the candidate set
        if contents:
            tokenized = [self._tokenize(c) for c in contents]
            temp_bm25 = BM25Okapi(tokenized) if any(tokenized) else None
        else:
            temp_bm25 = None

        # Get BM25 scores for query against candidates
        if temp_bm25:
            tokenized_query = self._tokenize(query)
            bm25_scores = temp_bm25.get_scores(tokenized_query).tolist()
        else:
            bm25_scores = [0.0] * len(semantic_results)

        # Normalize scores
        normalized_bm25 = self.normalize_scores(bm25_scores)
        semantic_scores = [r.get("score", 0.0) for r in semantic_results]
        # Semantic scores from cosine similarity are already in [0, 1]
        # but normalize anyway to handle edge cases
        normalized_semantic = self.normalize_scores(semantic_scores)

        # Combine scores
        results = []
        for i, result in enumerate(semantic_results):
            bm25_norm = normalized_bm25[i] if i < len(normalized_bm25) else 0.0
            semantic_norm = normalized_semantic[i] if i < len(normalized_semantic) else 0.0

            combined = (
                self.bm25_weight * bm25_norm +
                self.semantic_weight * semantic_norm
            )

            results.append(SearchResult(
                chunk_id=result.get("id", f"chunk_{i}"),
                content=result.get("content", ""),
                metadata=result.get("metadata", {}),
                bm25_score=bm25_norm,
                semantic_score=semantic_norm,
                combined_score=combined
            ))

        # Sort by combined score descending
        results.sort(key=lambda x: x.combined_score, reverse=True)

        # Return top_k results
        return results[:self.top_k]

    def search_with_fallback(
        self,
        query: str,
        semantic_results: List[Dict[str, Any]],
        chunks: Optional[List[Dict[str, Any]]] = None
    ) -> Tuple[List[SearchResult], str]:
        """
        Search with fallback to semantic-only if BM25 fails.

        Args:
            query: Search query
            semantic_results: Results from semantic search
            chunks: Optional chunks for BM25 indexing

        Returns:
            Tuple of (results, method_used)
            method_used is "hybrid", "semantic", or "none"
        """
        try:
            results = self.hybrid_search(query, semantic_results, chunks)
            if results:
                return results, "hybrid"
        except Exception as e:
            logger.warning(f"Hybrid search failed, falling back to semantic: {e}")

        # Fallback to semantic-only
        if semantic_results:
            results = [
                SearchResult(
                    chunk_id=r.get("id", f"chunk_{i}"),
                    content=r.get("content", ""),
                    metadata=r.get("metadata", {}),
                    bm25_score=0.0,
                    semantic_score=r.get("score", 0.0),
                    combined_score=r.get("score", 0.0)
                )
                for i, r in enumerate(semantic_results)
            ]
            results.sort(key=lambda x: x.combined_score, reverse=True)
            return results[:self.top_k], "semantic"

        return [], "none"


def create_search_service(
    bm25_weight: float = 0.5,
    semantic_weight: float = 0.5,
    top_k: int = 5
) -> SearchService:
    """Factory function to create a SearchService instance."""
    return SearchService(
        bm25_weight=bm25_weight,
        semantic_weight=semantic_weight,
        top_k=top_k
    )
