
from backend.services.retrieval_service import retrieve_relevant_chunks
from backend.services.llm_service import generate_response


SIMILARITY_THRESHOLD = 0.30
MAX_CONTEXT_CHARS = 8000


def generate_rag_response(
    question: str,
    top_k: int = 5,
    max_context_chars: int = MAX_CONTEXT_CHARS
) -> dict:
    """Generate an answer using retrieved document context."""

    if not isinstance(question, str) or not question.strip():
        raise ValueError("Question cannot be empty.")

    if max_context_chars <= 0:
        raise ValueError("Maximum context size must be positive.")

    # Step 1: Retrieve relevant chunks.
    retrieved_chunks = retrieve_relevant_chunks(
        query=question,
        top_k=top_k
    )

    # Step 2: Filter chunks using similarity threshold.
    relevant_chunks = [
        result for result in retrieved_chunks
        if result["similarity"] >= SIMILARITY_THRESHOLD
    ]

    if not relevant_chunks:
        return {
            "answer": (
                "I could not find sufficiently relevant information "
                "in your uploaded documents."
            ),
            "sources": []
        }

    # Step 3: Remove duplicates and control context size.
    context_parts = []
    sources = []
    seen_chunks = set()
    current_context_size = 0

    for result in relevant_chunks:
        chunk = result["chunk"]
        chunk_text = chunk["text"].strip()

        if not chunk_text or chunk_text in seen_chunks:
            continue

        separator = "\n\n" if context_parts else ""
        remaining_chars = (
            max_context_chars - current_context_size - len(separator)
        )

        if remaining_chars <= 0:
            break

        # Truncate the final chunk if it exceeds the remaining limit.
        if len(chunk_text) > remaining_chars:
            chunk_text = chunk_text[:remaining_chars].rstrip()

        if not chunk_text:
            break

        seen_chunks.add(chunk["text"].strip())
        context_parts.append(chunk_text)

        current_context_size += len(separator) + len(chunk_text)

        sources.append({
            "filename": chunk["filename"],
            "page_number": chunk.get("page_number"),
            "slide_number": chunk.get("slide_number"),
            "similarity": round(result["similarity"], 3)
        })

        if current_context_size >= max_context_chars:
            break

    context = "\n\n".join(context_parts)

    # Step 4: Prepare the prompt.
    prompt = f"""
Answer the student's question using the context below.

Context:
{context}

Question:
{question}

Instructions:
- Use the provided context as your primary source.
- Give a clear and simple explanation.
- If the answer is not available in the context, clearly say so.
- Do not invent facts or information.
"""

    # Step 5: Generate the answer using Gemini.
    answer = generate_response(prompt)

    return {
        "answer": answer,
        "sources": sources
    }
