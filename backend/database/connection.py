
import sqlite3
from pathlib import Path

from backend.database.models import (
    CREATE_DOCUMENTS_TABLE,
    CREATE_PYQ_QUESTIONS_TABLE,
    CREATE_PRACTICE_SESSIONS_TABLE,
    CREATE_PRACTICE_ANSWERS_TABLE
)


BASE_DIR = Path(__file__).resolve().parents[2]

DATABASE_PATH = BASE_DIR / "data" / "studymate.db"


def get_connection() -> sqlite3.Connection:
    """
    Create and return a connection to the StudyMate SQLite database.
    """

    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(
        DATABASE_PATH,
        timeout=10
    )

    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")

    return connection


def initialize_database() -> None:
    """
    Create the required database tables if they do not exist.
    """

    connection = get_connection()

    try:
        connection.execute(CREATE_DOCUMENTS_TABLE)
        connection.execute(CREATE_PYQ_QUESTIONS_TABLE)
        connection.execute(CREATE_PRACTICE_SESSIONS_TABLE)
        connection.execute(CREATE_PRACTICE_ANSWERS_TABLE)

        connection.commit()

    finally:
        connection.close()
