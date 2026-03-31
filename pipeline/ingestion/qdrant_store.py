from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from ..config import QDRANT_HOST, QDRANT_PORT, COLLECTION_NAME, VECTOR_SIZE


def get_qdrant_client():
    return QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)


def create_collection(client):
    existing = [c.name for c in client.get_collections().collections]
    if COLLECTION_NAME in existing:
        client.delete_collection(COLLECTION_NAME)
        print(f"Deleted existing Qdrant collection '{COLLECTION_NAME}'")
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
