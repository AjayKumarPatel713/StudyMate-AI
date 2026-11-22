
from fastapi import APIRouter, HTTPException
from google.genai import errors

from backend.config import settings
from backend.schemas.chat_schema import (
    ChatRequest,
    ChatResponse
)
from backend.services.llm_service import generate_response
from backend.services.rag_service import generate_rag_response


router = APIRouter(
    prefix="/api",
    tags=["Chat"]
)


@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    """
    Generate a response using normal Gemini chat or document-based RAG.
    """

    try:
        if request.use_documents:
            rag_result = generate_rag_response(
                question=request.prompt
            )

            return ChatResponse(
                response=rag_result["answer"],
                model=settings.GEMINI_MODEL,
                sources=rag_result["sources"]
            )

        answer = generate_response(
            prompt=request.prompt,
            system_instruction=request.system_instruction
        )

        return ChatResponse(
            response=answer,
            model=settings.GEMINI_MODEL
        )

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error)
        )

    except errors.APIError as error:

        # Temporary upstream errors: 429, 500, 502, 503, 504
        if error.code in (429, 500, 502, 503, 504):
            raise HTTPException(
                status_code=503,
                detail="Gemini is temporarily unavailable. Please try again later."
            )

        raise HTTPException(
            status_code=502,
            detail=f"Gemini API request failed (HTTP {error.code})."
        )

    except Exception:
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred while generating the response."
        )
