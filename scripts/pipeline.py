import os
from dotenv import load_dotenv
from pypdf import PdfReader
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
import anthropic
import google.generativeai as genai

load_dotenv()

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
EMBEDDING_MODEL = "BAAI/bge-base-en-v1.5"
QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", 6333))
COLLECTION_NAME = "ask_my_docs"
VECTOR_SIZE = 768  # bge-base produces 768-dimensional vectors


# STEP 1: LOAD PDF

def load_pdf(path):
    reader = PdfReader(path)
    pages = []
    for page in reader.pages:
        text = page.extract_text()
        if text:
            pages.append(text)
    full_text = "\n\n".join(pages)
    print(f"Loaded PDF: {len(reader.pages)} pages, {len(full_text)} characters")
    return full_text


# STEP 2: CHUNK TEXT

def chunk_text(text, chunk_size=500, overlap=50):
    words = text.split()
    chunks = []
    i = 0
    chunk_index = 0

    while i < len(words):
        chunk_words = words[i : i + chunk_size]
        chunk_content = " ".join(chunk_words)
        chunks.append({
            "chunk_id": chunk_index,
            "text": chunk_content,
            "word_count": len(chunk_words)
        })
        chunk_index += 1
        i += chunk_size - overlap

    print(f"Chunked into {len(chunks)} chunks (size={chunk_size}, overlap={overlap})")
    return chunks


# STEP 3: EMBED CHUNKS

def load_embedding_model():
    print(f"Loading embedding model: {EMBEDDING_MODEL}")
    model = SentenceTransformer(EMBEDDING_MODEL)
    print("Model loaded")
    return model

def embed_chunks(chunks, model):
    texts = [chunk["text"] for chunk in chunks]
    print(f"Embedding {len(texts)} chunks...")
    embeddings = model.encode(texts, show_progress_bar=True)

    for chunk, embedding in zip(chunks, embeddings):
        chunk["embedding"] = embedding.tolist()

    print(f"Done. Each embedding has {len(chunks[0]['embedding'])} dimensions")
    return chunks


# STEP 4: STORE IN QDRANT

def get_qdrant_client():
    return QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)

def create_collection(client):
    existing = [c.name for c in client.get_collections().collections]
    if COLLECTION_NAME in existing:
        print(f"Collection '{COLLECTION_NAME}' already exists, skipping creation")
        return
    client.create_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=VectorParams(size=VECTOR_SIZE, distance=Distance.COSINE)
    )
    print(f"Collection '{COLLECTION_NAME}' created")

def store_chunks(client, chunks):
    points = []
    for chunk in chunks:
        points.append(PointStruct(
            id=chunk["chunk_id"],
            vector=chunk["embedding"],
            payload={
                "text": chunk["text"],
                "chunk_id": chunk["chunk_id"],
                "word_count": chunk["word_count"]
            }
        ))
    client.upsert(collection_name=COLLECTION_NAME, points=points)
    print(f"Stored {len(points)} chunks in Qdrant")


# STEP 5: QUERY QDRANT

def search(client, model, question, top_k=5):
    print(f"Searching for: {question}")
    question_embedding = model.encode(question).tolist()
    results = client.query_points(
        collection_name=COLLECTION_NAME,
        query=question_embedding,
        limit=top_k
    ).points
    chunks = []
    for result in results:
        chunks.append({
            "chunk_id": result.payload["chunk_id"],
            "text": result.payload["text"],
            "score": result.score
        })
    print(f"Found {len(chunks)} relevant chunks")
    return chunks


# STEP 6: GENERATE ANSWER WITH CLAUDE

def build_prompt(question, chunks):
    context = ""
    for i, chunk in enumerate(chunks):
        context += f"[CHUNK {i+1}]\n{chunk['text']}\n\n"

    prompt = f"""You are a precise document assistant. Answer the user's question using ONLY the context chunks provided below.

Rules:
- Only use information from the provided chunks
- Cite your sources by referencing [CHUNK X] inline
- If the answer is not in the chunks, say "I could not find this information in the provided document"
- Do not use any outside knowledge

Context:
{context}

Question: {question}

Answer:"""
    return prompt


def get_latest_flash_model():
    # Lists all models and picks the first one that contains 'flash' and 'gemini'
    for m in genai.list_models():
        if 'gemini' in m.name and 'flash' in m.name:
            if 'generateContent' in m.supported_generation_methods:
                return m.name
    return "gemini-2.5-flash" # Fallback



def generate_answer(question, chunks):
    # client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    # prompt = build_prompt(question, chunks)
    # response = client.messages.create(
    #     model="claude-opus-4-5",
    #     max_tokens=1024,
    #     messages=[
    #         {"role": "user", "content": prompt}
    #     ]
    # )
    # return response.content[0].text
    genai.configure(api_key=GEMINI_API_KEY)
    model_name = get_latest_flash_model()
    print(model_name)
    model = genai.GenerativeModel(model_name)
    prompt = build_prompt(question, chunks)
    response = model.generate_content(prompt)
    return response.text

if __name__ == "__main__":
    import sys

    mode = sys.argv[1] if len(sys.argv) > 1 else "ingest"

    if mode == "ingest":
        text = load_pdf("data/sample.pdf")
        chunks = chunk_text(text)
        model = load_embedding_model()
        chunks = embed_chunks(chunks, model)
        qdrant = get_qdrant_client()
        create_collection(qdrant)
        store_chunks(qdrant, chunks)
        print("Ingestion complete")

    elif mode == "search":
        question = sys.argv[2] if len(sys.argv) > 2 else "What is this document about?"
        model = load_embedding_model()
        qdrant = get_qdrant_client()
        results = search(qdrant, model, question)
        for r in results:
            print(f"\n--- Chunk {r['chunk_id']} (score: {r['score']:.4f}) ---")
            print(r["text"][:300])

    elif mode == "ask":
        question = sys.argv[2] if len(sys.argv) > 2 else "What is this document about?"
        model = load_embedding_model()
        qdrant = get_qdrant_client()
        chunks = search(qdrant, model, question)
        answer = generate_answer(question, chunks)
        print(f"\nQuestion: {question}")
        print(f"\nAnswer:\n{answer}")