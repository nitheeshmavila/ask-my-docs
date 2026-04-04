# Ask My Docs

A RAG (Retrieval-Augmented Generation) system that lets you upload PDF documents and ask questions about them through a chat interface. It uses hybrid retrieval combining semantic search and BM25, cross-encoder reranking, and LLM-powered answer generation with source citations.

## Architecture

```
PDF Upload
    |
    v
[Text Extraction] --> [Chunking] --> [Embedding] --> [Qdrant (vector)]
                                                  --> [Elasticsearch (BM25)]

User Question
    |
    v
[Encode Query]
    |
    +--> [Qdrant semantic search] --+
    |                               |--> [Reciprocal Rank Fusion] --> [Cross-Encoder Rerank] --> [Gemini LLM] --> Answer
    +--> [ES BM25 keyword search] --+
```

### Pipeline stages

1. **Load** -- Extracts text from PDF using PyPDF
2. **Chunk** -- Splits text into 250-word overlapping chunks (25-word overlap)
3. **Embed** -- Generates 768-dimensional vectors using BAAI/bge-base-en-v1.5
4. **Store** -- Indexes chunks in both Qdrant (vectors) and Elasticsearch (text)
5. **Retrieve** -- Runs semantic search (top 10) and BM25 search (top 10) in parallel
6. **Fuse** -- Combines results using Reciprocal Rank Fusion (top 5)
7. **Rerank** -- Scores with cross-encoder/ms-marco-MiniLM-L-6-v2 (top 3)
8. **Generate** -- Sends context to Gemini Flash with citation-enforcing prompt

## Project structure

```
ask-my-docs/
  api/
    main.py              # FastAPI server (ingest, ask, health endpoints)
  pipeline/
    config.py            # All model and service configuration
    __main__.py          # CLI entry point
    ingestion/
      loader.py          # PDF text extraction
      chunker.py         # Word-based chunking with overlap
      embedder.py        # Sentence-transformer embeddings
      qdrant_store.py    # Qdrant vector storage
      es_store.py        # Elasticsearch BM25 indexing
    retrieval/
      vector_search.py   # Semantic search via Qdrant
      bm25_search.py     # Keyword search via Elasticsearch
      fusion.py          # Reciprocal Rank Fusion
      reranker.py        # Cross-encoder reranking
    generation/
      llm.py             # Gemini API integration
      prompt.py          # Prompt template with citation rules
  ui/
    src/
      App.tsx            # React chat interface
      App.css            # Styling
    vite.config.ts       # Dev server with API proxy
    package.json
  data/                  # Sample PDFs
  requirements.txt
  .env                   # API keys and service URLs
```

## Prerequisites

- Python 3.10+
- Node.js 18+
- Qdrant running locally on port 6333
- Elasticsearch running locally on port 9200
- Gemini API key

### Starting Qdrant and Elasticsearch

```bash
docker run -d -p 6333:6333 qdrant/qdrant
docker run -d -p 9200:9200 -e "discovery.type=single-node" -e "xpack.security.enabled=false" elasticsearch:8.13.0
```

## Setup

### Backend

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Create a `.env` file in the project root:

```
GEMINI_API_KEY=your-gemini-api-key
QDRANT_HOST=localhost
QDRANT_PORT=6333
ELASTICSEARCH_URL=http://localhost:9200
ELASTICSEARCH_INDEX=ask_my_docs
```

### Frontend

```bash
cd ui
npm install
```

## Running

### Start the API server

```bash
uvicorn api.main:app --reload
```

This starts the FastAPI server on http://localhost:8000.

### Start the frontend

```bash
cd ui
npm run dev
```

This starts the Vite dev server on http://localhost:5173. The dev server proxies `/api/*` requests to the backend.

### Using the app

1. Open http://localhost:5173 in your browser
2. Upload a PDF document
3. Ask questions about it in the chat

## API endpoints

**GET /health** -- Health check, returns `{"status": "ok"}`

**POST /ingest** -- Upload and index a PDF document
- Body: multipart form data with a `file` field (PDF only)
- Returns: `{"filename": "...", "chunks": N, "status": "ingested"}`

**POST /ask** -- Ask a question about the indexed document
- Body: `{"question": "your question here"}`
- Returns: `{"answer": "...", "chunks": [...]}`

## CLI usage

The pipeline can also be run directly from the command line:

```bash
# Ingest a PDF (uses data/Systemdesign.pdf by default)
python -m pipeline ingest

# Ask a question using vector search only
python -m pipeline ask "What is this document about?"

# Ask using the full hybrid pipeline (vector + BM25 + rerank)
python -m pipeline hybrid "What are the key concepts?"
```

## Configuration

All model and service settings are in `pipeline/config.py`:

| Setting | Default |
|---|---|
| Embedding model | BAAI/bge-base-en-v1.5 |
| Reranker model | cross-encoder/ms-marco-MiniLM-L-6-v2 |
| Chunk size | 250 words |
| Chunk overlap | 25 words |
| Vector dimensions | 768 |
| Qdrant host | localhost:6333 |
| Elasticsearch URL | localhost:9200 |
| ES index name | ask_my_docs |

## Tech stack

- **Backend**: FastAPI, Python
- **Frontend**: React, TypeScript, Vite
- **Embeddings**: sentence-transformers (BAAI/bge-base-en-v1.5)
- **Vector DB**: Qdrant
- **Text search**: Elasticsearch
- **Reranking**: cross-encoder/ms-marco-MiniLM-L-6-v2
- **LLM**: Google Gemini Flash
- **PDF parsing**: PyPDF
