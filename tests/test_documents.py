
from pathlib import Path

import pytest
import pymupdf
from docx import Document
from pptx import Presentation

from backend.utils.file_validator import (
    validate_file,
    validate_file_content
)
from backend.services.document_service import extract_document


def test_valid_pdf_file():
    content = b"%PDF-1.4 test content"

    validate_file("notes.pdf", len(content))
    validate_file_content("notes.pdf", content)


def test_invalid_extension():
    with pytest.raises(ValueError):
        validate_file("notes.exe", 100)


def test_empty_file():
    with pytest.raises(ValueError):
        validate_file("notes.pdf", 0)


def test_file_size_limit():
    with pytest.raises(ValueError):
        validate_file("notes.pdf", 10 * 1024 * 1024 + 1)


def test_invalid_pdf_content():
    with pytest.raises(ValueError):
        validate_file_content("notes.pdf", b"This is not a PDF")


def test_txt_extraction(tmp_path):
    file_path = tmp_path / "notes.txt"
    file_path.write_text(
        "Machine Learning is a branch of Artificial Intelligence.",
        encoding="utf-8"
    )

    result = extract_document(file_path)

    assert result["file_type"] == ".txt"
    assert len(result["segments"]) == 1
    assert "Machine Learning" in result["segments"][0]["text"]


def test_pdf_extraction(tmp_path):
    file_path = tmp_path / "notes.pdf"

    with pymupdf.open() as pdf:
        page = pdf.new_page()
        page.insert_text(
            (50, 50),
            "StudyMate AI PDF extraction test."
        )
        pdf.save(file_path)

    result = extract_document(file_path)

    assert result["file_type"] == ".pdf"
    assert result["total_pages"] == 1
    assert result["segments"][0]["page_number"] == 1
    assert "StudyMate AI" in result["segments"][0]["text"]


def test_docx_extraction(tmp_path):
    file_path = tmp_path / "notes.docx"

    document = Document()
    document.add_paragraph("StudyMate DOCX extraction test.")
    document.save(file_path)

    result = extract_document(file_path)

    assert result["file_type"] == ".docx"
    assert "StudyMate DOCX" in result["segments"][0]["text"]


def test_pptx_extraction(tmp_path):
    file_path = tmp_path / "notes.pptx"

    presentation = Presentation()
    slide = presentation.slides.add_slide(
        presentation.slide_layouts[6]
    )

    textbox = slide.shapes.add_textbox(
        1000000, 1000000, 5000000, 1000000
    )
    textbox.text = "StudyMate PPTX extraction test."

    presentation.save(file_path)

    result = extract_document(file_path)

    assert result["file_type"] == ".pptx"
    assert result["total_slides"] == 1
    assert result["segments"][0]["slide_number"] == 1
    assert "StudyMate PPTX" in result["segments"][0]["text"]


def test_missing_document():
    with pytest.raises(FileNotFoundError):
        extract_document("non_existing_document.pdf")
