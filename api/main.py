import asyncio
import os
import shutil
from functools import partial

from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from pipeline.ingestion import (
    load_pdf, chunk_text, load_embedding_model, embed_chunks,
    get_qdrant_client, create_collection, store_chunks,
    get_es_client, create_es_index, index_chunks_es,
)
from pipeline.retrieval import search_vector, search_bm25, reciprocal_rank_fusion, rerank
from pipeline.generation import generate_answer

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = "/tmp/ask-my-docs"
os.makedirs(UPLOAD_DIR, exist_ok=True)


class AskRequest(BaseModel):
    question: str


@app.get("/health")
async def health_check():
    return {"status": "ok"}


@app.post("/ingest")
async def ingest(file: UploadFile = File(...)):
    if not file.filename.endswith(".pdf"):
        return {"error": "Only PDF files are accepted"}

    file_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(file_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    loop = asyncio.get_event_loop()

    text = load_pdf(file_path)
    chunks = chunk_text(text)

    model = await loop.run_in_executor(None, load_embedding_model)
    chunks = await loop.run_in_executor(None, embed_chunks, chunks, model)

    qdrant = get_qdrant_client()
    create_collection(qdrant)
    store_chunks(qdrant, chunks)

    es = get_es_client()
    create_es_index(es)
    index_chunks_es(es, chunks)

    return {
        "filename": file.filename,
        "chunks": len(chunks),
        "status": "ingested",
    }


@app.post("/ask")
async def ask(req: AskRequest):
    loop = asyncio.get_event_loop()
    question = req.question

    model = await loop.run_in_executor(None, load_embedding_model)

    qdrant = get_qdrant_client()
    vector_results = await loop.run_in_executor(
        None, partial(search_vector, qdrant, model, question)
    )

    es = get_es_client()
    bm25_results = await loop.run_in_executor(
        None, partial(search_bm25, es, question)
    )

    fused = reciprocal_rank_fusion(vector_results, bm25_results)
    reranked = await loop.run_in_executor(None, partial(rerank, question, fused))
    answer = await loop.run_in_executor(None, partial(generate_answer, question, reranked))

    return {
        "answer": answer,
        "chunks": reranked,
    }
