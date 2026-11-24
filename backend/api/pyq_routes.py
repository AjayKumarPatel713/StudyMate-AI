
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, File, HTTPException, Query, UploadFile

from backend.database.repository import (
    get_all_questions,
    delete_question
)
from backend.schemas.pyq_schema import (
    PYQQuestionResponse,
    PYQUploadResponse
)
from backend.services.pyq_service import process_and_save_pyq
from backend.utils.file_validator import (
    MAX_FILE_SIZE,
    validate_file,
    validate_file_content
)


router = APIRouter(
    prefix="/api/pyq",
    tags=["PYQ Analyzer"]
)

BASE_DIR = Path(__file__).resolve().parents[2]
PYQ_UPLOAD_DIR = BASE_DIR / "data" / "pyq" / "uploads"


@router.post(
    "/upload",
    response_model=PYQUploadResponse
)
async def upload_pyq(
    subject: str = Query(..., min_length=1, max_length=100),
    exam_year: int = Query(..., ge=1900, le=2100),
    file: UploadFile = File(...)
):
    """
    Upload a previous-year question paper,
    extract questions using Gemini and save them in SQLite.
    """

    upload_path = None

    try:
        if not file.filename:
            raise HTTPException(
                status_code=400,
                detail="Filename cannot be empty."
            )

        original_filename = Path(
            file.filename.replace("\\", "/")
        ).name

        if Path(original_filename).suffix.lower() != ".pdf":
            raise HTTPException(
                status_code=400,
                detail="PYQ Analyzer currently supports PDF files only."
            )

        content = await file.read(MAX_FILE_SIZE + 1)

        try:
            validate_file(original_filename, len(content))
            validate_file_content(original_filename, content)

        except ValueError as error:
            raise HTTPException(
                status_code=400,
                detail=str(error)
            ) from error

        PYQ_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

        stored_filename = f"{uuid4()}.pdf"
        upload_path = PYQ_UPLOAD_DIR / stored_filename

        upload_path.write_bytes(content)

        result = process_and_save_pyq(
            file_path=upload_path,
            subject=subject,
            exam_year=exam_year,
            original_filename=original_filename
        )

        return PYQUploadResponse(
            filename=result["filename"],
            subject=result["subject"],
            exam_year=result["exam_year"],
            total_questions=result["total_questions"],
            message=result["message"]
        )

    except HTTPException:
        raise

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error)
        ) from error

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred while processing the PYQ paper."
        ) from error

    finally:
        if upload_path and upload_path.exists():
            upload_path.unlink()

        await file.close()


@router.get(
    "/questions",
    response_model=list[PYQQuestionResponse]
)
def list_pyq_questions(
    subject: str | None = Query(default=None, max_length=100),
    exam_year: int | None = Query(default=None, ge=1900, le=2100),
    topic: str | None = Query(default=None, max_length=100)
):
    """
    Retrieve PYQ questions with optional subject, year and topic filters.
    """

    return get_all_questions(
        subject=subject,
        exam_year=exam_year,
        topic=topic
    )

@router.get("/analytics")
def get_pyq_analytics(
    subject: str | None = Query(default=None, max_length=100)
):
    """
    Return question counts grouped by topic and examination year.
    """

    questions = get_all_questions(subject=subject)

    topic_counts = {}
    year_counts = {}

    for question in questions:
        topic = question["topic"] or "Uncategorized"
        year = str(question["exam_year"])

        topic_counts[topic] = topic_counts.get(topic, 0) + 1
        year_counts[year] = year_counts.get(year, 0) + 1

    return {
        "subject": subject,
        "total_questions": len(questions),
        "topic_wise": topic_counts,
        "year_wise": year_counts
    }


@router.delete("/questions/{question_id}")
def remove_pyq_question(question_id: str):
    """
    Delete one saved PYQ question.
    """

    deleted = delete_question(question_id)

    if not deleted:
        raise HTTPException(
            status_code=404,
            detail="PYQ question not found."
        )

    return {
        "message": "PYQ question deleted successfully.",
        "question_id": question_id
    }
