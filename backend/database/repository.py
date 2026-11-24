
from backend.database.connection import get_connection


def save_document(metadata: dict) -> None:
    """
    Save document metadata in the SQLite database.
    """

    connection = get_connection()

    try:
        connection.execute(
            """
            INSERT INTO documents (
                document_id,
                user_id,
                original_filename,
                stored_filename,
                file_type,
                file_size,
                total_pages,
                total_slides,
                segment_count,
                extraction_status
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                metadata["document_id"],
                metadata.get("user_id"),
                metadata["original_filename"],
                metadata["stored_filename"],
                metadata["file_type"],
                metadata["file_size"],
                metadata.get("total_pages"),
                metadata.get("total_slides"),
                metadata.get("segment_count", 0),
                metadata.get("extraction_status", "success")
            )
        )

        connection.commit()

    finally:
        connection.close()


def get_document_by_id(document_id: str) -> dict | None:
    """
    Retrieve one document using its unique ID.
    """

    connection = get_connection()

    try:
        row = connection.execute(
            "SELECT * FROM documents WHERE document_id = ?",
            (document_id,)
        ).fetchone()

        return dict(row) if row else None

    finally:
        connection.close()


def get_all_documents(user_id: str | None = None) -> list[dict]:
    """
    Retrieve all documents or documents belonging to one user.
    """

    connection = get_connection()

    try:
        if user_id is None:
            rows = connection.execute(
                "SELECT * FROM documents ORDER BY uploaded_at DESC"
            ).fetchall()
        else:
            rows = connection.execute(
                """
                SELECT * FROM documents
                WHERE user_id = ?
                ORDER BY uploaded_at DESC
                """,
                (user_id,)
            ).fetchall()

        return [dict(row) for row in rows]

    finally:
        connection.close()


def delete_document(document_id: str) -> bool:
    """
    Delete document metadata using its unique ID.

    Returns True if a record was deleted, otherwise False.
    """

    connection = get_connection()

    try:
        cursor = connection.execute(
            "DELETE FROM documents WHERE document_id = ?",
            (document_id,)
        )

        connection.commit()

        return cursor.rowcount > 0

    finally:
        connection.close()



def save_question(question: dict) -> None:
    """
    Save one PYQ question in the database.
    """

    connection = get_connection()

    try:
        connection.execute(
            """
            INSERT INTO pyq_questions (
                question_id,
                subject,
                exam_year,
                question_text,
                topic,
                marks,
                source_filename
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                question["question_id"],
                question["subject"],
                question["exam_year"],
                question["question_text"],
                question.get("topic"),
                question.get("marks"),
                question["source_filename"]
            )
        )

        connection.commit()

    finally:
        connection.close()


def get_question_by_id(question_id: str) -> dict | None:
    """
    Retrieve one PYQ question using its unique ID.
    """

    connection = get_connection()

    try:
        row = connection.execute(
            "SELECT * FROM pyq_questions WHERE question_id = ?",
            (question_id,)
        ).fetchone()

        return dict(row) if row else None

    finally:
        connection.close()



def get_all_questions(
    subject: str | None = None,
    exam_year: int | None = None,
    topic: str | None = None
) -> list[dict]:
    """
    Retrieve PYQ questions with optional subject, year and topic filters.
    """

    connection = get_connection()

    try:
        query = "SELECT * FROM pyq_questions WHERE 1=1"
        parameters = []

        if subject:
            query += " AND subject = ?"
            parameters.append(subject.strip())

        if exam_year is not None:
            query += " AND exam_year = ?"
            parameters.append(exam_year)

        if topic:
            query += " AND LOWER(topic) = LOWER(?)"
            parameters.append(topic.strip())

        query += " ORDER BY exam_year DESC, created_at DESC"

        rows = connection.execute(
            query,
            parameters
        ).fetchall()

        return [dict(row) for row in rows]

    finally:
        connection.close()



def delete_question(question_id: str) -> bool:
    """
    Delete a PYQ question using its unique ID.
    """

    connection = get_connection()

    try:
        cursor = connection.execute(
            "DELETE FROM pyq_questions WHERE question_id = ?",
            (question_id,)
        )

        connection.commit()

        return cursor.rowcount > 0

    finally:
        connection.close()


