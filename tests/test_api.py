from backend.api import pyq_routes
from backend.api import chat_routes
from fastapi.testclient import TestClient

from backend.main import app
from backend.api import document_routes


client = TestClient(app)


def test_document_api_workflow(tmp_path, monkeypatch):
    # Use temporary folders instead of real project storage.
    upload_dir = tmp_path / "uploads"
    processed_dir = tmp_path / "processed"

    monkeypatch.setattr(
        document_routes, "UPLOAD_DIR", upload_dir
    )
    monkeypatch.setattr(
        document_routes, "PROCESSED_DIR", processed_dir
    )

    # Use temporary in-memory metadata storage.
    documents = {}
    indexing_calls = []
    vector_deletion_calls = []

    def fake_save_document(metadata):
        record = metadata.copy()
        record["uploaded_at"] = "2026-11-21 10:00:00"
        documents[metadata["document_id"]] = record

    def fake_get_document_by_id(document_id):
        return documents.get(document_id)

    def fake_get_all_documents(user_id=None):
        return list(documents.values())

    def fake_delete_document(document_id):
        return documents.pop(document_id, None) is not None

    # Mock document indexing.
    def fake_index_document(extracted_document, document_id):
        indexing_calls.append({
            "document_id": document_id,
            "filename": extracted_document["filename"]
        })

        return {
            "document_id": document_id,
            "filename": extracted_document["filename"],
            "total_chunks": 2,
            "total_vectors": 2,
            "previous_vectors_removed": 0,
            "index_saved": True
        }

    # Mock FAISS vector deletion.
    def fake_remove_document_vectors(document_id):
        vector_deletion_calls.append(document_id)
        return 2

    monkeypatch.setattr(
        document_routes, "save_document", fake_save_document
    )
    monkeypatch.setattr(
        document_routes, "get_document_by_id",
        fake_get_document_by_id
    )
    monkeypatch.setattr(
        document_routes, "get_all_documents",
        fake_get_all_documents
    )
    monkeypatch.setattr(
        document_routes, "delete_document",
        fake_delete_document
    )
    monkeypatch.setattr(
        document_routes, "index_document",
        fake_index_document
    )
    monkeypatch.setattr(
        document_routes, "remove_document_vectors",
        fake_remove_document_vectors
    )

    # 1. Upload a TXT document.
    response = client.post(
        "/api/documents/upload",
        files={
            "file": (
                "notes.txt",
                b"Machine Learning is a branch of AI.",
                "text/plain"
            )
        }
    )

    assert response.status_code == 200

    document_id = response.json()["document_id"]

    assert response.json()["original_filename"] == "notes.txt"
    assert "Machine Learning" in response.json()["text_preview"]
    assert "indexed successfully" in response.json()["message"]

    # 2. Verify indexing was triggered.
    assert len(indexing_calls) == 1
    assert indexing_calls[0]["document_id"] == document_id
    assert indexing_calls[0]["filename"] == "notes.txt"

    # 3. Verify original and processed files exist.
    assert len(list(upload_dir.iterdir())) == 1
    assert len(list(processed_dir.iterdir())) == 1

    # 4. List uploaded documents.
    response = client.get("/api/documents/")

    assert response.status_code == 200
    assert len(response.json()) == 1

    # 5. Retrieve document by ID.
    response = client.get(
        f"/api/documents/{document_id}"
    )

    assert response.status_code == 200
    assert response.json()["document_id"] == document_id

    # 6. Delete document.
    response = client.delete(
        f"/api/documents/{document_id}"
    )

    assert response.status_code == 200
    assert response.json()["files_deleted"] is True
    assert response.json()["vectors_deleted"] == 2

    # 7. Verify vector deletion was triggered.
    assert vector_deletion_calls == [document_id]

    # 8. Verify files and metadata are deleted.
    assert len(list(upload_dir.iterdir())) == 0
    assert len(list(processed_dir.iterdir())) == 0
    assert len(documents) == 0


