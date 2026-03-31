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
