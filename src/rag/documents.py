"""Production-ready document processing functions.

Supports multiple file formats with proper error handling and configuration.
Uses functional programming patterns for better testability.
"""
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Union
import json

# Core dependencies only - no heavy frameworks
try:
    import PyPDF2
except ImportError:
    PyPDF2 = None

try:
    from docx import Document as DocxDocument
except ImportError:
    DocxDocument = None

from rag.config import get_settings

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def read_text_file(file_path: Path) -> Optional[str]:
    """Read a text file safely."""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        logger.info(f"✅ Read text file: {file_path.name} ({len(content)} chars)")
        return content
    except Exception as e:
        logger.error(f"❌ Failed to read text file {file_path}: {e}")
        return None


def read_pdf_file(file_path: Path) -> Optional[str]:
    """Read PDF file using PyPDF2 (lightweight alternative to LangChain)."""
    if not PyPDF2:
        logger.error("❌ PyPDF2 not installed. Run: uv add PyPDF2")
        return None
    
    try:
        content = ""
        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            
            for page_num, page in enumerate(pdf_reader.pages):
                try:
                     page_text = page.extract_text()
                     content += page_text + "\n\n"  # Remove the "--- Page X ---" markers
                except Exception as page_error:
                    logger.warning(f"⚠️ Failed to read page {page_num + 1}: {page_error}")
                    continue
        
        logger.info(f"✅ Read PDF: {file_path.name} ({len(pdf_reader.pages)} pages, {len(content)} chars)")
        return content
        
    except Exception as e:
        logger.error(f"❌ Failed to read PDF {file_path}: {e}")
        return None


def read_docx_file(file_path: Path) -> Optional[str]:
    """Read DOCX file."""
    if not DocxDocument:
        logger.error("❌ python-docx not installed. Run: uv add python-docx")
        return None
    
    try:
        doc = DocxDocument(file_path)
        content = "\n".join([paragraph.text for paragraph in doc.paragraphs])
        logger.info(f"✅ Read DOCX: {file_path.name} ({len(content)} chars)")
        return content
    except Exception as e:
        logger.error(f"❌ Failed to read DOCX {file_path}: {e}")
        return None


def read_json_file(file_path: Path) -> Optional[str]:
    """Read JSON file and convert to text."""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
        
        # Convert JSON to readable text
        if isinstance(data, dict):
            content = json.dumps(data, indent=2)
        elif isinstance(data, list):
            content = "\n".join([json.dumps(item, indent=2) for item in data])
        else:
            content = str(data)
        
        logger.info(f"✅ Read JSON: {file_path.name} ({len(content)} chars)")
        return content
    except Exception as e:
        logger.error(f"❌ Failed to read JSON {file_path}: {e}")
        return None


def read_document(file_path: Union[str, Path]) -> Optional[Dict[str, Any]]:
    """
    Read any supported document type and return structured data.
    
    Returns:
        Dict with 'content', 'source', 'file_type', 'metadata'
    """
    file_path = Path(file_path)
    
    if not file_path.exists():
        logger.error(f"❌ File not found: {file_path}")
        return None
    
    # Determine file type and read accordingly
    suffix = file_path.suffix.lower()
    content = None
    
    if suffix == '.pdf':
        content = read_pdf_file(file_path)
        file_type = 'pdf'
    elif suffix == '.docx':
        content = read_docx_file(file_path)
        file_type = 'docx'
    elif suffix == '.txt':
        content = read_text_file(file_path)
        file_type = 'text'
    elif suffix == '.json':
        content = read_json_file(file_path)
        file_type = 'json'
    else:
        # Try as text file
        content = read_text_file(file_path)
        file_type = 'text'
    
    if content is None:
        return None
    
    return {
        'content': content,
        'source': str(file_path),
        'file_name': file_path.name,
        'file_type': file_type,
        'metadata': {
            'source': str(file_path),
            'file_type': file_type,
            'char_count': len(content)
        }
    }


def recursive_text_chunker(
    text: str, 
    chunk_size: int = 1000, 
    overlap: int = 200,
    separators: List[str] = None
) -> List[str]:
    """
    Advanced chunking similar to LangChain's RecursiveCharacterTextSplitter.
    Tries to split on different separators in order of preference.
    """
    if separators is None:
        separators = ["\n\n", "\n", ". ", " ", ""]
    
    if len(text) <= chunk_size:
        return [text]
    
    chunks = []
    
    # Try each separator in order
    for separator in separators:
        if separator in text:
            parts = text.split(separator)
            current_chunk = ""
            
            for part in parts:
                # If adding this part would exceed chunk size
                if len(current_chunk) + len(part) + len(separator) > chunk_size:
                    if current_chunk:
                        chunks.append(current_chunk.strip())
                        # Handle overlap
                        if overlap > 0 and len(current_chunk) > overlap:
                            current_chunk = current_chunk[-overlap:] + separator + part
                        else:
                            current_chunk = part
                    else:
                        # Part itself is too large, recursively split it
                        if len(part) > chunk_size:
                            sub_chunks = recursive_text_chunker(
                                part, chunk_size, overlap, separators[1:]
                            )
                            chunks.extend(sub_chunks)
                            current_chunk = ""
                        else:
                            current_chunk = part
                else:
                    if current_chunk:
                        current_chunk += separator + part
                    else:
                        current_chunk = part
            
            # Add the last chunk
            if current_chunk.strip():
                chunks.append(current_chunk.strip())
            
            return [chunk for chunk in chunks if chunk.strip()]
    
    # Fallback: split by character count
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        chunks.append(chunk)
        start = end - overlap
    
    return chunks


