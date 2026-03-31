from elasticsearch import Elasticsearch
from ..config import ELASTICSEARCH_URL, ELASTICSEARCH_INDEX


def get_es_client():
    return Elasticsearch(ELASTICSEARCH_URL)


def create_es_index(es):
    try:
        es.indices.get(index=ELASTICSEARCH_INDEX)
        es.indices.delete(index=ELASTICSEARCH_INDEX)
        print(f"Deleted existing ES index '{ELASTICSEARCH_INDEX}'")
    except Exception:
        pass
    es.indices.create(
        index=ELASTICSEARCH_INDEX,
        body={
            "mappings": {
                "properties": {
                    "chunk_id": {"type": "integer"},
                    "text": {"type": "text"},
                    "word_count": {"type": "integer"}
                }
            }
        }
    )
    print(f"ES index '{ELASTICSEARCH_INDEX}' created")


def index_chunks_es(es, chunks):
    for chunk in chunks:
        es.index(
            index=ELASTICSEARCH_INDEX,
            id=chunk["chunk_id"],
            body={
                "chunk_id": chunk["chunk_id"],
                "text": chunk["text"],
                "word_count": chunk["word_count"]
            }
        )
    es.indices.refresh(index=ELASTICSEARCH_INDEX)
    print(f"Indexed {len(chunks)} chunks in Elasticsearch")
