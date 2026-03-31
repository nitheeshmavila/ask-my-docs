# Ask My Docs

A RAG (Retrieval-Augmented Generation) pipeline that lets you ask questions about your PDF documents using semantic search and LLM-powered answers.

## How It Works

1. Load - Extracts text from a PDF
2. Chunk - Splits text into overlapping word-based chunks
3. Embed - Generates vector embeddings using BAAI/bge-base-en-v1.5
4. Store - Indexes chunks in Qdrant for fast similarity search
5. Search - Finds the most relevant chunks for a given question
6. Answer - Sends retrieved context to Gemini Flash to generate a grounded answer

## Prerequisites

- Python 3.10+
- Qdrant running locally (default: localhost:6333)

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install pypdf sentence-transformers qdrant-client anthropic google-generativeai python-dotenv
```

Create a .env file:

```
GEMINI_API_KEY=your-key-here
QDRANT_HOST=localhost
QDRANT_PORT=6333
```

## Usage

Place your PDF at data/sample.pdf, then:

```bash
# Ingest the PDF into Qdrant
python scripts/pipeline.py ingest

# Search for relevant chunks
python scripts/pipeline.py search "What is this document about?"

# Ask a question and get an LLM-generated answer
python scripts/pipeline.py ask "What are the key findings?"
```
