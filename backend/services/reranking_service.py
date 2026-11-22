
from functools import lru_cache

from sentence_transformers import CrossEncoder


MODEL_NAME = "cross-encoder/ms-marco-MiniLM-L-6-v2"


@lru_cache(maxsize=1)
def get_reranker():
    """Load the reranking model only once."""

    return CrossEncoder(
        MODEL_NAME,
        max_length=512
    )


def rerank_chunks(query: str, results: list[dict]) -> list[dict]:
    """
    Reorder retrieved chunks according to their relevance
    to the user's question.
    """

    if not isinstance(query, str) or not query.strip():
        raise ValueError("Search query cannot be empty.")

    if not results:
        return []

    # Create question-chunk pairs.
    pairs = [
        (query, result["chunk"]["text"])
        for result in results
    ]

    # Calculate relevance scores.
    reranker = get_reranker()

    scores = reranker.predict(
        pairs,
        show_progress_bar=False
    )

    # Preserve original results and add reranking scores.
    reranked_results = []

    for result, score in zip(results, scores):
        updated_result = result.copy()
        updated_result["rerank_score"] = float(score)

        reranked_results.append(updated_result)

    # Highest reranking score comes first.
    reranked_results.sort(
        key=lambda item: item["rerank_score"],
        reverse=True
    )

    return reranked_results
