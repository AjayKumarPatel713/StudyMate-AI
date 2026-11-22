
CREATE_DOCUMENTS_TABLE = """
CREATE TABLE IF NOT EXISTS documents (
    document_id TEXT PRIMARY KEY,
    user_id TEXT,

    original_filename TEXT NOT NULL,
    stored_filename TEXT NOT NULL UNIQUE,

    file_type TEXT NOT NULL,
    file_size INTEGER NOT NULL,

    uploaded_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

    total_pages INTEGER,
    total_slides INTEGER,
    segment_count INTEGER NOT NULL DEFAULT 0,

    extraction_status TEXT NOT NULL DEFAULT 'success'
);
"""


CREATE_PYQ_QUESTIONS_TABLE = """
CREATE TABLE IF NOT EXISTS pyq_questions (
    question_id TEXT PRIMARY KEY,

    subject TEXT NOT NULL,
    exam_year INTEGER NOT NULL,

    question_text TEXT NOT NULL,
    topic TEXT,

    marks REAL,

    source_filename TEXT NOT NULL,

    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
"""

