import sys

from .ingestion import (
    load_pdf, chunk_text, load_embedding_model, embed_chunks,
    get_qdrant_client, create_collection, store_chunks,
    get_es_client, create_es_index, index_chunks_es,
)
from .retrieval import search_vector, search_bm25, reciprocal_rank_fusion, rerank
from .generation import generate_answer


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "ingest"

    if mode == "ingest":
        text = load_pdf("data/Systemdesign.pdf")
        chunks = chunk_text(text)
        model = load_embedding_model()
        chunks = embed_chunks(chunks, model)
        qdrant = get_qdrant_client()
        create_collection(qdrant)
        store_chunks(qdrant, chunks)
        es = get_es_client()
        create_es_index(es)
        index_chunks_es(es, chunks)
        print("Ingestion complete")

    elif mode == "ask":
        question = sys.argv[2] if len(sys.argv) > 2 else "What is this document about?"
        model = load_embedding_model()
        qdrant = get_qdrant_client()
        chunks = search_vector(qdrant, model, question)
        answer = generate_answer(question, chunks)
        print(f"\nQuestion: {question}")
        print(f"\nAnswer:\n{answer}")

    elif mode == "hybrid":
        question = sys.argv[2] if len(sys.argv) > 2 else "What is this document about?"
        model = load_embedding_model()
        qdrant = get_qdrant_client()
        es = get_es_client()
        vector_results = search_vector(qdrant, model, question, top_k=10)
        bm25_results = search_bm25(es, question, top_k=10)
        fused_chunks = reciprocal_rank_fusion(vector_results, bm25_results)
        reranked_chunks = rerank(question, fused_chunks)
        answer = generate_answer(question, reranked_chunks)
        print(f"\nQuestion: {question}")
        print(f"\nAnswer:\n{answer}")
