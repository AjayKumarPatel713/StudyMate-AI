
from functools import lru_cache

import numpy as np
from sentence_transformers import SentenceTransformer


MODEL_NAME = "all-MiniLM-L6-v2"


@lru_cache(maxsize=1)
def get_embedding_model():
    """
    Load the embedding model only once.
    """

    return SentenceTransformer(MODEL_NAME)


def generate_embeddings(texts: list[str]) -> np.ndarray:
    """
    Convert a list of text chunks into normalized embeddings.
    """

    if not texts:
        raise ValueError("Text list cannot be empty.")

    if not all(isinstance(text, str) and text.strip() for text in texts):
        raise ValueError("All texts must be non-empty strings.")

    model = get_embedding_model()

    embeddings = model.encode(
        texts,
        normalize_embeddings=True,
        convert_to_numpy=True,
        show_progress_bar=False
    )

    return np.asarray(embeddings, dtype=np.float32)


def get_embedding_dimension() -> int:
    """
    Return the number of dimensions in each embedding.
    """

    return get_embedding_model().get_embedding_dimension()
