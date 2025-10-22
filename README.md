
# 🚀 Production-Ready RAG System

> A complete **Retrieval-Augmented Generation (RAG)** system built with functional programming principles — featuring intelligent document processing, semantic search, and AI-powered responses.

![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Status](https://img.shields.io/badge/status-production--ready-brightgreen.svg)

---

## 📋 Table of Contents

- [🚀 Production-Ready RAG System](#-production-ready-rag-system)
  - [📋 Table of Contents](#-table-of-contents)
  - [🎯 Overview](#-overview)
  - [✨ Features](#-features)
    - [🔧 Core Functionality](#-core-functionality)
    - [🧱 Production-Grade Enhancements](#-production-grade-enhancements)
  - [🛠️ Tech Stack](#️-tech-stack)
    - [Core Technologies](#core-technologies)
    - [Development Tools](#development-tools)
  - [🏗️ Architecture](#️-architecture)
    - [🔄 Data Flow](#-data-flow)
  - [📦 Installation](#-installation)
    - [Prerequisites](#prerequisites)
    - [Setup Steps](#setup-steps)
  - [🚀 Usage](#-usage)
    - [💡 Interactive CLI](#-interactive-cli)
    - [Options:](#options)
    - [🧠 Python API Example](#-python-api-example)
- [⚙️ Configuration Example (config.py)](#️-configuration-example-configpy)
- [🔮 Future Enhancements](#-future-enhancements)
  - [Phase 1 — API \& Auth (High Priority)](#phase-1--api--auth-high-priority)
  - [Phase 2 — Advanced Retrieval](#phase-2--advanced-retrieval)
  - [Phase 3 — Document Support](#phase-3--document-support)
  - [Phase 4 — Web Interface](#phase-4--web-interface)
  - [Phase 5 — Advanced Features](#phase-5--advanced-features)
  - [🎯 Why This Project Stands Out](#-why-this-project-stands-out)
  - [Best Practices](#best-practices)
  - [**Real-World Value**](#real-world-value)
- [📄 License](#-license)

---

## 🎯 Overview

This **RAG (Retrieval-Augmented Generation)** system enables intelligent question-answering from your documents. It processes data, creates semantic embeddings, stores them in a vector database, and generates context-aware responses using Large Language Models.

**Perfect for:**
- 📚 Document Q&A systems  
- 🔍 Intelligent search applications  
- 💼 Enterprise knowledge bases  
- 🎓 Educational platforms  
- 📊 Research paper analysis  

---

## ✨ Features

### 🔧 Core Functionality
- ✅ **Multi-format Document Processing:** PDF, DOCX, TXT, JSON  
- ✅ **Intelligent Text Chunking:** Context-aware segmentation  
- ✅ **Semantic Embeddings:** High-quality vectors (SentenceTransformers)  
- ✅ **Smart Caching:** Disk-based cache for repeated queries  
- ✅ **Vector Database Integration:** Pinecone for similarity search  
- ✅ **LLM Integration:** Google Gemini for response generation  
- ✅ **Interactive CLI:** Clean command-line interface  
- ✅ **Source Attribution:** Returns relevance scores & citations  

### 🧱 Production-Grade Enhancements
- 🛡️ **Error Handling:** Graceful recovery and fallbacks  
- 📝 **Structured Logging:** DEBUG, INFO, ERROR levels  
- ⚡ **Batch Processing:** Memory-efficient large document handling  
- 🔄 **Configurable Settings:** Environment-based configuration  
- 📊 **Performance Monitoring:** Cache hit rates and metrics  
- 🧪 **Testing Support:** Unit & integration testing ready  

---

## 🛠️ Tech Stack

### Core Technologies

| Component | Technology | Purpose |
|------------|-------------|----------|
| **Language** | Python 3.11+ | Core development |
| **Package Manager** | uv | Fast dependency management |
| **LLM** | Google Gemini 2.0 | Response generation |
| **Embeddings** | Sentence-Transformers | Semantic vector creation |
| **Vector DB** | Pinecone | Similarity search & storage |
| **PDF Processing** | PyPDF2 | Document text extraction |
| **Config Management** | Pydantic | Environment validation |

### Development Tools
- 🧪 **Testing:** pytest  
- 🧹 **Code Quality:** black, isort  
- 🧾 **Type Checking:** mypy (optional)  
- 🧠 **Logging:** Python logging module  

---

## 🏗️ Architecture


### 🔄 Data Flow

1. **Ingestion:** PDF/DOCX → Text extraction → Cleaning  
2. **Chunking:** Text → Segmentation → Metadata enrichment  
3. **Embedding:** Sentence-transformers → 384-dim vectors  
4. **Storage:** Vectors + Metadata → Pinecone index  
5. **Query:** User question → Embedding → Similarity search  
6. **Generation:** Retrieved context + Query → Gemini LLM → Answer  

---

## 📦 Installation

### Prerequisites
- Python ≥ 3.11  
- Pinecone API key  
- Google Gemini API key  

### Setup Steps

```bash
# 1. Clone the repository
git clone https://github.com/yourusername/rag-project.git
cd rag-project

# 2. Install uv (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# 3. Create virtual environment & install dependencies
uv venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
uv sync

# 4. Install the package
uv add -e .

# 5. Add core dependencies
uv add google-generativeai pinecone-client sentence-transformers PyPDF2 python-dotenv pydantic pydantic-settings numpy

# 6. Create environment file
cp .env.example .env
# Edit .env with your API keys

# Example .env Configuration

``` python 
# API Keys
GOOGLE_API_KEY=your_google_api_key
PINECONE_API_KEY=your_pinecone_api_key

# Config
PINECONE_INDEX_NAME=your-index-name
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2

# Processing
CHUNK_SIZE=1000
CHUNK_OVERLAP=200

# General
PROJECT_NAME=rag-project
DEBUG=false

```

## 🚀 Usage
### 💡 Interactive CLI

``` python 
python src/rag_pipeline.py
```
### Options:
-1️⃣ Process new document
-2️⃣ Query existing knowledge base
-3️⃣ Exit

### 🧠 Python API Example
``` python 
from rag.documents import process_document
from rag.embeddings import embed_document_chunks
from rag.vectorstore import store_embedded_documents
from rag.llm_integration import ask_question, ask_question_detailed

# Process & store
chunks = process_document("data/your_document.pdf")
embedded = embed_document_chunks(chunks)
store_embedded_documents(embedded)

# Simple query
print(ask_question("What is prompt engineering?"))

# Detailed query with sources
res = ask_question_detailed("Explain RAG systems")
print(res["answer"])
for src in res["sources"]:
    print(f"- {src['source']} (Score: {src['relevance_score']:.3f})")
    ```
# 📁 Project Structure
``` python 
rag-project/
├── src/
│   └── rag/
│       ├── config.py
│       ├── documents.py
│       ├── embeddings.py
│       ├── vectorstore.py
│       ├── llm_integration.py
│       └── utils.py
│
├── tests/
│   ├── test_documents.py
│   ├── test_embeddings.py
│   └── test_vectorstore.py
│
├── scripts/
│   └── rag_pipeline.py
│
├── data/
│   ├── raw/
│   ├── embeddings_cache/
│   └── logs/
│
├── .env
├── .env.example
├── .gitignore
├── pyproject.toml
├── README.md
└── requirements.txt
```
# ⚙️ Configuration Example (config.py)
  ``` python 
from pydantic_settings import BaseSettings
from pathlib import Path

class Settings(BaseSettings):
    google_api_key: str
    pinecone_api_key: str
    pinecone_index_name: str
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    chunk_size: int = 1000
    chunk_overlap: int = 200
    data_dir: Path = Path("data")
    logs_dir: Path = Path("logs")

```
#  🔮 Future Enhancements
## Phase 1 — API & Auth (High Priority)

 FastAPI REST endpoints

 JWT authentication

 Rate limiting

 Swagger docs

## Phase 2 — Advanced Retrieval

 Hybrid search (semantic + keyword)

 Multi-query & re-ranking

 Query expansion

## Phase 3 — Document Support

 OCR for scanned files

 Image & table extraction

 HTML / Markdown support

## Phase 4 — Web Interface

 React/Next.js UI

 Chat interface

 Upload portal

## Phase 5 — Advanced Features

 Multi-language support

 Fine-tuned embeddings

 Conversation memory

## 🎯 Why This Project Stands Out
Technical Excellence

- ✅ Production-Ready Code – Modular & deployable
- ✅ Functional Programming – Clean & testable
- ✅ Performance Optimized – Caching, batching, metrics
- ✅ Error-Resilient – Structured logging

## Best Practices

- ✅ Type hints & docstrings
- ✅ Config-based architecture
- ✅ Consistent coding style
- ✅ Unit & integration test support

## **Real-World Value**

- ✅ Scalable for thousands of docs
- ✅ Extensible architecture
- ✅ Portfolio-ready professional project

# 📄 License

This project is licensed under the MIT License — see the LICENSE
 file for details.

👤 Author

Amna Akram 

GitHub: @Amna-05 

Email: amnaaa963@gmail.com

Made with 🤍 by Amna.