
from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    prompt: str = Field(
        ...,
        min_length=1,
        max_length=10000,
        description="Question asked by the student"
    )

    system_instruction: str | None = Field(
        default=None,
        max_length=2000
    )

    use_documents: bool = Field(
        default=False,
        description="Whether to use uploaded documents for RAG"
    )


class SourceReference(BaseModel):
    filename: str
    page_number: int | None = None
    slide_number: int | None = None
    similarity: float | None = None


class ChatResponse(BaseModel):
    response: str
    model: str
    status: str = "success"
    sources: list[SourceReference] = Field(default_factory=list)
