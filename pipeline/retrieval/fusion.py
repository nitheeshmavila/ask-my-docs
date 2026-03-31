def reciprocal_rank_fusion(vector_results, bm25_results, top_k=5, k=60):
    scores = {}
    texts = {}

    for rank, chunk in enumerate(vector_results):
        cid = chunk["chunk_id"]
        scores[cid] = scores.get(cid, 0) + 1 / (k + rank + 1)
        texts[cid] = chunk["text"]

    for rank, chunk in enumerate(bm25_results):
        cid = chunk["chunk_id"]
        scores[cid] = scores.get(cid, 0) + 1 / (k + rank + 1)
        texts[cid] = chunk["text"]

    sorted_chunks = sorted(scores.items(), key=lambda x: x[1], reverse=True)

    fused = []
    for cid, score in sorted_chunks[:top_k]:
        fused.append({
            "chunk_id": cid,
            "text": texts[cid],
            "score": score
        })

    print(f"RRF fusion produced {len(fused)} chunks")
    return fused
