import os
import shutil
from fastapi import FastAPI, UploadFile, File
from pipeline.ingestion import (
    load_pdf, chunk_text, load_embedding_model, embed_chunks,
    get_qdrant_client, create_collection, store_chunks,
    get_es_client, create_es_index, index_chunks_es,
)

app = FastAPI()

UPLOAD_DIR = "data"
os.makedirs(UPLOAD_DIR, exist_ok=True)


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.post("/upload")
def upload_pdf(file: UploadFile = File(...)):
    if not file.filename.endswith(".pdf"):
        return {"error": "Only PDF files are accepted"}

    file_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(file_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    text = load_pdf(file_path)
    chunks = chunk_text(text)
    model = load_embedding_model()
    chunks = embed_chunks(chunks, model)

    qdrant = get_qdrant_client()
    create_collection(qdrant)
    store_chunks(qdrant, chunks)

    es = get_es_client()
    create_es_index(es)
    index_chunks_es(es, chunks)

    return {
        "filename": file.filename,
        "chunks": len(chunks),
        "status": "ingested"
    }
