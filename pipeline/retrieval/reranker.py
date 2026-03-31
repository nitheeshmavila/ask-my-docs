from sentence_transformers import CrossEncoder
from ..config import RERANKER_MODEL


def rerank(question, chunks, top_k=3):
    print(f"Loading reranker: {RERANKER_MODEL}")
    reranker = CrossEncoder(RERANKER_MODEL)
    pairs = [(question, chunk["text"]) for chunk in chunks]
    scores = reranker.predict(pairs)
    for chunk, score in zip(chunks, scores):
        chunk["rerank_score"] = float(score)
    reranked = sorted(chunks, key=lambda x: x["rerank_score"], reverse=True)
    print(f"Reranked. Top chunk score: {reranked[0]['rerank_score']:.4f}")
    return reranked[:top_k]
