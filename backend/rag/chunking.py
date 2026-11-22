
def split_text_into_chunks(
    text: str,
    chunk_size: int = 250,
    overlap: int = 40
) -> list[str]:
    """
    Split text into word-based chunks with overlap.
    """

    if not isinstance(text, str):
        raise TypeError("Text must be a string.")

    if chunk_size <= 0:
        raise ValueError("Chunk size must be positive.")

    if overlap < 0 or overlap >= chunk_size:
        raise ValueError(
            "Overlap must be non-negative and smaller than chunk size."
        )

    words = text.split()

    if not words:
        return []

    chunks = []
    start = 0

    while start < len(words):
        end = start + chunk_size

        chunk_words = words[start:end]

        chunks.append(" ".join(chunk_words))

        if end >= len(words):
            break

        start = end - overlap

    return chunks


def create_document_chunks(
    extracted_document: dict,
    document_id: str,
    chunk_size: int = 250,
    overlap: int = 40
) -> list[dict]:
    """
    Convert extracted document segments into chunks.
    Preserve document and page/slide information.
    """

    if not document_id:
        raise ValueError("Document ID cannot be empty.")

    if not isinstance(extracted_document, dict):
        raise TypeError("Extracted document must be a dictionary.")

    filename = extracted_document.get("filename")

    if not filename:
        raise ValueError("Document filename is missing.")

    segments = extracted_document.get("segments", [])

    all_chunks = []
    chunk_number = 0

    for segment_number, segment in enumerate(segments, start=1):
        text = segment.get("text", "").strip()

        if not text:
            continue

        text_chunks = split_text_into_chunks(
            text,
            chunk_size=chunk_size,
            overlap=overlap
        )

        for chunk_text in text_chunks:
            chunk_number += 1

            all_chunks.append({
                "chunk_id": f"{document_id}_{chunk_number}",
                "document_id": document_id,
                "filename": filename,
                "chunk_number": chunk_number,
                "segment_number": segment_number,
                "page_number": segment.get("page_number"),
                "slide_number": segment.get("slide_number"),
                "text": chunk_text
            })

    return all_chunks
