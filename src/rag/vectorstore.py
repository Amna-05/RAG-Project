"""
Simple Pinecone vector database integration.
Clean, focused, gets the job done.
"""
import logging
from typing import List, Dict, Any
import time

try:
    from pinecone import Pinecone, ServerlessSpec
    PINECONE_AVAILABLE = True
except ImportError:
    Pinecone = None
    ServerlessSpec = None
    PINECONE_AVAILABLE = False

from rag.config import get_settings
from rag.embeddings import EmbeddingGenerator

logger = logging.getLogger(__name__)


class SimplePineconeStore:
    """Simple Pinecone vector database client."""

    def __init__(self):
        """Initialize Pinecone connection."""
        settings = get_settings()

        if not PINECONE_AVAILABLE:
            raise ImportError("❌ Pinecone not installed. Run: uv add pinecone")

        if not settings.pinecone_api_key:
            raise ValueError("❌ PINECONE_API_KEY not set in .env file")

        if not settings.pinecone_index_name:
            raise ValueError("❌ PINECONE_INDEX_NAME not set in .env file")

        # Configure Pinecone
        self.pc = Pinecone(api_key=settings.pinecone_api_key)
        self.index_name = settings.pinecone_index_name
        self.index = None

        logger.info(f"🌲 Initialized Pinecone client for index: {self.index_name}")

    def connect_to_index(self) -> bool:
        """Connect to existing Pinecone index."""
        try:
            self.index = self.pc.Index(self.index_name)

            # Test connection
            stats = self.pc.describe_index(self.index_name)
            total_vectors = stats["dimension"]
            logger.info(f"✅ Connected to index: {self.index_name}")
            logger.info(f"📊 Index dimension: {total_vectors}")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to connect to index {self.index_name}: {e}")
            return False

    def create_index_if_not_exists(self, dimension: int = 384) -> bool:
        """Create index if it doesn't exist."""
        try:
            # Check if index exists
            existing_indexes = [i["name"] for i in self.pc.list_indexes()]

            if self.index_name in existing_indexes:
                logger.info(f"📍 Index {self.index_name} already exists")
                return self.connect_to_index()

            # Create new index
            logger.info(f"🏗️ Creating index: {self.index_name}")

            self.pc.create_index(
                name=self.index_name,
                dimension=dimension,
                metric="cosine",
                spec=ServerlessSpec(cloud="aws", region="us-east-1")
            )

            # Wait for index to be ready
            logger.info("⏳ Waiting for index to be ready...")
            while not self.pc.describe_index(self.index_name)["status"]["ready"]:
                time.sleep(1)

            logger.info(f"✅ Index {self.index_name} created successfully")
            return self.connect_to_index()

        except Exception as e:
            logger.error(f"❌ Failed to create index: {e}")
            return False

    def upsert_documents(self, embedded_docs: List[Dict[str, Any]]) -> bool:
        """Upload embedded documents to Pinecone."""
        if not self.index and not self.connect_to_index():
            logger.error("❌ No index connection")
            return False

        if not embedded_docs:
            logger.warning("⚠️ No documents to upsert")
            return True

        logger.info(f"📤 Upserting {len(embedded_docs)} documents to Pinecone")

        try:
            vectors = []
            for doc in embedded_docs:
                if doc.get('embedding') is None:
                    logger.warning(f"⚠️ Skipping document without embedding: {doc.get('id')}")
                    continue

                vectors.append({
                    'id': str(doc.get('id', f"doc_{len(vectors)}")),
                    'values': doc['embedding'],
                    'metadata': {
                        'text': doc.get('text', ''),
                        'source': doc.get('source', ''),
                        'file_name': doc.get('file_name', ''),
                        'chunk_index': doc.get('chunk_index', 0)
                    }
                })

            if not vectors:
                logger.error("❌ No valid vectors to upsert")
                return False

            self.index.upsert(vectors=vectors)
            logger.info("✅ Successfully upserted vectors to Pinecone")
            return True

        except Exception as e:
            logger.error(f"❌ Upsert failed: {e}")
            return False

    def search_similar(self, query_embedding: List[float], top_k: int = 5, include_metadata: bool = True) -> List[Dict[str, Any]]:
        """Search for similar vectors."""
        if not self.index and not self.connect_to_index():
            return []

        try:
            logger.info(f"🔍 Searching for {top_k} similar documents")

            response = self.index.query(
                vector=query_embedding,
                top_k=top_k,
                include_metadata=include_metadata
            )

            results = []
            for match in response["matches"]:
                results.append({
                    "id": match["id"],
                    "score": float(match["score"]),
                    "metadata": match.get("metadata", {})
                })

            logger.info(f"✅ Found {len(results)} similar documents")
            return results

        except Exception as e:
            logger.error(f"❌ Search failed: {e}")
            return []

    def get_index_stats(self) -> Dict[str, Any]:
        """Get index statistics."""
        if not self.index and not self.connect_to_index():
            return {}

        try:
            stats = self.pc.describe_index(self.index_name)
            return {
                "dimension": stats["dimension"],
                "status": stats["status"],
                "host": stats["host"]
            }
        except Exception as e:
            logger.error(f"❌ Failed to get stats: {e}")
            return {}


# === Convenience functions ===
def store_embedded_documents(embedded_docs: List[Dict[str, Any]]) -> bool:
    """Store embedded documents."""
    store = SimplePineconeStore()

    if embedded_docs and embedded_docs[0].get('embedding'):
        dimension = len(embedded_docs[0]['embedding'])
        if not store.create_index_if_not_exists(dimension):
            return False

    return store.upsert_documents(embedded_docs)


def search_documents(query_embedding: List[float], top_k: int = 5) -> List[Dict[str, Any]]:
    """Search documents by embedding."""
    store = SimplePineconeStore()
    return store.search_similar(query_embedding, top_k)


def search_documents_by_text(query: str, top_k: int = 5):
    """Convert query text → embedding → search Pinecone."""
    embedder = EmbeddingGenerator()
    query_embedding = embedder.embed_single_text(query)
    store = SimplePineconeStore()
    return store.search_similar(query_embedding.tolist(), top_k)
