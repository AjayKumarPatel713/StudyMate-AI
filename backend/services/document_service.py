import pytesseract

pytesseract.pytesseract.tesseract_cmd = (
    r"C:\Program Files\Tesseract-OCR\tesseract.exe"
)
from pathlib import Path
from io import BytesIO

import pymupdf
import pytesseract
from PIL import Image
from pytesseract import TesseractNotFoundError

from docx import Document
from pptx import Presentation

from backend.utils.file_validator import validate_file


def extract_document(
    file_path: str | Path,
    original_filename: str | None = None
) -> dict:
    """
    Extract text from PDF, DOCX, PPTX or TXT documents.
    Automatically uses OCR for PDF pages without extractable text.
    """

    path = Path(file_path)

    if not path.exists() or not path.is_file():
        raise FileNotFoundError("Document file was not found.")

    filename = original_filename or path.name
    file_size = path.stat().st_size

    validate_file(filename, file_size)

    extension = Path(filename).suffix.lower()

    if extension == ".pdf":
        return _extract_pdf(path, filename)

    if extension == ".docx":
        return _extract_docx(path, filename)

    if extension == ".pptx":
        return _extract_pptx(path, filename)

    if extension == ".txt":
        return _extract_txt(path, filename)

    raise ValueError("Unsupported document type.")


def _extract_pdf(path: Path, filename: str) -> dict:
    segments = []

    with pymupdf.open(path) as pdf:
        total_pages = len(pdf)

        for page_number, page in enumerate(pdf, start=1):
            text = page.get_text("text").strip()

            # Use OCR when a page has no extractable text.
            if not text:
                try:
                    pix = page.get_pixmap(
                        matrix=pymupdf.Matrix(2, 2),
                        alpha=False
                    )

                    image = Image.open(
                        BytesIO(pix.tobytes("png"))
                    )

                    text = pytesseract.image_to_string(
                        image,
                        lang="eng",
                        config="--psm 6"
                    ).strip()

                except TesseractNotFoundError as error:
                    raise RuntimeError(
                        "Tesseract OCR is not installed or not configured. "
                        "Install Tesseract and add it to your system PATH."
                    ) from error

            if text:
                segments.append({
                    "text": text,
                    "page_number": page_number,
                    "slide_number": None
                })

    if not segments:
        raise ValueError(
            "No readable text found in this PDF, even after OCR."
        )

    return {
        "filename": filename,
        "file_type": ".pdf",
        "total_pages": total_pages,
        "total_slides": None,
        "segments": segments
    }


def _extract_docx(path: Path, filename: str) -> dict:
    document = Document(path)
    text_parts = []

    for paragraph in document.paragraphs:
        text = paragraph.text.strip()

        if text:
            text_parts.append(text)

    for table in document.tables:
        for row in table.rows:
            row_text = [
                cell.text.strip()
                for cell in row.cells
                if cell.text.strip()
            ]

            if row_text:
                text_parts.append(" | ".join(row_text))

    full_text = "\n".join(text_parts).strip()

    if not full_text:
        raise ValueError("No extractable text found in this DOCX file.")

    return {
        "filename": filename,
        "file_type": ".docx",
        "total_pages": None,
        "total_slides": None,
        "segments": [{
            "text": full_text,
            "page_number": None,
            "slide_number": None
        }]
    }


def _extract_pptx(path: Path, filename: str) -> dict:
    presentation = Presentation(path)
    segments = []
    total_slides = len(presentation.slides)

    for slide_number, slide in enumerate(presentation.slides, start=1):
        slide_text = []

        for shape in slide.shapes:
            if shape.has_text_frame:
                text = shape.text.strip()

                if text:
                    slide_text.append(text)

            if shape.has_table:
                for row in shape.table.rows:
                    row_text = [
                        cell.text.strip()
                        for cell in row.cells
                        if cell.text.strip()
                    ]

                    if row_text:
                        slide_text.append(" | ".join(row_text))

        full_text = "\n".join(slide_text).strip()

        if full_text:
            segments.append({
                "text": full_text,
                "page_number": None,
                "slide_number": slide_number
            })

    if not segments:
        raise ValueError("No extractable text found in this PPTX file.")

    return {
        "filename": filename,
        "file_type": ".pptx",
        "total_pages": None,
        "total_slides": total_slides,
        "segments": segments
    }


def _extract_txt(path: Path, filename: str) -> dict:
    try:
        text = path.read_text(encoding="utf-8-sig").strip()
    except UnicodeDecodeError as error:
        raise ValueError(
            "TXT file must use UTF-8 text encoding."
        ) from error

    if not text:
        raise ValueError("No extractable text found in this TXT file.")

    return {
        "filename": filename,
        "file_type": ".txt",
        "total_pages": None,
        "total_slides": None,
        "segments": [{
            "text": text,
            "page_number": None,
            "slide_number": None
        }]
    }
