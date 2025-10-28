"""
Simple Pinecone vector database integration with user isolation.
Clean, focused, gets the job done.
"""
import logging
from typing import List, Dict, Any, Optional
import time

try:
    from pinecone import Pinecone, ServerlessSpec
    PINECONE_AVAILABLE = True
except ImportError:
    Pinecone = None
    ServerlessSpec = None
    PINECONE_AVAILABLE = False

from rag.core.config import get_settings
from rag.embeddings import EmbeddingGenerator

logger = logging.getLogger(__name__)


class SimplePineconeStore:
    """Simple Pinecone vector database client with user isolation."""

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
        self.use_namespaces = settings.pinecone_use_namespaces
        self.index = None

        logger.info(f"🌲 Initialized Pinecone client for index: {self.index_name}")
        logger.info(f"🔐 User namespaces: {'enabled' if self.use_namespaces else 'disabled'}")

    def connect_to_index(self) -> bool:
        """Connect to existing Pinecone index."""
        try:
            self.index = self.pc.Index(self.index_name)

            # Test connection
            stats = self.pc.describe_index(self.index_name)
            dimension = stats.get("dimension", "unknown")
            logger.info(f"✅ Connected to index: {self.index_name}")
            logger.info(f"📊 Index dimension: {dimension}")
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

    def upsert_documents(
        self, 
        embedded_docs: List[Dict[str, Any]],
        namespace: Optional[str] = None
    ) -> bool:
        """Upload embedded documents to Pinecone with optional namespace."""
        if not self.index and not self.connect_to_index():
            logger.error("❌ No index connection")
            return False

        if not embedded_docs:
            logger.warning("⚠️ No documents to upsert")
            return True

        effective_namespace = namespace if self.use_namespaces else None
        
        logger.info(
            f"📤 Upserting {len(embedded_docs)} documents "
            f"(namespace: {effective_namespace or 'default'})"
        )

        try:
            vectors = []
            for doc in embedded_docs:
                if doc.get('embedding') is None:
                    logger.warning(f"⚠️ Skipping document without embedding: {doc.get('id')}")
                    continue

                metadata = doc.get('metadata', {})
                
                # Ensure critical fields are in metadata
                metadata.update({
                    'text': doc.get('text', '')[:1000],  # Pinecone metadata limit
                    'source': doc.get('source', ''),
                    'file_name': doc.get('file_name', ''),
                    'chunk_index': doc.get('chunk_index', 0),
                    'user_id': metadata.get('user_id', ''),
                    'document_id': metadata.get('document_id', '')
                })

                vectors.append({
                    'id': str(doc.get('id', f"doc_{len(vectors)}")),
                    'values': doc['embedding'],
                    'metadata': metadata
                })

            if not vectors:
                logger.error("❌ No valid vectors to upsert")
                return False

            self.index.upsert(
                vectors=vectors,
                namespace=effective_namespace or ""
            )
            
            logger.info(f"✅ Successfully upserted {len(vectors)} vectors")
            return True

        except Exception as e:
            logger.error(f"❌ Upsert failed: {e}")
            return False

    def search_similar(
        self, 
        query_embedding: List[float], 
        top_k: int = 5,
        namespace: Optional[str] = None,
        filter_dict: Optional[Dict[str, Any]] = None,
        include_metadata: bool = True
    ) -> List[Dict[str, Any]]:
        """Search for similar vectors with optional filtering."""
        if not self.index and not self.connect_to_index():
            return []

        try:
            effective_namespace = namespace if self.use_namespaces else None
            
            logger.info(
                f"🔍 Searching for {top_k} similar documents "
                f"(namespace: {effective_namespace or 'default'}, "
                f"filter: {filter_dict or 'none'})"
            )

            query_params = {
                "vector": query_embedding,
                "top_k": top_k,
                "include_metadata": include_metadata,
                "namespace": effective_namespace or ""
            }
            
            if filter_dict:
                query_params["filter"] = filter_dict

            response = self.index.query(**query_params)

            results = []
            for match in response.get("matches", []):
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

    def delete_by_filter(
        self,
        filter_dict: Dict[str, Any],
        namespace: Optional[str] = None
    ) -> bool:
        """Delete vectors matching filter criteria."""
        if not self.index and not self.connect_to_index():
            return False

        try:
            effective_namespace = namespace if self.use_namespaces else None
            
            logger.info(f"🗑️ Deleting vectors with filter: {filter_dict}")
            
            self.index.delete(
                filter=filter_dict,
                namespace=effective_namespace or ""
            )
            
            logger.info("✅ Vectors deleted successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Delete failed: {e}")
            return False


# === Updated convenience functions ===

def store_embedded_documents(
    embedded_docs: List[Dict[str, Any]],
    namespace: Optional[str] = None
) -> bool:
    """Store embedded documents with optional namespace."""
    store = SimplePineconeStore()

    if embedded_docs and embedded_docs[0].get('embedding'):
        dimension = len(embedded_docs[0]['embedding'])
        if not store.create_index_if_not_exists(dimension):
            return False

    return store.upsert_documents(embedded_docs, namespace=namespace)


def search_documents(
    query_embedding: List[float],
    top_k: int = 5,
    namespace: Optional[str] = None,
    user_id: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Search documents with optional user filtering."""
    store = SimplePineconeStore()
    
    filter_dict = None
    if user_id and not store.use_namespaces:
        filter_dict = {"user_id": user_id}
    
    return store.search_similar(
        query_embedding,
        top_k=top_k,
        namespace=namespace,
        filter_dict=filter_dict
    )


def search_documents_by_text(
    query: str,
    top_k: int = 5,
    namespace: Optional[str] = None,
    user_id: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Convert query text → embedding → search."""
    embedder = EmbeddingGenerator()
    query_embedding = embedder.embed_single_text(query)
    
    return search_documents(
        query_embedding.tolist(),
        top_k=top_k,
        namespace=namespace,
        user_id=user_id
    )


def delete_document(
    document_id: str,
    namespace: Optional[str] = None
) -> bool:
    """Delete all chunks of a document."""
    store = SimplePineconeStore()
    return store.delete_by_filter(
        filter_dict={"document_id": document_id},
        namespace=namespace
    )