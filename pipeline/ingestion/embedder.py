from sentence_transformers import SentenceTransformer
from ..config import EMBEDDING_MODEL


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
