from ..config import ELASTICSEARCH_INDEX


def search_bm25(es, question, top_k=10):
    print(f"BM25 searching for: {question}")
    response = es.search(
        index=ELASTICSEARCH_INDEX,
        body={
            "query": {
                "match": {
                    "text": question
                }
            },
            "size": top_k
        }
    )
    results = []
    for hit in response["hits"]["hits"]:
        results.append({
            "chunk_id": hit["_source"]["chunk_id"],
            "text": hit["_source"]["text"],
            "score": hit["_score"]
        })
    print(f"BM25 returned {len(results)} chunks")
    return results