def test_document_not_found():
    response = client.get(
        "/api/documents/non-existing-id"
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Document not found."


def test_normal_chat_api(monkeypatch):
    """Normal chat should use Gemini directly."""

    def fake_generate_response(prompt, system_instruction=None):
        assert prompt == "Explain Python."
        assert system_instruction == "Keep it simple."
        return "Python is a programming language."

    monkeypatch.setattr(
        chat_routes, "generate_response", fake_generate_response
    )

    response = client.post(
        "/api/chat",
        json={
            "prompt": "Explain Python.",
            "system_instruction": "Keep it simple.",
            "use_documents": False
        }
    )

    assert response.status_code == 200
    assert response.json()["response"] == (
        "Python is a programming language."
    )
    assert response.json()["sources"] == []


def test_rag_chat_api(monkeypatch):
    """Document chat should use the RAG service."""

    def fake_generate_rag_response(question):
        assert question == "Explain normalization."

        return {
            "answer": "Normalization reduces data redundancy.",
            "sources": []
        }

    monkeypatch.setattr(
        chat_routes, "generate_rag_response",
        fake_generate_rag_response
    )

    response = client.post(
        "/api/chat",
        json={
            "prompt": "Explain normalization.",
            "use_documents": True
        }
    )

    assert response.status_code == 200
    assert response.json()["response"] == (
        "Normalization reduces data redundancy."
    )
    assert response.json()["sources"] == []


def test_rag_chat_returns_sources(monkeypatch):
    """RAG chat should return document source information."""

    def fake_generate_rag_response(question):
        return {
            "answer": "A class is a blueprint for creating objects.",
            "sources": [
                {
                    "filename": "Python_Notes.pdf",
                    "page_number": 5,
                    "slide_number": None,
                    "similarity": 0.89
                }
            ]
        }

    monkeypatch.setattr(
        chat_routes, "generate_rag_response",
        fake_generate_rag_response
    )

    response = client.post(
        "/api/chat",
        json={
            "prompt": "What is a class?",
            "use_documents": True
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert data["response"] == (
        "A class is a blueprint for creating objects."
    )

    assert len(data["sources"]) == 1
    assert data["sources"][0]["filename"] == "Python_Notes.pdf"
    assert data["sources"][0]["page_number"] == 5
    assert data["sources"][0]["similarity"] == 0.89


def test_pyq_upload_api(monkeypatch, tmp_path):
    """PYQ upload should process and save extracted questions."""

    upload_dir = tmp_path / "pyq_uploads"

    monkeypatch.setattr(
        pyq_routes, "PYQ_UPLOAD_DIR", upload_dir
    )

    def fake_process_and_save_pyq(
        file_path, subject, exam_year, original_filename=None
    ):
        assert file_path.exists()
        assert subject == "DBMS"
        assert exam_year == 2024
        assert original_filename == "DBMS_2024.pdf"

        return {
            "filename": original_filename,
            "subject": subject,
            "exam_year": exam_year,
            "total_questions": 4,
            "saved_questions": 4,
            "message": "4 questions extracted and saved successfully."
        }

    monkeypatch.setattr(
        pyq_routes,
        "process_and_save_pyq",
        fake_process_and_save_pyq
    )

    response = client.post(
        "/api/pyq/upload?subject=DBMS&exam_year=2024",
        files={
            "file": (
                "DBMS_2024.pdf",
                b"%PDF-1.4 test content",
                "application/pdf"
            )
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert data["filename"] == "DBMS_2024.pdf"
    assert data["subject"] == "DBMS"
    assert data["exam_year"] == 2024
    assert data["total_questions"] == 4

    # Temporary uploaded file should be deleted.
    assert list(upload_dir.iterdir()) == []


def test_pyq_upload_rejects_invalid_file():
    """PYQ upload should reject unsupported file types."""

    response = client.post(
        "/api/pyq/upload?subject=DBMS&exam_year=2024",
        files={
            "file": (
                "notes.txt",
                b"Some question paper text",
                "text/plain"
            )
        }
    )

    assert response.status_code == 400
    assert "PDF files only" in response.json()["detail"]


def test_list_pyq_questions(monkeypatch):
    """Questions should be returned with subject and year filters."""

    expected_questions = [
        {
            "question_id": "test-id-1",
            "subject": "DBMS",
            "exam_year": 2024,
            "question_text": "Explain database normalization.",
            "topic": "Normalization",
            "marks": 5,
            "source_filename": "DBMS_2024.pdf"
        }
    ]

    def fake_get_all_questions(subject=None, exam_year=None, topic=None):
        assert subject == "DBMS"
        assert exam_year == 2024
        assert topic is None
        return expected_questions

    monkeypatch.setattr(
        pyq_routes,
        "get_all_questions",
        fake_get_all_questions
    )

    response = client.get(
        "/api/pyq/questions?subject=DBMS&exam_year=2024"
    )

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["topic"] == "Normalization"


def test_pyq_analytics(monkeypatch):
    """Analytics should calculate topic-wise and year-wise counts."""

    questions = [
        {"topic": "Normalization", "exam_year": 2024},
        {"topic": "Normalization", "exam_year": 2024},
        {"topic": "SQL Commands", "exam_year": 2023},
        {"topic": None, "exam_year": 2023}
    ]

    def fake_get_all_questions(subject=None, exam_year=None):
        assert subject == "DBMS"
        return questions

    monkeypatch.setattr(
        pyq_routes,
        "get_all_questions",
        fake_get_all_questions
    )

    response = client.get(
        "/api/pyq/analytics?subject=DBMS"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total_questions"] == 4
    assert data["topic_wise"] == {
        "Normalization": 2,
        "SQL Commands": 1,
        "Uncategorized": 1
    }
    assert data["year_wise"] == {
        "2024": 2,
        "2023": 2
    }


def test_delete_pyq_question(monkeypatch):
    """An existing PYQ question should be deleted successfully."""

    deleted_ids = []

    def fake_delete_question(question_id):
        deleted_ids.append(question_id)
        return True

    monkeypatch.setattr(
        pyq_routes,
        "delete_question",
        fake_delete_question
    )

    response = client.delete(
        "/api/pyq/questions/test-question-id"
    )

    assert response.status_code == 200
    assert response.json()["message"] == (
        "PYQ question deleted successfully."
    )
    assert deleted_ids == ["test-question-id"]


def test_delete_non_existing_pyq_question(monkeypatch):
    """Deleting a missing question should return 404."""

    monkeypatch.setattr(
        pyq_routes,
        "delete_question",
        lambda question_id: False
    )

    response = client.delete(
        "/api/pyq/questions/non-existing-id"
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "PYQ question not found."