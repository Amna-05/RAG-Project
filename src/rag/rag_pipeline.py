"""
Interactive RAG Pipeline
Complete end-to-end pipeline with user-friendly CLI interface.
"""
import logging
import sys
from pathlib import Path
from typing import Optional

# Import all your RAG components
from rag.documents import process_document
from rag.embeddings import embed_document_chunks
from rag.vectorstore import store_embedded_documents
from rag.llm_integration import ask_question, ask_question_detailed

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s: %(message)s'
)
logger = logging.getLogger(__name__)


def process_new_document(file_path: str) -> bool:
    """
    Complete document ingestion pipeline.
    Process document -> Generate embeddings -> Store in vector database
    """
    print(f"\n📄 Processing new document: {file_path}")
    
    # Step 1: Check if file exists
    doc_path = Path(file_path)
    if not doc_path.exists():
        print(f"❌ File not found: {file_path}")
        return False
    
    try:
        # Step 2: Process document into chunks
        print("🔨 Breaking document into chunks...")
        chunks = process_document(doc_path)
        
        if not chunks:
            print("❌ No chunks created from document")
            return False
        
        print(f"✅ Created {len(chunks)} chunks")
        
        # Step 3: Generate embeddings
        print("🔢 Generating embeddings...")
        embedded_chunks = embed_document_chunks(chunks)
        
        successful_embeddings = sum(1 for chunk in embedded_chunks if chunk.get('embedding') is not None)
        print(f"✅ Generated embeddings for {successful_embeddings}/{len(embedded_chunks)} chunks")
        
        # Step 4: Store in vector database
        print("📤 Storing in vector database...")
        success = store_embedded_documents(embedded_chunks)
        
        if success:
            print("✅ Document successfully ingested into RAG system!")
            return True  
        else:
            print("❌ Failed to store in vector database")
            return False
            
    except Exception as e:
        print(f"❌ Pipeline failed: {e}")
        logger.error(f"Document processing failed: {e}")
        return False


def query_interface():
    """
    Interactive query interface for the RAG system.
    """
    print("\n🤖 RAG Query Interface")
    print("="*50)
    
    while True:
        try:
            # Get user query
            print("\n💬 Enter your question (or 'quit'/'exit' to stop):")
            query = input("❓ ").strip()
            
            if not query:
                print("⚠️ Please enter a question")
                continue
                
            if query.lower() in ['quit', 'exit', 'q']:
                print("👋 Goodbye!")
                break
            
            # Choose response type
            print("\n🔧 Choose response type:")
            print("1. Simple answer (ask_question)")
            print("2. Detailed with sources (ask_question_detailed)")
            
            choice = input("Enter choice (1 or 2): ").strip()
            
            if choice == '1':
                print("\n🔍 Searching and generating simple answer...")
                try:
                    answer = ask_question(query)
                    print(f"\n🤖 Answer:")
                    print("-" * 40)
                    print(answer)
                    print("-" * 40)
                except Exception as e:
                    print(f"❌ Error generating answer: {e}")
                    
            elif choice == '2':
                print("\n🔍 Searching and generating detailed answer...")
                try:
                    result = ask_question_detailed(query)
                    
                    print(f"\n🤖 Detailed Answer:")
                    print("=" * 50)
                    print(f"Question: {result['question']}")
                    print(f"\nAnswer: {result['answer']}")
                    print(f"\nSources Used: {result['num_sources_used']}")
                    
                    print(f"\n📚 Source Details:")
                    for i, source in enumerate(result['sources'], 1):
                        print(f"\n  Source {i}:")
                        print(f"    File: {source['source']}")
                        print(f"    Relevance: {source['relevance_score']:.3f}")
                        print(f"    Preview: {source['text_preview'][:150]}...")
                    
                    print("=" * 50)
                    
                except Exception as e:
                    print(f"❌ Error generating detailed answer: {e}")
            else:
                print("⚠️ Invalid choice. Please enter 1 or 2")
                
        except KeyboardInterrupt:
            print("\n\n👋 Interrupted by user. Goodbye!")
            break
        except Exception as e:
            print(f"❌ Unexpected error: {e}")


def main():
    """
    Main pipeline interface.
    """
    print("🚀 RAG Pipeline Interface")
    print("=" * 50)
    print("Choose an option:")
    print("1. Process new document (full pipeline)")
    print("2. Query existing knowledge base")
    print("3. Exit")
    
    while True:
        try:
            choice = input("\nEnter your choice (1, 2, or 3): ").strip()
            
            if choice == '1':
                print("\n📂 Document Processing Mode")
                file_path = input("Enter file path: ").strip()
                
                if not file_path:
                    print("⚠️ Please provide a file path")
                    continue
                
                success = process_new_document(file_path)
                
                if success:
                    # Ask if user wants to query the new document
                    query_now = input("\n❓ Would you like to query the document now? (y/n): ").lower()
                    if query_now in ['y', 'yes']:
                        query_interface()
                
            elif choice == '2':
                query_interface()
                
            elif choice == '3':
                print("👋 Goodbye!")
                sys.exit(0)
                
            else:
                print("⚠️ Invalid choice. Please enter 1, 2, or 3")
                
        except KeyboardInterrupt:
            print("\n\n👋 Interrupted by user. Goodbye!")
            sys.exit(0)
        except Exception as e:
            print(f"❌ Unexpected error: {e}")


def quick_demo():
    """
    Quick demo function for testing.
    """
    print("🎬 Quick RAG Demo")
    print("=" * 30)
    
    # Test queries
    demo_queries = [
        "What is prompt engineering?",
        "What are the main prompting techniques?",
        "How do you optimize prompts?"
    ]
    
    print("Running demo queries...")
    
    for i, query in enumerate(demo_queries, 1):
        print(f"\n{i}. Query: {query}")
        try:
            answer = ask_question(query)
            print(f"   Answer: {answer[:200]}...")
        except Exception as e:
            print(f"   Error: {e}")


if __name__ == "__main__":
    # Check if running in demo mode
    if len(sys.argv) > 1 and sys.argv[1] == 'demo':
        quick_demo()
    else:
        main()