"""
Clean, focused embeddings module for portfolio RAG project.

Features (only what we need):
- Basic embedding generation with sentence-transformers
- Simple file-based caching to avoid re-computation
- Batch processing for multiple documents
- Error handling for robust operation
"""
import logging
import hashlib
import time
from pathlib import Path
from typing import List, Dict, Any, Optional
import numpy as np
from rag.documents import process_document
try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    SentenceTransformer = None

from rag.core.config import get_settings

logger = logging.getLogger(__name__)


class SimpleEmbeddingCache:
    """File-based caching for embeddings."""
    
    def __init__(self):
        settings = get_settings()
        self.cache_dir = settings.data_dir / "embeddings_cache"
        self.cache_dir.mkdir(exist_ok=True)
        logger.info(f"📁 Cache directory: {self.cache_dir}")
    
    def _get_cache_key(self, text: str, model_name: str) -> str:
        """Generate cache key from text + model."""
        content = f"{model_name}:{text}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def get(self, text: str, model_name: str) -> Optional[np.ndarray]:
        """Get embedding from cache if exists."""
        try:
            cache_key = self._get_cache_key(text, model_name)
            cache_file = self.cache_dir / f"{cache_key}.npy"
            
            if cache_file.exists():
                return np.load(cache_file)
            return None
        except Exception as e:
            logger.warning(f"⚠️ Cache read failed: {e}")
            return None
    
    def set(self, text: str, model_name: str, embedding: np.ndarray):
        """Save embedding to cache."""
        try:
            cache_key = self._get_cache_key(text, model_name)
            cache_file = self.cache_dir / f"{cache_key}.npy"
            np.save(cache_file, embedding)
        except Exception as e:
            logger.warning(f"⚠️ Cache save failed: {e}")


