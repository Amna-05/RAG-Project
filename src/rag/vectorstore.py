"""
Simple Pinecone vector database integration.
Clean, focused, gets the job done.
"""
import logging
from typing import List, Dict, Any, Optional
import time

try:
    from pinecone import Pinecone
    PINECONE_AVAILABLE = True
except ImportError:
    Pinecone = None
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
            raise ImportError("❌ Pinecone not installed. Run: uv add pinecone-client")
        
        if not settings.pinecone_api_key:
            raise ValueError("❌ PINECONE_API_KEY not set in .env file")
        
        if not settings.pinecone_index_name:
            raise ValueError("❌ PINECONE_INDEX_NAME not set in .env file")
        
        # Initialize Pinecone
        self.pc = Pinecone(api_key=settings.pinecone_api_key)
        self.index_name = settings.pinecone_index_name
        self.index = None
        
        logger.info(f"🌲 Initialized Pinecone client for index: {self.index_name}")
    
    def connect_to_index(self) -> bool:
        """Connect to existing Pinecone index."""
        try:
            self.index = self.pc.Index(self.index_name)
            
            # Test connection with stats
            stats = self.index.describe_index_stats()
            total_vectors = stats.total_vector_count
            
            logger.info(f"✅ Connected to index: {self.index_name}")
            logger.info(f"📊 Current vectors in index: {total_vectors}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to connect to index {self.index_name}: {e}")
            return False
    
    def create_index_if_not_exists(self, dimension: int = 384) -> bool:
        """Create index if it doesn't exist."""
        try:
            # Check if index exists
            existing_indexes = [index.name for index in self.pc.list_indexes()]
            
            if self.index_name in existing_indexes:
                logger.info(f"📍 Index {self.index_name} already exists")
                return self.connect_to_index()
            
            # Create new index
            logger.info(f"🏗️ Creating index: {self.index_name}")
            
            self.pc.create_index(
                name=self.index_name,
                dimension=dimension,
                metric="cosine",  # Good for text embeddings
                spec={
                    "serverless": {
                        "cloud": "aws",
                        "region": "us-east-1"
                    }
                }
            )
            
            # Wait for index to be ready
            logger.info("⏳ Waiting for index to be ready...")
            while not self.pc.describe_index(self.index_name).status['ready']:
                time.sleep(1)
            
            logger.info(f"✅ Index {self.index_name} created successfully")
            return self.connect_to_index()
            
        except Exception as e:
            logger.error(f"❌ Failed to create index: {e}")
            return False
    
    def upsert_documents(self, embedded_docs: List[Dict[str, Any]]) -> bool:
        """
        Upload embedded documents to Pinecone.
        Main function you'll use.
        """
        if not self.index:
            if not self.connect_to_index():
                logger.error("❌ No index connection")
                return False
        
        if not embedded_docs:
            logger.warning("⚠️ No documents to upsert")
            return True
        
        logger.info(f"📤 Upserting {len(embedded_docs)} documents to Pinecone")
        
        try:
            # Prepare vectors for Pinecone
            vectors = []
            for doc in embedded_docs:
                if doc.get('embedding') is None:
                    logger.warning(f"⚠️ Skipping document without embedding: {doc.get('id')}")
                    continue
                
                # Pinecone format: (id, vector, metadata)
                vector_data = {
                    'id': str(doc.get('id', f"doc_{len(vectors)}")),
                    'values': doc['embedding'],
                    'metadata': {
                        'text': doc.get('text', ''),
                        'source': doc.get('source', ''),
                        'file_name': doc.get('file_name', ''),
                        'chunk_index': doc.get('chunk_index', 0)
                    }
                }
                vectors.append(vector_data)
            
            if not vectors:
                logger.error("❌ No valid vectors to upsert")
                return False
            
            # Batch upsert (Pinecone handles batching internally)
            response = self.index.upsert(vectors=vectors)
            
            logger.info(f"✅ Successfully upserted {response.upserted_count} vectors")
            return True
            
        except Exception as e:
            logger.error(f"❌ Upsert failed: {e}")
            return False
    
    def search_similar(
        self, 
        query_embedding: List[float], 
        top_k: int = 5,
        include_metadata: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Search for similar vectors.
        Returns documents most similar to query.
        """
        if not self.index:
            if not self.connect_to_index():
                return []
        
        try:
            logger.info(f"🔍 Searching for {top_k} similar documents")
            
            response = self.index.query(
                vector=query_embedding,
                top_k=top_k,
                include_metadata=include_metadata,
                include_values=False  # Don't return the vectors (saves bandwidth)
            )
            
            # Convert to simple format
            results = []
            for match in response.matches:
                result = {
                    'id': match.id,
                    'score': float(match.score),
                    'metadata': match.metadata or {}
                }
                results.append(result)
            
            logger.info(f"✅ Found {len(results)} similar documents")
            return results
            
        except Exception as e:
            logger.error(f"❌ Search failed: {e}")
            return []
    
    def get_index_stats(self) -> Dict[str, Any]:
        """Get index statistics."""
        if not self.index:
            if not self.connect_to_index():
                return {}
        
        try:
            stats = self.index.describe_index_stats()
            return {
                'total_vectors': stats.total_vector_count,
                'dimension': stats.dimension,
                'index_fullness': stats.index_fullness
            }
        except Exception as e:
            logger.error(f"❌ Failed to get stats: {e}")
            return {}


# Convenience functions - what you'll actually use
def store_embedded_documents(embedded_docs: List[Dict[str, Any]]) -> bool:
    """
    Simple function to store your embedded documents.
    Use this in your pipeline.
    """
    store = SimplePineconeStore()
    
    # Get embedding dimension from first document
    if embedded_docs and embedded_docs[0].get('embedding'):
        dimension = len(embedded_docs[0]['embedding'])
        
        # Create index if needed
        if not store.create_index_if_not_exists(dimension):
            return False
    
    # Store documents
    return store.upsert_documents(embedded_docs)


def search_documents(query_embedding: List[float], top_k: int = 5) -> List[Dict[str, Any]]:
    """
    Simple function to search documents.
    Use this for retrieval.
    """
    store = SimplePineconeStore()
    return store.search_similar(query_embedding, top_k)

def search_documents_by_text(query: str, top_k: int = 5):
    # Step 1: Convert user's question to embedding
    embedder = EmbeddingGenerator()
    query_embedding = embedder.embed_single_text(query)  # "What is RAG?" → [0.1, -0.3, 0.8, ...]
    
    # Step 2: Search Pinecone with that embedding
    store = SimplePineconeStore()
    return store.search_similar(query_embedding.tolist(), top_k)


# Test function
#def test_pinecone():
#    """Test Pinecone integration."""
#    print("🧪 Testing Pinecone integration...")
#    
#    try:
#        # Test connection
#        store = SimplePineconeStore()
#        
#        # Test with sample embedded documents
#        sample_docs = [
#            {
#                'id': 'test_doc_1',
#                'text': 'This is a test document about machine learning.',
#                'embedding': [0.1] * 384,  # Fake embedding for testing
#                'source': 'test.pdf'
#            },
#            {
#                'id': 'test_doc_2', 
#                'text': 'Another test document about AI systems.',
#                'embedding': [0.2] * 384,  # Fake embedding for testing
#                'source': 'test.pdf'
#            }
#        ]
#        
#        # Test storage
#        print("📤 Testing document storage...")
#        success = store_embedded_documents(sample_docs)
#        
#        if not success:
#            print("❌ Storage test failed")
#            return False
#        
#        # Test search
#        print("🔍 Testing document search...")
#        query_embedding = [0.15] * 384  # Fake query embedding
#        results = search_documents(query_embedding, top_k=2)
#        
#        if results:
#            print(f"✅ Search returned {len(results)} results")
#            for result in results:
#                print(f"  - ID: {result['id']}, Score: {result['score']:.3f}")
#        else:
#            print("❌ Search returned no results")
#            return False
#        
#        # Test stats
#        stats = store.get_index_stats()
#        if stats:
#            print(f"📊 Index stats: {stats}")
#        
#        print("🎉 All Pinecone tests passed!")
#        return True
#        
#    except Exception as e:
#        print(f"❌ Pinecone test failed: {e}")
#        return False
#
#
#if __name__ == "__main__":
#    test_pinecone()
#    search_documents([0.1] * 384, top_k=3)