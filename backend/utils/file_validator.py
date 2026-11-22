
from pathlib import Path
import io
import zipfile

ALLOWED_EXTENSIONS = {
    ".pdf",
    ".docx",
    ".pptx",
    ".txt"
}

MAX_FILE_SIZE = 10 * 1024 * 1024


def validate_file(filename: str, file_size: int) -> None:
    """
    Validate document filename, extension and size.
    """

    if not filename or not filename.strip():
        raise ValueError("Filename cannot be empty.")

    extension = Path(filename).suffix.lower()

    if extension not in ALLOWED_EXTENSIONS:
        raise ValueError(
            "Unsupported file type. "
            "Upload PDF, DOCX, PPTX or TXT files."
        )

    if file_size <= 0:
        raise ValueError("File is empty.")

    if file_size > MAX_FILE_SIZE:
        raise ValueError("File size exceeds the 10 MB limit.")


def validate_file_content(filename: str, content: bytes) -> None:
    """
    Verify that the actual file content matches its extension.
    """

    extension = Path(filename).suffix.lower()

    if extension == ".pdf":
        if not content.startswith(b"%PDF-"):
            raise ValueError("Invalid PDF file content.")

    elif extension in {".docx", ".pptx"}:
        try:
            with zipfile.ZipFile(io.BytesIO(content)) as archive:
                file_names = archive.namelist()

        except zipfile.BadZipFile as error:
            raise ValueError(
                "Invalid Office document. File is not a valid DOCX/PPTX."
            ) from error

        if extension == ".docx":
            expected_file = "word/document.xml"
        else:
            expected_file = "ppt/presentation.xml"

        if expected_file not in file_names:
            raise ValueError(
                f"File content does not match {extension} format."
            )

    elif extension == ".txt":
        try:
            content.decode("utf-8-sig")
        except UnicodeDecodeError as error:
            raise ValueError(
                "TXT file must use UTF-8 text encoding."
            ) from error
