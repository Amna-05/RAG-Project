"""
Mock Pinecone implementation for testing.
File: tests/mocks/pinecone_mock.py
"""
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
import numpy as np


@dataclass
class MockVector:
    """Mock vector data."""
    id: str
    values: List[float]
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MockQueryMatch:
    """Mock query result match."""
    id: str
    score: float
    metadata: Dict[str, Any] = field(default_factory=dict)


class MockPineconeIndex:
    """
    Mock Pinecone index for testing.

    Stores vectors in memory and provides similarity search.
    """

    def __init__(self, dimension: int = 384):
        self.dimension = dimension
        self.vectors: Dict[str, MockVector] = {}
        self.namespaces: Dict[str, Dict[str, MockVector]] = {}

    def upsert(
        self,
        vectors: List[tuple],
        namespace: str = ""
    ) -> Dict[str, int]:
        """Insert or update vectors."""
        if namespace not in self.namespaces:
            self.namespaces[namespace] = {}

        for vec in vectors:
            if len(vec) == 2:
                id_, values = vec
                metadata = {}
            else:
                id_, values, metadata = vec

            mock_vec = MockVector(id=id_, values=values, metadata=metadata)
            self.namespaces[namespace][id_] = mock_vec

        return {"upserted_count": len(vectors)}

    def query(
        self,
        vector: List[float],
        top_k: int = 5,
        namespace: str = "",
        include_metadata: bool = True,
        filter: Optional[Dict] = None
    ) -> Dict[str, List[MockQueryMatch]]:
        """Query similar vectors using cosine similarity."""
        if namespace not in self.namespaces:
            return {"matches": []}

        query_vec = np.array(vector)
        matches = []

        for vec_id, mock_vec in self.namespaces[namespace].items():
            # Apply filter if provided
            if filter and not self._matches_filter(mock_vec.metadata, filter):
                continue

            # Calculate cosine similarity
            stored_vec = np.array(mock_vec.values)
            similarity = self._cosine_similarity(query_vec, stored_vec)

            matches.append(MockQueryMatch(
                id=vec_id,
                score=similarity,
                metadata=mock_vec.metadata if include_metadata else {}
            ))

        # Sort by score descending and take top_k
        matches.sort(key=lambda x: x.score, reverse=True)
        return {"matches": matches[:top_k]}

    def delete(
        self,
        ids: Optional[List[str]] = None,
        namespace: str = "",
        delete_all: bool = False,
        filter: Optional[Dict] = None
    ) -> Dict:
        """Delete vectors."""
        if namespace not in self.namespaces:
            return {"deleted_count": 0}

        if delete_all:
            count = len(self.namespaces[namespace])
            self.namespaces[namespace] = {}
            return {"deleted_count": count}

        if ids:
            count = 0
            for id_ in ids:
                if id_ in self.namespaces[namespace]:
                    del self.namespaces[namespace][id_]
                    count += 1
            return {"deleted_count": count}

        return {"deleted_count": 0}

    def describe_index_stats(self) -> Dict:
        """Get index statistics."""
        total_count = sum(len(ns) for ns in self.namespaces.values())
        return {
            "dimension": self.dimension,
            "total_vector_count": total_count,
            "namespaces": {
                ns: {"vector_count": len(vecs)}
                for ns, vecs in self.namespaces.items()
            }
        }

    @staticmethod
    def _cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
        """Calculate cosine similarity between two vectors."""
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return float(np.dot(a, b) / (norm_a * norm_b))

    @staticmethod
    def _matches_filter(metadata: Dict, filter: Dict) -> bool:
        """Check if metadata matches filter conditions."""
        for key, condition in filter.items():
            if key not in metadata:
                return False
            if isinstance(condition, dict):
                # Handle operators like $eq, $in, $gt, etc.
                for op, value in condition.items():
                    if op == "$eq" and metadata[key] != value:
                        return False
                    if op == "$in" and metadata[key] not in value:
                        return False
                    if op == "$gt" and metadata[key] <= value:
                        return False
                    if op == "$lt" and metadata[key] >= value:
                        return False
            elif metadata[key] != condition:
                return False
        return True
