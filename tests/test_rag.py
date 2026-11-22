
import pytest

from backend.services import rag_service


def test_rag_successful_response(monkeypatch):
    """Test successful RAG answer generation."""

    mock_chunks = [
        {
            "similarity": 0.85,
            "chunk": {
                "filename": "dbms_notes.pdf",
                "page_number": 2,
                "slide_number": None,
                "text": "Normalization reduces data redundancy."
            }
        }
    ]

    # Mock document retrieval.
    def mock_retrieve(query, top_k):
        return mock_chunks

    # Mock Gemini response.
    def mock_generate(prompt):
        assert "Normalization reduces data redundancy." in prompt
        assert "Explain normalization." in prompt
        return "Normalization reduces duplicate data."

    monkeypatch.setattr(
        rag_service,
        "retrieve_relevant_chunks",
        mock_retrieve
    )

    monkeypatch.setattr(
        rag_service,
        "generate_response",
        mock_generate
    )

    result = rag_service.generate_rag_response(
        "Explain normalization."
    )

    assert result["answer"] == "Normalization reduces duplicate data."
    assert len(result["sources"]) == 1
    assert result["sources"][0]["filename"] == "dbms_notes.pdf"
    assert result["sources"][0]["page_number"] == 2


def test_rag_no_relevant_chunks(monkeypatch):
    """Test behavior when no relevant chunks are found."""

    monkeypatch.setattr(
        rag_service,
        "retrieve_relevant_chunks",
        lambda query, top_k: []
    )

    # Gemini should not be called.
    def mock_generate(prompt):
        pytest.fail("Gemini should not be called.")

    monkeypatch.setattr(
        rag_service,
        "generate_response",
        mock_generate
    )

    result = rag_service.generate_rag_response(
        "Explain an unknown topic."
    )

    assert result["answer"] == (
    "I could not find sufficiently relevant information "
    "in your uploaded documents."
    )
    assert result["sources"] == []


def test_rag_empty_question():
    """Test validation for an empty question."""

    with pytest.raises(ValueError, match="Question cannot be empty."):
        rag_service.generate_rag_response("")


def test_rag_duplicate_chunks(monkeypatch):
    """Test that duplicate chunks are included only once."""

    duplicate_chunk = {
        "filename": "dbms_notes.pdf",
        "page_number": 1,
        "slide_number": None,
        "text": "Normalization reduces redundancy."
    }

    mock_chunks = [
        {"similarity": 0.90, "chunk": duplicate_chunk},
        {"similarity": 0.85, "chunk": duplicate_chunk}
    ]

    monkeypatch.setattr(
        rag_service,
        "retrieve_relevant_chunks",
        lambda query, top_k: mock_chunks
    )

    captured_prompt = {}

    def mock_generate(prompt):
        captured_prompt["text"] = prompt
        return "Normalization reduces redundancy."

    monkeypatch.setattr(
        rag_service,
        "generate_response",
        mock_generate
    )

    result = rag_service.generate_rag_response(
        "Explain normalization."
    )

    assert result["answer"] == "Normalization reduces redundancy."
    assert captured_prompt["text"].count(
        "Normalization reduces redundancy."
    ) == 1
    assert len(result["sources"]) == 1


def test_rag_filters_irrelevant_chunks(monkeypatch):
    """Test that chunks below the similarity threshold are ignored."""

    mock_chunks = [
        {
            "similarity": 0.15,
            "chunk": {
                "filename": "unrelated.pdf",
                "page_number": 1,
                "slide_number": None,
                "text": "This is unrelated information."
            }
        }
    ]

    monkeypatch.setattr(
        rag_service,
        "retrieve_relevant_chunks",
        lambda query, top_k: mock_chunks
    )

    def mock_generate(prompt):
        pytest.fail("Gemini should not be called for irrelevant chunks.")

    monkeypatch.setattr(
        rag_service,
        "generate_response",
        mock_generate
    )

    result = rag_service.generate_rag_response(
        "Explain database normalization."
    )

    assert result["sources"] == []
    assert "sufficiently relevant" in result["answer"]



def test_rag_respects_context_size_limit(monkeypatch):
    """Verify that the context sent to Gemini respects the size limit."""

    chunks = [
        {
            "similarity": 0.90,
            "chunk": {
                "text": "A" * 100,
                "filename": "notes.txt",
                "page_number": 1,
                "slide_number": None
            }
        },
        {
            "similarity": 0.85,
            "chunk": {
                "text": "B" * 100,
                "filename": "notes.txt",
                "page_number": 2,
                "slide_number": None
            }
        }
    ]

    captured = {}

    monkeypatch.setattr(
        "backend.services.rag_service.retrieve_relevant_chunks",
        lambda query, top_k: chunks
    )

    def mock_generate_response(prompt):
        captured["prompt"] = prompt
        return "Test answer"

    monkeypatch.setattr(
        "backend.services.rag_service.generate_response",
        mock_generate_response
    )

    from backend.services.rag_service import generate_rag_response

    generate_rag_response(
        question="Explain the notes.",
        max_context_chars=150
    )

    context = captured["prompt"].split(
        "Context:\n", 1
    )[1].split("\n\nQuestion:", 1)[0]

    assert len(context) <= 150


def test_rag_context_limit_validation():
    """Verify that invalid context limits are rejected."""

    import pytest
    from backend.services.rag_service import generate_rag_response

    with pytest.raises(ValueError, match="Maximum context size"):
        generate_rag_response(
            question="Explain Python.",
            max_context_chars=0
        )
