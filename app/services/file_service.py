"""
file_service.py  —  app/services/file_service.py

Handles uploaded files:
  - Extracts text from PDF, DOCX, TXT
  - Chunks the text
  - Stores chunks in ChromaDB via context_service so they surface
    automatically when retrieve_context() is called during /generate
"""

import uuid
import pdfplumber
import docx
from pathlib import Path
from app.services.context_service import context_service


SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".txt"}


# ---------------------------------------------------------------------------
# Text extraction
# ---------------------------------------------------------------------------


def extract_text_from_pdf(file_path: str) -> str:
    text = []
    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text.append(page_text)
    return "\n\n".join(text)


def extract_text_from_docx(file_path: str) -> str:
    doc = docx.Document(file_path)
    paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
    return "\n\n".join(paragraphs)


def extract_text_from_txt(file_path: str) -> str:
    return Path(file_path).read_text(encoding="utf-8")


def extract_text(file_path: str) -> str:
    ext = Path(file_path).suffix.lower()
    if ext == ".pdf":
        return extract_text_from_pdf(file_path)
    elif ext == ".docx":
        return extract_text_from_docx(file_path)
    elif ext == ".txt":
        return extract_text_from_txt(file_path)
    else:
        raise ValueError(
            f"Unsupported file type: {ext}. Supported: {SUPPORTED_EXTENSIONS}"
        )


# ---------------------------------------------------------------------------
# Chunking  (simple fixed-size with overlap)
# ---------------------------------------------------------------------------


def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> list[str]:
    """
    Split text into overlapping chunks so long documents don't lose context
    at chunk boundaries.
    """
    words = text.split()
    chunks = []
    start = 0
    while start < len(words):
        end = start + chunk_size
        chunk = " ".join(words[start:end])
        chunks.append(chunk)
        start += chunk_size - overlap
    return chunks


# ---------------------------------------------------------------------------
# Main entry point — call this from the /upload endpoint
# ---------------------------------------------------------------------------


def ingest_file(file_path: str, source_name: str) -> dict:
    """
    Extract text from a file, chunk it, and store in ChromaDB.
    Returns metadata about what was ingested.
    """
    text = extract_text(file_path)
    chunks = chunk_text(text)

    if not chunks:
        raise ValueError("No text could be extracted from the file.")

    # Build unique IDs and metadata for each chunk
    ids = [f"{source_name}_{i}_{uuid.uuid4().hex[:8]}" for i in range(len(chunks))]
    metadatas = [{"source": source_name, "chunk_index": i} for i in range(len(chunks))]

    context_service.add_documents(
        documents=chunks,
        metadata=metadatas,
        ids=ids,
    )

    return {
        "source": source_name,
        "chunks_stored": len(chunks),
        "preview": chunks[0][:200] + "..." if len(chunks[0]) > 200 else chunks[0],
    }
