
from backend.services.embedding_service import generate_embeddings
from backend.services.vector_service import VectorStore


def retrieve_relevant_chunks(
    query: str,
    top_k: int = 5,
    index_name: str = "studymate_index"
) -> list[dict]:
    """
    Retrieve the most relevant document chunks for a question.
    """

    if not isinstance(query, str) or not query.strip():
        raise ValueError("Search query cannot be empty.")

    if top_k <= 0:
        raise ValueError("top_k must be positive.")

    # Step 1: Convert question into an embedding
    query_embedding = generate_embeddings([query])

    # Step 2: Load the saved FAISS index
    vector_store = VectorStore.load(index_name)

    # Step 3: Search for similar chunks
    results = vector_store.search(
        query_embedding=query_embedding,
        top_k=top_k
    )

    return results
