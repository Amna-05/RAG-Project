"""
Complete RAG system with Gemini LLM integration.
The final piece - generates answers using retrieved context!
"""
import logging
from typing import List, Dict, Any, Optional

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    genai = None
    GEMINI_AVAILABLE = False

from rag.core.config import get_settings
from rag.vectorstore import search_documents_by_text

logger = logging.getLogger(__name__)


class RAGWithGemini:
    """Complete RAG system with Gemini for final response generation."""
    
    def __init__(self):
        """Initialize Gemini client."""
        settings = get_settings()
        
        if not GEMINI_AVAILABLE:
            raise ImportError("❌ google-generativeai not installed. Run: uv add google-generativeai")
        
        if not settings.google_api_key:
            raise ValueError("❌ GOOGLE_API_KEY not set in .env file")
        
        # Configure Gemini
        genai.configure(api_key=settings.google_api_key)
        self.model = genai.GenerativeModel(settings.gemini_model)
        
        logger.info("🤖 Initialized Gemini LLM for RAG")
    
    def format_context(self, search_results: List[Dict[str, Any]]) -> str:
        """Format retrieved documents into context for LLM."""
        if not search_results:
            return "No relevant information found in the knowledge base."
        
        context_parts = []
        for i, result in enumerate(search_results, 1):
            text = result['metadata'].get('text', '')
            source = result['metadata'].get('source', 'Unknown')
            score = result.get('score', 0)
            
            # Format each piece of context
            context_part = f"""
Context {i} (Relevance: {score:.2f}, Source: {source}):
{text}
"""
            context_parts.append(context_part)
        
        return "\n".join(context_parts)
    
    def create_rag_prompt(self, question: str, context: str) -> str:
        """Create a well-structured prompt for RAG."""
        return f"""You are a helpful AI assistant that answers questions based on the provided context.

CONTEXT:
{context}

QUESTION: {question}

INSTRUCTIONS:
1. Answer the question using ONLY the information provided in the context above
2. If the context doesn't contain enough information to answer the question, say so
3. Be specific and cite relevant parts of the context when possible
4. Keep your answer concise but complete
5. If you mention information from the context, briefly indicate which context source it came from

ANSWER:"""

    def generate_response(self, question: str, context: str) -> str:
        """Generate response using Gemini."""
        try:
            prompt = self.create_rag_prompt(question, context)
            
            logger.info(f"🧠 Generating response for: {question}...")
            
            # Generate response
            response = self.model.generate_content(prompt)
            
            if response.text:
                logger.info("✅ Response generated successfully")
                return response.text.strip()
            else:
                logger.error("❌ Empty response from Gemini")
                return "I apologize, but I couldn't generate a response. Please try rephrasing your question."
                
        except Exception as e:
            logger.error(f"❌ Response generation failed: {e}")
            return f"I apologize, but I encountered an error while generating the response: {str(e)}"
    
    def query(self, question: str, top_k: int = 5) -> Dict[str, Any]:
        """
        Complete RAG pipeline: retrieve documents + generate response.
        This is your main function!
        """
        logger.info(f"🔍 Processing RAG query: {question}")
        
        # Step 1: Retrieve relevant documents
        search_results = search_documents_by_text(question, top_k=top_k,)
        
        if not search_results:
            return {
                'question': question,
                'answer': "I couldn't find any relevant information in the knowledge base to answer your question.",
                'sources': [],
                'context_used': ""
            }
        
        # Step 2: Format context
        context = self.format_context(search_results)
        
        # Step 3: Generate response
        answer = self.generate_response(question, context)
        
        # Step 4: Prepare response
        sources = []
        for result in search_results:
            sources.append({
                'source': result['metadata'].get('source', 'Unknown'),
                'relevance_score': result.get('score', 0),
                'text_preview': result['metadata'].get('text', '')[:200] + "..."
            })
        
        return {
            'question': question,
            'answer': answer,
            'sources': sources,
            'context_used': context,
            'num_sources_used': len(search_results)
        }


# Simple convenience function - your main interface
def ask_question(question: str, top_k: int = 5) -> str:
    """
    Ask a question and get an AI-generated answer based on your documents.
    
    This is the main function you'll use!
    """
    rag = RAGWithGemini()
    result = rag.query(question, top_k)
    return result['answer']

