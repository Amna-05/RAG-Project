"""Test script to check what's in Pinecone."""
import asyncio
from rag.core.config import get_settings
from rag.vectorstore import SimplePineconeStore

async def check_pinecone():
    settings = get_settings()
    store = SimplePineconeStore()
    
    if store.connect_to_index():
        print("✅ Connected to Pinecone")
        
        # Get stats
        stats = store.get_index_stats()
        print(f"📊 Stats: {stats}")
        
        # List namespaces
        if 'namespaces' in stats:
            print(f"📁 Namespaces: {list(stats['namespaces'].keys())}")
            for ns, info in stats['namespaces'].items():
                print(f"   - {ns}: {info.get('vector_count', 0)} vectors")
    else:
        print("❌ Failed to connect")

if __name__ == "__main__":
    asyncio.run(check_pinecone())