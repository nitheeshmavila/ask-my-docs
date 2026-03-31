from ..config import COLLECTION_NAME


def search_vector(client, model, question, top_k=10):
    print(f"Vector searching for: {question}")
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
    print(f"Vector search returned {len(chunks)} chunks")
    return chunks