def generate_answer_with_gemini(prompt: str) -> str:
    """
    Simple wrapper to generate answer using Gemini.
    
    Args:
        prompt: The prompt with context and question
        
    Returns:
        Generated answer as string
    """
    settings = get_settings()
    
    try:
        import google.generativeai as genai
        
        genai.configure(api_key=settings.google_api_key)
        model = genai.GenerativeModel(settings.gemini_model)
        
        response = model.generate_content(prompt)
        
        return response.text
        
    except Exception as e:
        logger.error(f"Gemini generation failed: {e}")
        return f"I apologize, but I encountered an error generating a response: {str(e)}"
def ask_question_detailed(
                question: str,
                 top_k: int = 5,
                 namespace: Optional[str] = None,  
                 user_id: Optional[str] = None
                 ) -> Dict[str, Any]:
    """
    Ask a question and get detailed results including sources.
    Use this when you want to see what documents were used.
    """
    rag = RAGWithGemini()
    results = search_documents_by_text(
        question, 
        top_k=top_k,
        namespace=namespace,  
        user_id=user_id       
    )
    return rag.query(question, top_k)


# Test function
def test_rag_complete():
    """Test the complete RAG system."""
    print("🚀 Testing complete RAG system...")
    
    try:
        # Test simple question answering
        print("\n1️⃣ Testing simple Q&A...")
        question1 = "What is prompt engineering?"
        answer1 = ask_question(question1)
        
        print(f"Question: {question1}")
        print(f"Answer: {answer1}")
        
        # Test detailed results
        print("\n2️⃣ Testing detailed results...")
        question2 = "What are the main techniques used in RAG systems?"
        detailed_result = ask_question_detailed(question2)
        
        print(f"Question: {detailed_result['question']}")
        print(f"Answer: {detailed_result['answer']}")
        print(f"Sources used: {detailed_result['num_sources_used']}")
        
        for i, source in enumerate(detailed_result['sources'], 1):
            print(f"  Source {i}: {source['source']} (Score: {source['relevance_score']:.3f})")
            print(f"    Preview: {source['text_preview']}")
        
        # Test edge case
        print("\n3️⃣ Testing unknown topic...")
        question3 = "What is the capital of Mars?"
        answer3 = ask_question(question3)
        
        print(f"Question: {question3}")
        print(f"Answer: {answer3}")
        
        print("\n🎉 RAG system testing complete!")
        return True
        
    except Exception as e:
        print(f"❌ RAG test failed: {e}")
        return False


# Complete pipeline demo
def demo_complete_pipeline():
    """Demo the entire RAG pipeline from documents to answers."""
    print("🎬 Complete RAG Pipeline Demo")
    print("=" * 50)
    
    # This assumes you've already processed and stored documents
    # If not, uncomment the lines below:
    
    # from rag.documents import process_document
    # from rag.embeddings import embed_document_chunks  
    # from rag.vectorstore import store_embedded_documents
    
    # print("📄 Processing document...")
    # chunks = process_document("data/22365_3_Prompt Engineering_v7 (1).pdf")
    # embedded_chunks = embed_document_chunks(chunks)
    # store_embedded_documents(embedded_chunks)
    
    print("🤖 Starting Q&A session...")
    
    # Sample questions
    questions = [
        "What is prompt engineering?",
        "How do you improve AI model responses?", 
        "What are the main challenges in prompt design?",
        "Can you explain retrieval augmented generation?"
    ]
    
    for i, question in enumerate(questions, 1):
        print(f"\n{'='*20} Question {i} {'='*20}")
        print(f"Q: {question}")
        
        try:
            result = ask_question_detailed(question, top_k=3)
            print(f"A: {result['answer']}")
            print(f"📚 Sources: {result['num_sources_used']} documents used")
            
        except Exception as e:
            print(f"❌ Error: {e}")
    
    print(f"\n{'='*50}")
    print("🎉 Demo complete! Your RAG system is working!")


if __name__ == "__main__":
    print("🧪 Testing RAG + LLM integration...")
    
    # Test the system
    success = test_rag_complete()
    
    if success:
        print("\n" + "="*50)
        print("🎉 SUCCESS! Your RAG system is ready!")
        print("="*50)
        print("\n📖 How to use:")
        print('answer = ask_question("Your question here")')
        print('detailed = ask_question_detailed("Your question here")')
    else:
        print("❌ Some tests failed - check the logs above")