def get_questions_by_topic(
    subject: str,
    topic: str
) -> list[dict]:
    """
    Retrieve questions belonging to a particular subject and topic.
    """

    connection = get_connection()

    try:
        rows = connection.execute(
            """
            SELECT * FROM pyq_questions
            WHERE subject = ? AND topic = ?
            ORDER BY exam_year DESC
            """,
            (subject, topic)
        ).fetchall()

        return [dict(row) for row in rows]

    finally:
        connection.close()



def create_practice_session(
    subject: str | None,
    exam_year: int | None,
    topic: str | None,
    question_ids: list[str]
) -> str:
    """
    Create a practice session and initialize its question responses.
    Returns the session ID.
    """

    from uuid import uuid4

    session_id = str(uuid4())

    connection = get_connection()

    try:
        connection.execute(
            """
            INSERT INTO practice_sessions (
                session_id,
                subject,
                exam_year,
                topic,
                total_questions
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                session_id,
                subject,
                exam_year,
                topic,
                len(question_ids)
            )
        )

        for question_id in question_ids:
            connection.execute(
                """
                INSERT INTO practice_answers (
                    answer_id,
                    session_id,
                    question_id
                )
                VALUES (?, ?, ?)
                """,
                (
                    str(uuid4()),
                    session_id,
                    question_id
                )
            )

        connection.commit()
        return session_id

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


def save_practice_answer(
    session_id: str,
    question_id: str,
    selected_answer: str
) -> bool:
    """
    Save or update a user's answer to a practice question.
    """

    connection = get_connection()

    try:
        cursor = connection.execute(
            """
            UPDATE practice_answers
            SET selected_answer = ?,
                is_attempted = 1,
                answered_at = CURRENT_TIMESTAMP
            WHERE session_id = ?
              AND question_id = ?
            """,
            (
                selected_answer,
                session_id,
                question_id
            )
        )

        connection.commit()

        return cursor.rowcount > 0

    finally:
        connection.close()


def get_practice_session(session_id: str) -> dict | None:
    """
    Retrieve a practice session along with its questions and answers.
    """

    connection = get_connection()

    try:
        session = connection.execute(
            """
            SELECT *
            FROM practice_sessions
            WHERE session_id = ?
            """,
            (session_id,)
        ).fetchone()

        if not session:
            return None

        answers = connection.execute(
            """
            SELECT
                pa.answer_id,
                pa.question_id,
                pa.selected_answer,
                pa.is_attempted,
                pa.answered_at,
                pq.question_text,
                pq.topic,
                pq.marks
            FROM practice_answers pa
            JOIN pyq_questions pq
                ON pa.question_id = pq.question_id
            WHERE pa.session_id = ?
            """,
            (session_id,)
        ).fetchall()

        result = dict(session)
        result["answers"] = [dict(row) for row in answers]

        return result

    finally:
        connection.close()


def update_practice_session_status(
    session_id: str,
    status: str
) -> bool:
    """
    Update practice session status.
    """

    if status not in ("in_progress", "completed"):
        raise ValueError("Invalid practice session status.")

    connection = get_connection()

    try:
        if status == "completed":
            cursor = connection.execute(
                """
                UPDATE practice_sessions
                SET status = ?,
                    completed_at = CURRENT_TIMESTAMP
                WHERE session_id = ?
                """,
                (status, session_id)
            )
        else:
            cursor = connection.execute(
                """
                UPDATE practice_sessions
                SET status = ?,
                    completed_at = NULL
                WHERE session_id = ?
                """,
                (status, session_id)
            )

        connection.commit()

        return cursor.rowcount > 0

    finally:
        connection.close()


def get_practice_history() -> list[dict]:
    """
    Retrieve all practice sessions, newest first.
    """

    connection = get_connection()

    try:
        rows = connection.execute(
            """
            SELECT *
            FROM practice_sessions
            ORDER BY started_at DESC
            """
        ).fetchall()

        return [dict(row) for row in rows]

    finally:
        connection.close()
