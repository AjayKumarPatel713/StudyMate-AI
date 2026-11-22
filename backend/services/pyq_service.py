
import json
import re
from pathlib import Path

from backend.services.document_service import extract_document
from backend.services.llm_service import generate_response


MAX_BATCH_CHARS = 8000


def _create_page_batches(segments: list[dict]) -> list[str]:
    """Group extracted pages into manageable text batches."""

    batches = []
    current_pages = []
    current_size = 0

    for segment in segments:
        page_number = segment.get("page_number")
        page_text = segment["text"].strip()

        if not page_text:
            continue

        page_content = (
            f"\n--- Page {page_number} ---\n{page_text}"
        )

        if current_pages and current_size + len(page_content) > MAX_BATCH_CHARS:
            batches.append("\n".join(current_pages))
            current_pages = []
            current_size = 0

        current_pages.append(page_content)
        current_size += len(page_content)

    if current_pages:
        batches.append("\n".join(current_pages))

    return batches


def _parse_gemini_response(response_text: str) -> list[dict]:
    """Parse and validate the JSON returned by Gemini."""

    if not response_text or not response_text.strip():
        raise ValueError("Gemini returned an empty extraction response.")

    cleaned_text = response_text.strip()

    # Remove Markdown JSON code fences, if present.
    cleaned_text = re.sub(
        r"^```(?:json)?\s*",
        "",
        cleaned_text,
        flags=re.IGNORECASE
    )

    cleaned_text = re.sub(r"\s*```$", "", cleaned_text)

    # Extract the JSON object if Gemini adds extra text.
    start = cleaned_text.find("{")
    end = cleaned_text.rfind("}")

    if start == -1 or end == -1 or end < start:
        raise ValueError("Gemini did not return valid JSON.")

    try:
        data = json.loads(cleaned_text[start:end + 1])
    except json.JSONDecodeError as error:
        raise ValueError(
            "Could not parse the questions returned by Gemini."
        ) from error

    if not isinstance(data, dict):
        raise ValueError("Gemini returned an unexpected JSON structure.")

    questions = data.get("questions")

    if not isinstance(questions, list):
        raise ValueError("Gemini response does not contain a valid questions list.")

    validated_questions = []

    for item in questions:
        if not isinstance(item, dict):
            continue

        question_text = item.get("question_text")

        if not isinstance(question_text, str) or len(question_text.strip()) < 10:
            continue

        topic = item.get("topic")
        marks = item.get("marks")

        if not isinstance(topic, str):
            topic = None
        else:
            topic = topic.strip() or None

        if isinstance(marks, bool) or not isinstance(marks, (int, float)):
            marks = None
        elif marks <= 0 or marks > 100:
            marks = None

        validated_questions.append({
            "question_text": question_text.strip(),
            "topic": topic,
            "marks": marks
        })

    return validated_questions


def _extract_questions_from_batch(batch_text: str) -> list[dict]:
    """Use Gemini to identify questions in one text batch."""

    prompt = f"""
You are an expert university examination question paper analyzer.

Extract every actual examination question from the following
previous-year question paper text.

Paper text:
{batch_text}

Instructions:
1. Extract complete questions, not headings or instructions.
2. Preserve the original wording of each question.
3. Include sub-questions when they are independently answerable.
4. Identify the main academic topic for each question.
5. Extract marks if explicitly mentioned; otherwise use null.
6. Do not invent questions, topics, or marks.
7. Ignore page numbers, headers, footers, and general instructions.
8. Return only valid JSON. Do not include Markdown or explanations.

Required JSON structure:
{{
    "questions": [
        {{
            "question_text": "Explain database normalization with examples.",
            "topic": "Normalization",
            "marks": 5
        }}
    ]
}}

If no questions are found, return:
{{"questions": []}}
"""

    response = generate_response(prompt)

    return _parse_gemini_response(response)


def extract_questions_from_paper(
    file_path: str | Path,
    subject: str,
    exam_year: int,
    original_filename: str | None = None
) -> dict:
    """
    Extract questions from a text-based PDF question paper.

    Returns the extracted questions with paper metadata.
    """

    if not subject or not subject.strip():
        raise ValueError("Subject cannot be empty.")

    if not isinstance(exam_year, int) or not 1900 <= exam_year <= 2100:
        raise ValueError("Exam year must be between 1900 and 2100.")

    filename = original_filename or Path(file_path).name

    if Path(filename).suffix.lower() != ".pdf":
        raise ValueError("PYQ Analyzer currently supports PDF files only.")

    document = extract_document(
        file_path=file_path,
        original_filename=filename
    )

    batches = _create_page_batches(document["segments"])

    if not batches:
        raise ValueError("No readable text found in the question paper.")

    all_questions = []
    seen_questions = set()

    for batch in batches:
        extracted_questions = _extract_questions_from_batch(batch)

        for question in extracted_questions:
            # Avoid saving exact duplicate questions.
            normalized_text = " ".join(
                question["question_text"].lower().split()
            )

            if normalized_text in seen_questions:
                continue

            seen_questions.add(normalized_text)

            all_questions.append({
                **question,
                "subject": subject.strip(),
                "exam_year": exam_year,
                "source_filename": filename
            })

    return {
        "filename": filename,
        "subject": subject.strip(),
        "exam_year": exam_year,
        "total_questions": len(all_questions),
        "questions": all_questions
    }


import uuid

from backend.database.repository import save_question


def process_and_save_pyq(
    file_path: str | Path,
    subject: str,
    exam_year: int,
    original_filename: str | None = None
) -> dict:
    """
    Extract questions from a PYQ paper and save them in SQLite.
    """

    result = extract_questions_from_paper(
        file_path=file_path,
        subject=subject,
        exam_year=exam_year,
        original_filename=original_filename
    )

    saved_count = 0

    for question in result["questions"]:
        question_data = {
            "question_id": str(uuid.uuid4()),
            **question
        }

        save_question(question_data)
        saved_count += 1

    return {
        "filename": result["filename"],
        "subject": result["subject"],
        "exam_year": result["exam_year"],
        "total_questions": result["total_questions"],
        "saved_questions": saved_count,
        "message": f"{saved_count} questions extracted and saved successfully."
    }
