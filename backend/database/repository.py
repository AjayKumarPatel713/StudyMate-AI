
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
    exam_year: int | None = None
) -> list[dict]:
    """
    Retrieve all PYQ questions, optionally filtered by subject and year.
    """

    connection = get_connection()

    try:
        query = "SELECT * FROM pyq_questions WHERE 1=1"
        parameters = []

        if subject is not None:
            query += " AND subject = ?"
            parameters.append(subject)

        if exam_year is not None:
            query += " AND exam_year = ?"
            parameters.append(exam_year)

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
