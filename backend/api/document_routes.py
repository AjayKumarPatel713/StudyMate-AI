
import json
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, File, HTTPException, UploadFile

from backend.database.repository import (
    save_document,
    get_document_by_id,
    get_all_documents,
    delete_document
)
from backend.schemas.document_schema import (
    DocumentUploadResponse,
    DocumentMetadataResponse
)
from backend.services.document_service import extract_document
from backend.services.indexing_service import index_document
from backend.services.vector_service import VectorStore, INDEX_DIR
from backend.utils.file_validator import (
    MAX_FILE_SIZE,
    validate_file,
    validate_file_content
)


router = APIRouter(
    prefix="/api/documents",
    tags=["Documents"]
)

BASE_DIR = Path(__file__).resolve().parents[2]

UPLOAD_DIR = BASE_DIR / "data" / "uploads"
PROCESSED_DIR = BASE_DIR / "data" / "processed"


def remove_document_vectors(document_id: str) -> int:
    """
    Remove all FAISS vectors belonging to a document.
    """

    index_path = INDEX_DIR / "studymate_index.faiss"
    metadata_path = INDEX_DIR / "studymate_index.json"

    if not index_path.exists() and not metadata_path.exists():
        return 0

    if not index_path.exists() or not metadata_path.exists():
        raise RuntimeError("FAISS index files are incomplete.")

    vector_store = VectorStore.load("studymate_index")

    removed_count = vector_store.remove_document(document_id)

    if removed_count > 0:
        vector_store.save("studymate_index")

    return removed_count


@router.post(
    "/upload",
    response_model=DocumentUploadResponse
)
async def upload_document(file: UploadFile = File(...)):
    """
    Upload, extract, index and save a document.
    """

    upload_path = None
    processed_path = None
    indexing_started = False
    document_id = None

    try:
        if not file.filename:
            raise HTTPException(
                status_code=400,
                detail="Filename cannot be empty."
            )

        original_filename = Path(
            file.filename.replace("\\", "/")
        ).name

        content = await file.read(MAX_FILE_SIZE + 1)

        try:
            validate_file(original_filename, len(content))
            validate_file_content(original_filename, content)

        except ValueError as error:
            raise HTTPException(
                status_code=400,
                detail=str(error)
            ) from error

        UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
        PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

        document_id = str(uuid4())

        extension = Path(original_filename).suffix.lower()
        stored_filename = f"{document_id}{extension}"

        upload_path = UPLOAD_DIR / stored_filename
        processed_path = PROCESSED_DIR / f"{document_id}.json"

        upload_path.write_bytes(content)

        try:
            extracted_data = extract_document(
                upload_path,
                original_filename=original_filename
            )
        except Exception as error:
            raise HTTPException(
                status_code=400,
                detail=f"Unable to process document: {error}"
            ) from error

        segments = extracted_data["segments"]

        with processed_path.open("w", encoding="utf-8") as json_file:
            json.dump(
                extracted_data,
                json_file,
                ensure_ascii=False,
                indent=4
            )

        # Step 1: Create chunks, embeddings and FAISS vectors.
        indexing_started = True

        indexing_result = index_document(
            extracted_document=extracted_data,
            document_id=document_id
        )

        # Step 2: Save document metadata.
        metadata = {
            "document_id": document_id,
            "user_id": None,
            "original_filename": original_filename,
            "stored_filename": stored_filename,
            "file_type": extracted_data["file_type"],
            "file_size": len(content),
            "total_pages": extracted_data["total_pages"],
            "total_slides": extracted_data["total_slides"],
            "segment_count": len(segments),
            "extraction_status": "success"
        }

        save_document(metadata)

        full_text = "\n".join(
            segment["text"] for segment in segments
        )

        return DocumentUploadResponse(
            document_id=document_id,
            original_filename=original_filename,
            file_type=extracted_data["file_type"],
            file_size=len(content),
            total_pages=extracted_data["total_pages"],
            total_slides=extracted_data["total_slides"],
            segment_count=len(segments),
            extraction_status="success",
            text_preview=full_text[:500],
            message=(
                "Document uploaded, processed and indexed successfully. "
                f"Total chunks: {indexing_result['total_chunks']}."
            )
        )

    except HTTPException:
        if indexing_started and document_id:
            try:
                remove_document_vectors(document_id)
            except Exception:
                pass

        if upload_path and upload_path.exists():
            upload_path.unlink()

        if processed_path and processed_path.exists():
            processed_path.unlink()

        raise

    except Exception as error:
        if indexing_started and document_id:
            try:
                remove_document_vectors(document_id)
            except Exception:
                pass

        if upload_path and upload_path.exists():
            upload_path.unlink()

        if processed_path and processed_path.exists():
            processed_path.unlink()

        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred while uploading the document."
        ) from error

    finally:
        await file.close()


@router.get(
    "/",
    response_model=list[DocumentMetadataResponse]
)
def list_documents():
    """
    Return metadata for all uploaded documents.
    """

    return get_all_documents()


@router.get(
    "/{document_id}",
    response_model=DocumentMetadataResponse
)
def get_document(document_id: str):
    """
    Return metadata for one document.
    """

    document = get_document_by_id(document_id)

    if document is None:
        raise HTTPException(
            status_code=404,
            detail="Document not found."
        )

    return document


@router.delete("/{document_id}")
def remove_document(document_id: str):
    """
    Delete a document's database record, vectors and stored files.
    """

    document = get_document_by_id(document_id)

    if document is None:
        raise HTTPException(
            status_code=404,
            detail="Document not found."
        )

    stored_filename = document["stored_filename"]

    upload_path = UPLOAD_DIR / stored_filename
    processed_path = PROCESSED_DIR / f"{document_id}.json"

    # Step 1: Delete the database record.
    deleted = delete_document(document_id)

    if not deleted:
        raise HTTPException(
            status_code=500,
            detail="Unable to delete document metadata."
        )

    # Step 2: Remove vectors from FAISS.
    try:
        removed_vectors = remove_document_vectors(document_id)
    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail="Document metadata deleted, but vector cleanup failed."
        ) from error

    # Step 3: Remove original and processed files.
    if upload_path.exists():
        upload_path.unlink()

    if processed_path.exists():
        processed_path.unlink()

    return {
        "message": "Document deleted successfully.",
        "document_id": document_id,
        "vectors_deleted": removed_vectors,
        "files_deleted": True
    }
