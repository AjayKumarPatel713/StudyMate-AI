
from pydantic import BaseModel, Field


class DocumentUploadResponse(BaseModel):
    document_id: str = Field(..., description="Unique document ID")

    original_filename: str
    file_type: str
    file_size: int

    total_pages: int | None = None
    total_slides: int | None = None

    segment_count: int

    extraction_status: str = "success"

    text_preview: str = Field(
        ...,
        description="Preview of the extracted document text"
    )

    message: str = "Document uploaded and processed successfully."


class DocumentMetadataResponse(BaseModel):
    document_id: str
    original_filename: str
    stored_filename: str
    file_type: str
    file_size: int
    uploaded_at: str
    total_pages: int | None = None
    total_slides: int | None = None
    segment_count: int
    extraction_status: str