def create_document_chunks(document_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Create chunks from document data using configurable settings.
    """
    settings = get_settings()
    
    content = document_data['content']
    chunks = recursive_text_chunker(
        content,
        chunk_size=settings.chunk_size,
        overlap=settings.chunk_overlap
    )
    
    # Create structured chunk objects
    chunk_objects = []
    for i, chunk_text in enumerate(chunks):
        chunk_obj = {
            'id': f"{document_data['file_name']}_{i}",
            'text': chunk_text,
            'chunk_index': i,
            'source': document_data['source'],
            'file_name': document_data['file_name'],
            'file_type': document_data['file_type'],
            'char_count': len(chunk_text),
            'metadata': {
                **document_data['metadata'],
                'chunk_index': i,
                'total_chunks': len(chunks)
            }
        }
        chunk_objects.append(chunk_obj)
    
    logger.info(f"✅ Created {len(chunk_objects)} chunks from {document_data['file_name']}")
    return chunk_objects


def process_document(file_path: Union[str, Path]) -> List[Dict[str, Any]]:
    """
    Complete pipeline: read document -> create chunks.
    This replaces your original workflow.
    """
    # Read document
    document_data = read_document(file_path)
    if not document_data:
        logger.error(f"❌ Failed to process document: {file_path}")
        return []
    
    # Create chunks
    chunks = create_document_chunks(document_data)
    return chunks



#
if __name__ == "__main__":
    response =read_pdf_file(Path("data/22365_3_Prompt-Engineering_v7-1.pdf"))
    #print(response)
    print("🚀 Testing document processing...")
    test_file = Path("data/22365_3_Prompt-Engineering_v7-1.pdf")
    chunks = process_document(test_file)
    if chunks:
        print(f"✅ Successfully processed: {len(chunks)} chunks")
        print(f"✅ First chunk preview: {chunks[3]['text'][100:500]}...")
        print(f"✅ Metadata: {chunks[0]['metadata']}")
    else:
        print("❌ Document processing failed")
#
# Test functions
#def test_pdf_processing():
#    """Test PDF processing with your specific file."""
#    test_file = Path("data/22365_3_Prompt-Engineering_v7-1.pdf")
#    
#    if not test_file.exists():
#        print(f"⚠️ Test file not found: {test_file}")
#        print("Creating sample PDF test...")
#        return test_sample_pdf()
#    
#    print(f"📄 Testing PDF processing with: {test_file}")
#    chunks = process_document(test_file)
#    
#    if chunks:
#        print(f"✅ Successfully processed PDF: {len(chunks)} chunks")
#        print(f"✅ First chunk preview: {chunks[0]['text'][:150]}...")
#        print(f"✅ Metadata: {chunks[0]['metadata']}")
#        return True
#    else:
#        print("❌ PDF processing failed")
#        return False
#
#
#def test_sample_pdf():
#    """Test with a simple text file if PDF not available."""
#    from rag.config import get_settings
#    settings = get_settings()
#    
#    # Create sample text file
#    sample_file = settings.data_dir / "sample_document.txt"
#    sample_content = """
#    This is a comprehensive test document for our RAG system.
#    
#    Section 1: Introduction
#    Retrieval-Augmented Generation (RAG) combines the power of large language #models 
#    with external knowledge bases to provide more accurate and contextual responses.
#    
#    Section 2: Components
#    The main components of a RAG system include:
#    1. Document processing and chunking
#    2. Embedding generation for semantic search
#    3. Vector database for efficient storage and retrieval
#    4. Query processing and similarity matching
#    5. Context-aware response generation
#    
#    Section 3: Benefits
#    RAG systems offer several advantages over traditional approaches:
#    - Up-to-date information from external sources
#    - Reduced hallucination in AI responses
#    - Ability to cite sources and provide references
#    - Scalable knowledge base that can be updated independently
#    
#    This document will be processed into multiple chunks for testing purposes.
#    Each chunk should maintain context while being appropriately sized for #embedding.
#    """
#    
#    with open(sample_file, 'w', encoding='utf-8') as f:
#        f.write(sample_content)
#    
#    print(f"📄 Testing with sample file: {sample_file}")
#    chunks = process_document(sample_file)
#    
#    if chunks:
#        print(f"✅ Successfully processed: {len(chunks)} chunks")
#        for i, chunk in enumerate(chunks[:2]):  # Show first 2 chunks
#            print(f"\n--- Chunk {i} ---")
#            print(f"Text: {chunk['text'][:100]}...")
#            print(f"Metadata: {chunk['metadata']}")
#        return True
#    else:
#        print("❌ Sample processing failed")
#        return False
#
#
#def test_chunking_algorithm():
#    """Test the chunking algorithm with different text patterns."""
#    test_cases = [
#        ("Short text", "This is short"),
#        ("Medium text with paragraphs", "Paragraph 1.\n\nParagraph 2.\n\nParagraph #3."),
#        ("Long text", "Word " * 300)  # 1500+ characters
#    ]
#    
#    print("🧪 Testing chunking algorithm...")
#    for name, text in test_cases:
#        chunks = recursive_text_chunker(text, chunk_size=100, overlap=20)
#        print(f"✅ {name}: {len(chunks)} chunks")
#    
#    return True
#
#
#if __name__ == "__main__":
#    print("🚀 Testing document processing...")
#    
#    # Test 1: Chunking algorithm
#    test_chunking_algorithm()
#    
#    # Test 2: File processing
#    success = test_pdf_processing()
#    
#    # Test 3: Configuration integration
#    from rag.config import get_settings
#    settings = get_settings()
#    print(f"✅ Using chunk_size: {settings.chunk_size}, overlap: {settings.#chunk_overlap}")
#    
#    print(f"\n{'✅ ALL TESTS PASSED' if success else '❌ SOME TESTS FAILED'}")
#