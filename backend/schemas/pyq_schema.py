
from pydantic import BaseModel, Field


class PYQQuestionCreate(BaseModel):
    """Data required to save an extracted PYQ question."""

    subject: str = Field(
        ...,
        min_length=1,
        max_length=100
    )

    exam_year: int = Field(
        ...,
        ge=1900,
        le=2100
    )

    question_text: str = Field(
        ...,
        min_length=10,
        max_length=5000
    )

    topic: str | None = Field(
        default=None,
        max_length=200
    )

    marks: float | None = Field(
        default=None,
        gt=0,
        le=100
    )

    source_filename: str = Field(
        ...,
        min_length=1,
        max_length=255
    )


class PYQQuestionResponse(BaseModel):
    """Question data returned by the API."""

    question_id: str
    subject: str
    exam_year: int
    question_text: str
    topic: str | None = None
    marks: float | None = None
    source_filename: str


class PYQUploadResponse(BaseModel):
    """Response returned after processing a PYQ paper."""

    filename: str
    subject: str
    exam_year: int
    total_questions: int
    message: str