class EmbeddingGenerator:
    """Simple, focused embedding generator."""
    
    def __init__(self, model_name: str = None, use_cache: bool = True):
        """Initialize embedder with model name from config."""
        settings = get_settings()
        self.model_name = model_name or getattr(settings, 'embedding_model', 'sentence-transformers/all-MiniLM-L6-v2')
        self.use_cache = use_cache
        
        # Lazy loading
        self.model = None
        self.cache = SimpleEmbeddingCache() if use_cache else None
        
        logger.info(f"🤖 Embedder initialized: {self.model_name} (cache: {use_cache})")
    
    def _load_model(self):
        """Load model when first needed."""
        if self.model is not None:
            return True
        
        if not SentenceTransformer:
            logger.error("❌ sentence-transformers not installed. Run: uv add sentence-transformers")
            return False
        
        try:
            logger.info(f"📥 Loading model: {self.model_name}")
            self.model = SentenceTransformer(self.model_name)
            logger.info("✅ Model loaded successfully")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to load model: {e}")
            return False
    
    def _clean_text(self, text: str) -> str:
        """Basic text cleaning."""
        if not text:
            return ""
        
        # Remove extra whitespace and truncate if too long
        text = " ".join(text.split())
        
        # Reasonable length limit (most models handle ~512 tokens well)
        if len(text) > 2000:
            text = text[:2000] + "..."
        
        return text
    
    def embed_single_text(self, text: str) -> Optional[np.ndarray]:
        """Generate embedding for a single text."""
        clean_text = self._clean_text(text)
        if not clean_text:
            return None
        
        # Check cache first
        if self.cache:
            cached = self.cache.get(clean_text , self.model_name)
            if cached is not None:
                logger.debug(f"📋 Cache hit: {clean_text[:50]}...")
                return cached
        
        # Load model if needed
        if not self._load_model():
            return None
        
        try:
            # Generate embedding
            embedding = self.model.encode([clean_text])[0]
            
            # Cache result
            if self.cache:
                self.cache.set(clean_text, self.model_name, embedding)
            
            logger.debug(f"⚡ Generated embedding: {clean_text[:50]}...")
            return embedding
            
        except Exception as e:
            logger.error(f"❌ Embedding failed: {e}")
            return None
    
    def embed_texts(self, texts: List[str], batch_size: int = 32) -> List[Optional[np.ndarray]]:
        """Generate embeddings for multiple texts with batching."""
        if not texts:
            return []
        
        logger.info(f"🔄 Generating embeddings for {len(texts)} texts")
        start_time = time.time()
        
        embeddings = []
        cache_hits = 0
        
        # Process in batches
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            batch_embeddings, batch_cache_hits = self._process_batch(batch)
            embeddings.extend(batch_embeddings)
            cache_hits += batch_cache_hits
        
        # Log results
        total_time = time.time() - start_time
        successful = sum(1 for e in embeddings if e is not None)
        
        logger.info(f"✅ Completed: {successful}/{len(texts)} embeddings in {total_time:.2f}s")
        if cache_hits > 0:
            logger.info(f"📋 Cache hits: {cache_hits}")
        
        return embeddings
        
    def _process_batch(self, texts: List[str]) -> tuple:
        """Process a batch of texts efficiently."""
        # Clean texts
        clean_texts = [self._clean_text(text) for text in texts]

        # Separate cached from uncached
        embeddings = []
        uncached_texts = []
        uncached_indices = []
        cache_hits = 0

        # Check for empty texts
        empty_count = 0
        for i, clean_text in enumerate(clean_texts):
            if not clean_text:
                embeddings.append(None)
                empty_count += 1
                continue

            # Check cache
            if self.cache:
                cached = self.cache.get(clean_text, self.model_name)
                if cached is not None:
                    embeddings.append(cached)
                    cache_hits += 1
                    continue

            # Needs embedding
            embeddings.append(None)  # Placeholder
            uncached_texts.append(clean_text)
            uncached_indices.append(i)

        # Alert if most texts are empty
        if empty_count > len(clean_texts) * 0.5:
            logger.error(
                f"❌ WARNING: {empty_count}/{len(clean_texts)} chunks are empty!\n"
                f"   Your document has very little extractable text.\n"
                f"   Possible reasons:\n"
                f"   - PDF is scanned/image-based (OCR disabled)\n"
                f"   - Document extraction failed\n"
                f"   - File is corrupted or encrypted"
            )

        # Batch process uncached texts
        if uncached_texts and self._load_model():
            try:
                logger.debug(f"🔄 Encoding {len(uncached_texts)} texts...")
                batch_embeddings = self.model.encode(uncached_texts)

                # Verify embeddings were generated
                if len(batch_embeddings) == 0:
                    logger.error("❌ Model returned 0 embeddings! Model might not be working properly.")
                    return embeddings, cache_hits

                # Update results and cache
                for idx, embedding in zip(uncached_indices, batch_embeddings):
                    embeddings[idx] = embedding

                    if self.cache:
                        self.cache.set(clean_texts[idx], self.model_name, embedding)

            except Exception as e:
                logger.error(
                    f"❌ Batch embedding FAILED: {str(e)}\n"
                    f"   Model: {self.model_name}\n"
                    f"   Texts: {len(uncached_texts)}\n"
                    f"   This usually means:\n"
                    f"   1. Model failed to load or initialize\n"
                    f"   2. GPU/CUDA issue (if using GPU)\n"
                    f"   3. Input texts are incompatible\n"
                    f"   4. Not enough system resources"
                )

        return embeddings, cache_hits
    
    def embed_documents(self, documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Add embeddings to document chunks.
        Main function you'll use with your processed documents.
        """
        logger.info(f"📚 Embedding {len(documents)} document chunks")
        
        # Extract texts
        texts = [doc.get('text', '') for doc in documents]
        
        # Generate embeddings
        embeddings = self.embed_texts(texts)
        
        # Add embeddings to documents
        updated_docs = []
        for doc, embedding in zip(documents, embeddings):
            updated_doc = doc.copy()
            
            if embedding is not None:
                updated_doc['embedding'] = embedding.tolist()  # Convert for JSON
                updated_doc['embedding_model'] = self.model_name
            else:
                updated_doc['embedding'] = None
                logger.warning(f"❌ Failed to embed: {doc.get('id', 'unknown')}")
            
            updated_docs.append(updated_doc)
        
        successful = sum(1 for doc in updated_docs if doc['embedding'] is not None)
        logger.info(f"✅ Successfully embedded {successful}/{len(documents)} documents")
        
        return updated_docs
    


# Simple convenience function - this is what you'll actually use
def embed_document_chunks(document_chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Main function to embed your document chunks.
    Use this in your pipeline.
    """
    embedder = EmbeddingGenerator(use_cache=True)
    return embedder.embed_documents(document_chunks)


if __name__ == "__main__":
  #from rag.documents import process_document

 # Process PDF
  chunks = process_document("data/22365_3_Prompt-Engineering_v7-1.pdf")
  embedded_chunks =    embed_document_chunks(chunks)
  print(embedded_chunks[0].keys())
  print(f"Embedded {len(embedded_chunks)} chunks")
 
# Test function
#def test_embeddings():
#    """Test the embedding functionality."""
#    print("🧪 Testing embeddings...")
#    
#    # Test basic functionality
#    embedder = EmbeddingGenerator()
#    
#    # Test single text
#    test_text = "This is a test document for RAG embeddings."
#    embedding = embedder.embed_single_text(test_text)
#    
#    if embedding is not None:
#        print(f"✅ Single embedding: shape {embedding.shape}")
#    else:
#        print("❌ Single embedding failed")
#        return False
#    
#    # Test multiple texts
#    test_texts = [
#        "First document about machine learning and AI.",
#        "Second document discussing natural language processing.",
#        "Third document about embeddings and vector databases."
#    ]
#    
#    embeddings = embedder.embed_texts(test_texts)
#    successful = sum(1 for e in embeddings if e is not None)
#    print(f"✅ Batch embedding: {successful}/{len(test_texts)} successful")
#    
#    # Test document integration (your main use case)
#    sample_docs = [
#        {'id': 'doc1', 'text': 'Sample document text for testing.'},
#        {'id': 'doc2', 'text': 'Another sample document for embedding.'}
#    ]
#    
#    embedded_docs = embed_document_chunks(sample_docs)
#    doc_success = sum(1 for doc in embedded_docs if doc['embedding'] is not None)
#    print(f"✅ Document embedding: {doc_success}/{len(sample_docs)} successful")
#    
#    # Test caching (run same text twice)
#    print("\n🧪 Testing caching...")
#    start_time = time.time()
#    embedder.embed_single_text(test_text)
#    first_time = time.time() - start_time
#    
#    start_time = time.time()
#    embedder.embed_single_text(test_text)  # Should be cached
#    second_time = time.time() - start_time
#    
#    print(f"✅ First: {first_time:.3f}s, Second: {second_time:.3f}s")
#    print(f"✅ Caching working: {second_time < first_time / 2}")
#    
#    return True
#
#
#if __name__ == "__main__":
#    print("🚀 Testing focused embeddings module...")
#    success = test_embeddings()
#    
#    if success:
#        print("\n🎉 ALL TESTS PASSED!")
#        print("📋 Ready to integrate with your document processing!")
#    else:
#        print("\n❌ Some tests failed")