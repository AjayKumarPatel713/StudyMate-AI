
import json
from pathlib import Path

import faiss
import numpy as np


BASE_DIR = Path(__file__).resolve().parents[2]
INDEX_DIR = BASE_DIR / "data" / "vector_indexes"


class VectorStore:
    def __init__(self, dimension: int):
        if dimension <= 0:
            raise ValueError("Embedding dimension must be positive.")

        self.dimension = dimension
        self.index = faiss.IndexIDMap2(
            faiss.IndexFlatIP(dimension)
        )
        self.metadata = {}

    def add_embeddings(
        self,
        embeddings: np.ndarray,
        chunks: list[dict]
    ) -> None:
        embeddings = np.asarray(embeddings, dtype=np.float32)

        if embeddings.ndim != 2:
            raise ValueError("Embeddings must be a 2D array.")

        if embeddings.shape[1] != self.dimension:
            raise ValueError("Embedding dimension mismatch.")

        if len(embeddings) != len(chunks) or not chunks:
            raise ValueError("Embeddings and chunks must match and be non-empty.")

        if not np.isfinite(embeddings).all():
            raise ValueError("Embeddings contain invalid values.")

        norms = np.linalg.norm(embeddings, axis=1)

        if not np.allclose(norms, 1.0, atol=1e-4):
            raise ValueError("Embeddings must be normalized.")

        if not all(isinstance(chunk, dict) for chunk in chunks):
            raise ValueError("Each chunk must be a dictionary.")

        if len(self.metadata) != self.index.ntotal:
            raise ValueError("Vector metadata and index are inconsistent.")

        start_id = max(self.metadata.keys(), default=0) + 1

        vector_ids = np.arange(
            start_id,
            start_id + len(chunks),
            dtype=np.int64
        )

        self.index.add_with_ids(embeddings, vector_ids)

        for vector_id, chunk in zip(vector_ids, chunks):
            self.metadata[int(vector_id)] = chunk

    def remove_document(self, document_id: str) -> int:
        """
        Remove all vectors belonging to a document.
        Returns the number of removed vectors.
        """

        vector_ids = [
            vector_id
            for vector_id, chunk in self.metadata.items()
            if chunk.get("document_id") == document_id
        ]

        if not vector_ids:
            return 0

        ids_to_remove = np.asarray(vector_ids, dtype=np.int64)

        removed_count = self.index.remove_ids(ids_to_remove)

        for vector_id in vector_ids:
            self.metadata.pop(vector_id, None)

        return int(removed_count)

    def search(
        self,
        query_embedding: np.ndarray,
        top_k: int = 5
    ) -> list[dict]:

        query_embedding = np.asarray(
            query_embedding,
            dtype=np.float32
        )

        if query_embedding.shape == (self.dimension,):
            query_embedding = query_embedding.reshape(1, -1)

        if query_embedding.shape != (1, self.dimension):
            raise ValueError("Query embedding has incorrect dimensions.")

        if not np.isfinite(query_embedding).all():
            raise ValueError("Query embedding contains invalid values.")

        norm = np.linalg.norm(query_embedding)

        if not np.isclose(norm, 1.0, atol=1e-4):
            raise ValueError("Query embedding must be normalized.")

        if top_k <= 0:
            raise ValueError("top_k must be positive.")

        if self.index.ntotal == 0:
            return []

        actual_k = min(top_k, self.index.ntotal)

        scores, vector_ids = self.index.search(
            query_embedding,
            actual_k
        )

        results = []

        for score, vector_id in zip(scores[0], vector_ids[0]):
            if vector_id == -1:
                continue

            chunk = self.metadata.get(int(vector_id))

            if chunk is not None:
                results.append({
                    "vector_id": int(vector_id),
                    "similarity": float(score),
                    "chunk": chunk
                })

        return results

    def save(self, name: str) -> None:
        if not name or Path(name).name != name:
            raise ValueError("Invalid index name.")

        INDEX_DIR.mkdir(parents=True, exist_ok=True)

        index_path = INDEX_DIR / f"{name}.faiss"
        metadata_path = INDEX_DIR / f"{name}.json"

        temp_index_path = INDEX_DIR / f"{name}.tmp.faiss"
        temp_metadata_path = INDEX_DIR / f"{name}.tmp.json"

        try:
            faiss.write_index(self.index, str(temp_index_path))

            with temp_metadata_path.open("w", encoding="utf-8") as file:
                json.dump(self.metadata, file, ensure_ascii=False)

            temp_index_path.replace(index_path)
            temp_metadata_path.replace(metadata_path)

        finally:
            if temp_index_path.exists():
                temp_index_path.unlink()

            if temp_metadata_path.exists():
                temp_metadata_path.unlink()

    @classmethod
    def load(cls, name: str):
        if not name or Path(name).name != name:
            raise ValueError("Invalid index name.")

        index_path = INDEX_DIR / f"{name}.faiss"
        metadata_path = INDEX_DIR / f"{name}.json"

        if not index_path.exists() or not metadata_path.exists():
            raise FileNotFoundError("Saved vector index was not found.")

        index = faiss.read_index(str(index_path))

        if not isinstance(index, faiss.IndexIDMap2):
            raise ValueError("Invalid FAISS index type.")

        with metadata_path.open("r", encoding="utf-8") as file:
            metadata = json.load(file)

        store = cls(index.d)

        store.index = index
        store.metadata = {
            int(vector_id): chunk
            for vector_id, chunk in metadata.items()
        }

        if len(store.metadata) != store.index.ntotal:
            raise ValueError(
                "Saved vector index and metadata are inconsistent."
            )

        return store
