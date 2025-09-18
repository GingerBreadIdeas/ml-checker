# Simple RAG Chatbot with Langfuse Integration

A terminal-based RAG (Retrieval-Augmented Generation) chatbot using LangChain, Ollama, and Langfuse for observability.

## Overview

This project creates a simple chatbot that:
- Downloads a small text dataset automatically
- Uses LangChain for RAG pipeline
- Runs a local LLM via Ollama
- Integrates Langfuse for tracing and observability

## Prerequisites

1. **Python 3.8+**
2. **Ollama installed locally**
   ```bash
   curl -fsSL https://ollama.ai/install.sh | sh
   ```
3. **A small LLM model** (e.g., llama2:7b-chat or mistral:7b)
   ```bash
   ollama pull mistral:7b
   ```

## Implementation Plan

### 1. Project Setup
```bash
pip install langchain langchain-community langchain-ollama langfuse chromadb requests beautifulsoup4
```

### 2. Dataset Selection
Use one of these small, freely available datasets:
- **Paul Graham Essays** (http://www.paulgraham.com/articles.html)
- **Simple Wikipedia articles** (via API)
- **Project Gutenberg short stories**

### 3. Main Components (`main.py`)

#### A. Dataset Download & Preprocessing
- Check if dataset exists locally
- Download if not present (using requests/BeautifulSoup)
- Clean and chunk text (500-1000 char chunks)

#### B. Vector Store Setup
- Use ChromaDB for local vector storage
- Generate embeddings using sentence-transformers
- Store chunked documents with metadata

#### C. LLM Integration
- Connect to local Ollama instance
- Use langchain-ollama wrapper
- Configure for chat completion

#### D. RAG Pipeline
- Document retrieval (top-k similarity search)
- Context injection into prompts
- Response generation

#### E. Langfuse Integration
- Initialize Langfuse client
- Trace RAG pipeline steps:
  - Query embedding
  - Document retrieval
  - LLM generation
  - Full conversation flow

#### F. Terminal Interface
- Simple input/output loop
- Display retrieved context (optional debug mode)
- Conversation history

### 4. File Structure
```
langfuse_example/
├── main.py                 # Main application
├── requirements.txt        # Dependencies
├── data/                   # Downloaded dataset
│   └── documents.json
├── vector_db/             # ChromaDB storage
└── .env                   # Langfuse credentials
```

### 5. Environment Variables
```env
LANGFUSE_SECRET_KEY=your_secret_key
LANGFUSE_PUBLIC_KEY=your_public_key
LANGFUSE_HOST=https://cloud.langfuse.com
OLLAMA_BASE_URL=http://localhost:11434
```

### 6. Key Features to Implement

#### Basic RAG Flow
1. User asks question
2. Embed query using sentence-transformers
3. Retrieve relevant documents from ChromaDB
4. Construct prompt with context
5. Generate response via Ollama
6. Return answer to user

#### Langfuse Tracing
- **Trace**: Full conversation turn
- **Spans**: Individual components (embed, retrieve, generate)
- **Scores**: Response quality metrics
- **Metadata**: Model used, retrieval count, token usage

### 7. Sample Usage
```bash
python main.py

> What is the main topic of the dataset?
[Retrieved context shown]
Based on the documents, the main topics include...

> How does X relate to Y?
[System retrieves relevant chunks and generates response]
```

### 8. Testing Langfuse Integration

#### Verification Steps
- Check traces appear in Langfuse dashboard
- Verify span hierarchy (query → retrieval → generation)
- Monitor token usage and latency
- Test error handling and logging

#### Sample Trace Structure
```
Conversation Turn
├── Query Embedding (span)
├── Document Retrieval (span)
│   ├── Vector Search
│   └── Context Preparation  
└── LLM Generation (span)
    ├── Prompt Construction
    └── Ollama API Call
```

## Getting Started

1. Clone and setup environment
2. Start Ollama: `ollama serve`
3. Configure Langfuse credentials in `.env`
4. Run: `python main.py`
5. Ask questions about the downloaded dataset
6. Check Langfuse dashboard for traces

## Success Metrics

- [x] Automatic dataset download
- [x] Functional RAG pipeline
- [x] Local LLM integration
- [x] Complete Langfuse tracing
- [x] Terminal-based interaction
- [x] Error handling and logging