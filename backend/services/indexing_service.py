
from backend.rag.chunking import create_document_chunks
from backend.services.embedding_service import (
    generate_embeddings,
    get_embedding_dimension
)
from backend.services.vector_service import VectorStore, INDEX_DIR


INDEX_NAME = "studymate_index"


def index_document(
    extracted_document: dict,
    document_id: str
) -> dict:
    """
    Add a document to the shared FAISS index.

    If the document was already indexed, replace its old vectors.
    """

    if not document_id:
        raise ValueError("Document ID cannot be empty.")

    # Step 1: Create chunks
    chunks = create_document_chunks(
        extracted_document=extracted_document,
        document_id=document_id
    )

    if not chunks:
        raise ValueError("No text chunks found in the document.")

    # Step 2: Generate embeddings before changing the index
    texts = [chunk["text"] for chunk in chunks]
    embeddings = generate_embeddings(texts)

    # Step 3: Load existing index or create a new one
    index_path = INDEX_DIR / f"{INDEX_NAME}.faiss"
    metadata_path = INDEX_DIR / f"{INDEX_NAME}.json"

    if index_path.exists() and metadata_path.exists():
        vector_store = VectorStore.load(INDEX_NAME)

    elif index_path.exists() or metadata_path.exists():
        raise ValueError(
            "FAISS index files are incomplete. "
            "Please check the vector index directory."
        )

    else:
        vector_store = VectorStore(
            dimension=get_embedding_dimension()
        )

    # Step 4: Remove old vectors for this document
    removed_vectors = vector_store.remove_document(document_id)

    # Step 5: Add new vectors
    vector_store.add_embeddings(
        embeddings=embeddings,
        chunks=chunks
    )

    # Step 6: Save the updated shared index
    vector_store.save(INDEX_NAME)

    return {
        "document_id": document_id,
        "filename": extracted_document["filename"],
        "total_chunks": len(chunks),
        "total_vectors": vector_store.index.ntotal,
        "previous_vectors_removed": removed_vectors,
        "index_saved": True
    }
