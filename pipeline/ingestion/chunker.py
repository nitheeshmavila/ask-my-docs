from ..config import CHUNK_SIZE, OVERLAP


def chunk_text(text, chunk_size=CHUNK_SIZE, overlap=OVERLAP):
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
