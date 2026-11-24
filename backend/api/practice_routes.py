
from pydantic import BaseModel, Field
from fastapi import APIRouter, HTTPException, Query

from backend.database.repository import (
    get_all_questions,
    create_practice_session,
    save_practice_answer,
    get_practice_session,
    update_practice_session_status,
    get_practice_history
)


router = APIRouter(
    prefix="/api/practice",
    tags=["PYQ Practice Mode"]
)


class PracticeAnswerRequest(BaseModel):
    question_id: str
    selected_answer: str = Field(min_length=1, max_length=5000)


@router.post("/start")
def start_practice_session(
    subject: str | None = Query(default=None, max_length=100),
    exam_year: int | None = Query(default=None, ge=1900, le=2100),
    topic: str | None = Query(default=None, max_length=100)
):
    """
    Start a practice session using optional PYQ filters.
    """

    questions = get_all_questions(
        subject=subject,
        exam_year=exam_year,
        topic=topic
    )

    if not questions:
        raise HTTPException(
            status_code=404,
            detail="No questions found for the selected filters."
        )

    question_ids = [
        question["question_id"]
        for question in questions
    ]

    session_id = create_practice_session(
        subject=subject,
        exam_year=exam_year,
        topic=topic,
        question_ids=question_ids
    )

    return {
        "message": "Practice session started successfully.",
        "session_id": session_id,
        "total_questions": len(question_ids)
    }


@router.get("/history")
def practice_history():
    """
    Retrieve previous practice sessions.
    """

    return get_practice_history()


@router.get("/{session_id}")
def get_practice_details(session_id: str):
    """
    Retrieve a practice session with its questions and saved answers.
    """

    session = get_practice_session(session_id)

    if not session:
        raise HTTPException(
            status_code=404,
            detail="Practice session not found."
        )

    return session


@router.post("/{session_id}/answer")
def submit_practice_answer(
    session_id: str,
    request: PracticeAnswerRequest
):
    """
    Save an answer submitted by the user.
    """

    session = get_practice_session(session_id)

    if not session:
        raise HTTPException(
            status_code=404,
            detail="Practice session not found."
        )

    if session["status"] != "in_progress":
        raise HTTPException(
            status_code=400,
            detail="This practice session is already completed."
        )

    question_exists = any(
        answer["question_id"] == request.question_id
        for answer in session["answers"]
    )

    if not question_exists:
        raise HTTPException(
            status_code=404,
            detail="Question does not belong to this practice session."
        )

    saved = save_practice_answer(
        session_id=session_id,
        question_id=request.question_id,
        selected_answer=request.selected_answer
    )

    if not saved:
        raise HTTPException(
            status_code=500,
            detail="Could not save the answer."
        )

    return {
        "message": "Answer saved successfully.",
        "question_id": request.question_id
    }


@router.post("/{session_id}/complete")
def complete_practice_session(session_id: str):
    """
    Mark a practice session as completed.
    """

    session = get_practice_session(session_id)

    if not session:
        raise HTTPException(
            status_code=404,
            detail="Practice session not found."
        )

    if session["status"] == "completed":
        raise HTTPException(
            status_code=400,
            detail="This practice session is already completed."
        )

    update_practice_session_status(
        session_id=session_id,
        status="completed"
    )

    return {
        "message": "Practice session completed successfully.",
        "session_id": session_id
    }

