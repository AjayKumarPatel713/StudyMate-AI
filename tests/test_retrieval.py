
import pytest

from backend.services.vector_service import VectorStore


def test_add_and_search_vectors():
    store = VectorStore(3)

    chunks = [
        {
            "document_id": "doc1",
            "text": "Python programming"
        },
        {
            "document_id": "doc2",
            "text": "Database management"
        }
    ]

    import numpy as np

    embeddings = np.array(
        [
            [1, 0, 0],
            [0, 1, 0]
        ],
        dtype=np.float32
    )

    store.add_embeddings(embeddings, chunks)

    results = store.search(
        np.array([1, 0, 0], dtype=np.float32),
        top_k=1
    )

    assert len(results) == 1
    assert results[0]["chunk"]["text"] == "Python programming"


def test_remove_document():
    store = VectorStore(3)

    import numpy as np

    embeddings = np.array(
        [
            [1, 0, 0],
            [0, 1, 0]
        ],
        dtype=np.float32
    )

    chunks = [
        {"document_id": "doc1", "text": "Python"},
        {"document_id": "doc2", "text": "DBMS"}
    ]

    store.add_embeddings(embeddings, chunks)

    removed = store.remove_document("doc1")

    assert removed == 1
    assert store.index.ntotal == 1
    assert len(store.metadata) == 1


def test_empty_search():
    store = VectorStore(3)

    import numpy as np

    results = store.search(
        np.array([1, 0, 0], dtype=np.float32)
    )

    assert results == []


def test_invalid_embedding_dimension():
    store = VectorStore(3)

    import numpy as np

    with pytest.raises(ValueError):
        store.add_embeddings(
            np.array([[1, 0]], dtype=np.float32),
            [{"document_id": "doc1", "text": "Python"}]
        )
